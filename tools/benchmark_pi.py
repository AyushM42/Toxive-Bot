"""Measure how fast stock models of different sizes run on the Pi, to pick what to fine-tune.

    python tools/benchmark_pi.py              # 1.5B, 3B and 7B
    python tools/benchmark_pi.py 3b 7b

Downloads go to models/bench/ (about 1 GB, 2 GB and 4.7 GB). Delete that folder afterwards.
"""
import sys
import time
from pathlib import Path

from huggingface_hub import hf_hub_download
from llama_cpp import Llama

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import chatformat  # noqa: E402

MODELS = {
    "1.5b": ("bartowski/Qwen2.5-1.5B-Instruct-GGUF", "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"),
    "3b": ("bartowski/Qwen2.5-3B-Instruct-GGUF", "Qwen2.5-3B-Instruct-Q4_K_M.gguf"),
    "7b": ("bartowski/Qwen2.5-7B-Instruct-GGUF", "Qwen2.5-7B-Instruct-Q4_K_M.gguf"),
}

LINES = [
    chatformat.line("toxive", "bro who is up rn"),
    chatformat.line("girlsonly", "me im grinding rivals"),
    chatformat.line("vivianmeat1", "yall are so cooked"),
    chatformat.line("toxive", "junior what do you think"),
]


def bench(size):
    repo, filename = MODELS[size]
    path = hf_hub_download(repo, filename, local_dir=BASE_DIR / "models" / "bench")
    start = time.time()
    llm = Llama(model_path=path, n_ctx=2048, n_threads=4, verbose=False)
    load = time.time() - start

    start = time.time()
    first = None
    tokens = 0
    text = ""
    for chunk in llm.create_chat_completion(chatformat.build_prompt(LINES), max_tokens=48, stream=True):
        delta = chunk["choices"][0]["delta"].get("content")
        if delta:
            first = first or time.time()
            tokens += 1
            text += delta
    end = time.time()

    gen_speed = (tokens - 1) / (end - first) if tokens > 1 else 0
    print(f"\n== {size} ==")
    print(f"load {load:.1f}s | first token after {first - start:.1f}s | {gen_speed:.1f} tokens/s")
    print(f"30-token reply would take ~{(first - start) + 30 / max(gen_speed, 0.01):.1f}s")
    print(f"sample: {text.strip()!r}")
    del llm


if __name__ == "__main__":
    for size in sys.argv[1:] or MODELS:
        bench(size.lower())
