"""Merge the adapter into the base model and convert it to a 4-bit GGUF file for the Pi.

Needs llama.cpp on the PC:
  1. git clone https://github.com/ggml-org/llama.cpp  (then: pip install -r llama.cpp/requirements.txt)
  2. Download a Windows release zip from the llama.cpp GitHub releases page (the "bin-win-cpu-x64" one)
     and unzip it; it contains llama-quantize.exe.

    python training/export_gguf.py --llama-cpp C:/path/to/llama.cpp --quantize C:/path/to/llama-quantize.exe

Writes models/toxive-jr.gguf. Copy that file to the same path on the Pi.
"""
import argparse
import subprocess
import sys
from pathlib import Path

import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

BASE_DIR = Path(__file__).resolve().parent.parent


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--adapter", default=str(BASE_DIR / "training" / "out" / "adapter"))
    p.add_argument("--merged", default=str(BASE_DIR / "training" / "out" / "merged"))
    p.add_argument("--llama-cpp", required=True, help="llama.cpp source folder (has convert_hf_to_gguf.py)")
    p.add_argument("--quantize", required=True, help="path to llama-quantize(.exe)")
    p.add_argument("--type", default="Q4_K_M")
    p.add_argument("--out", default=str(BASE_DIR / "models" / "toxive-jr.gguf"))
    return p.parse_args()


def main():
    args = parse_args()
    merged = Path(args.merged)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    f16 = merged / "model-f16.gguf"

    print("Merging adapter...")
    model = AutoPeftModelForCausalLM.from_pretrained(args.adapter, dtype=torch.bfloat16)
    model.merge_and_unload().save_pretrained(merged)
    AutoTokenizer.from_pretrained(args.adapter).save_pretrained(merged)

    print("Converting to GGUF...")
    convert = Path(args.llama_cpp) / "convert_hf_to_gguf.py"
    subprocess.run([sys.executable, str(convert), str(merged), "--outfile", str(f16), "--outtype", "f16"], check=True)

    print(f"Quantizing to {args.type}...")
    subprocess.run([args.quantize, str(f16), str(out), args.type], check=True)
    f16.unlink()
    print(f"Done: {out} ({out.stat().st_size / 1e9:.1f} GB)")


if __name__ == "__main__":
    main()
