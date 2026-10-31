"""Runs the fine-tuned model with llama.cpp. Every function here blocks, so call them from a thread."""
import re
import threading
from pathlib import Path

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
    """Returns (text, file_path or None)."""
    load()
    with _lock:
        out = _llm.create_chat_completion(
            messages=chatformat.build_prompt(lines),
            max_tokens=settings.AI_MAX_TOKENS,
            temperature=settings.AI_TEMPERATURE,
            top_p=0.9,
            repeat_penalty=1.1,
        )
    return _clean(out["choices"][0]["message"]["content"])


def _clean(text):
    text = text.strip()
    # The model sometimes writes "Name: message" like the transcript
    text = re.sub(r"^[^\n:]{1,32}:\s+", "", text, count=1)
    text = text.split("\n")[0].strip()

    file = None
    for name in re.findall(r"\[img:([^\]]+)\]", text):
        file = file or resolve_file(name)
    text = re.sub(r"\[(img|sticker):[^\]]+\]", "", text).strip()
    return text[:2000], file
