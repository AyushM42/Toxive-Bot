"""Runs the fine-tuned model with llama.cpp. Every function here except busy() blocks, so call them from a thread."""
import re
import threading
from pathlib import Path
from urllib.parse import urlparse

import chatformat
import settings
from keywords import resolve_file

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / settings.AI_MODEL_PATH

_llm = None
_lock = threading.Lock()
_failed = False


def available():
    return settings.AI_ENABLED and not _failed and MODEL_PATH.is_file()


def busy():
    return _lock.locked()


def load():
    global _llm, _failed
    with _lock:
        if _llm is not None:
            return
        try:
            from llama_cpp import Llama

            print(f"Loading {MODEL_PATH.name}...")
            _llm = Llama(
                model_path=str(MODEL_PATH),
                n_ctx=settings.AI_CONTEXT_TOKENS,
                n_threads=settings.AI_THREADS,
                verbose=False,
            )
            print("Model loaded")
        except Exception as e:
            _failed = True
            print(f"AI disabled, could not load model: {e}")
            raise


def generate(lines):
    """Returns (text, file_path or None). Either may be empty if the reply was unusable."""
    load()
    with _lock:
        lines = _fit(lines)
        out = _llm.create_chat_completion(
            messages=chatformat.build_prompt(lines),
            max_tokens=settings.AI_MAX_TOKENS,
            temperature=settings.AI_TEMPERATURE,
            top_p=0.9,
            repeat_penalty=1.1,
        )
    return _clean(out["choices"][0]["message"]["content"], lines)


def _fit(lines):
    """Drop the oldest messages until the prompt fits the token budget."""
    lines = list(lines)

    def tokens():
        text = chatformat.SYSTEM_PROMPT + "\n" + "\n".join(lines)
        return len(_llm.tokenize(text.encode(), add_bos=False))

    while len(lines) > 1 and tokens() > settings.AI_PROMPT_TOKENS:
        lines.pop(0)
    return lines


def _allowed_link(match):
    host = (urlparse(match.group(0)).hostname or "").lower()
    ok = any(host == d or host.endswith("." + d) for d in settings.AI_LINK_DOMAINS)
    return match.group(0) if ok else ""


def _clean(text, lines):
    text = text.strip().split("\n")[0].strip()
    # The model sometimes starts with "Name: " like the transcript; only strip real speaker names
    speakers = {l.split(": ", 1)[0] for l in lines} | {"Toxive Jr"}
    name, sep, rest = text.partition(": ")
    if sep and name in speakers:
        text = rest.strip()

    file = None
    for name in re.findall(r"\[img:([^\]]+)\]", text):
        file = file or resolve_file(name)
    text = re.sub(r"\[(img|sticker):[^\]]+\]", "", text)
    text = re.sub(r"https?://\S+", _allowed_link, text)
    text = re.sub(r"\s+", " ", text).strip()

    # Don't parrot the message that triggered the reply ("junior repeat after me: ...")
    last = lines[-1].split(": ", 1)[-1].lower() if lines else ""
    if len(text) > 10 and text.lower() in last:
        text = ""
    return text[:2000], file
