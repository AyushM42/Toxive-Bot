"""Fine-tune a small chat model on data/train.jsonl with QLoRA. Run on the PC (needs an NVIDIA GPU).

    python training/train.py
    python training/train.py --base Qwen/Qwen2.5-7B-Instruct --epochs 2

Saves a LoRA adapter to training/out/adapter. Test it with training/chat.py, then
build the Pi model with training/export_gguf.py.
"""
import argparse
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

BASE_DIR = Path(__file__).resolve().parent.parent


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="Qwen/Qwen2.5-3B-Instruct")
    p.add_argument("--train", default=str(BASE_DIR / "data" / "train.jsonl"))
    p.add_argument("--val", default=str(BASE_DIR / "data" / "val.jsonl"))
    p.add_argument("--out", default=str(BASE_DIR / "training" / "out"))
    p.add_argument("--epochs", type=float, default=2)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--batch", type=int, default=4)
    p.add_argument("--grad-accum", type=int, default=4)
    p.add_argument("--max-length", type=int, default=1024)
    p.add_argument("--rank", type=int, default=16)
    return p.parse_args()


def main():
    args = parse_args()
    files = {"train": args.train}
    if Path(args.val).is_file() and Path(args.val).stat().st_size > 0:
        files["val"] = args.val
    data = load_dataset("json", data_files=files)

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    model = AutoModelForCausalLM.from_pretrained(
        args.base,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        ),
        dtype=torch.bfloat16,
        device_map={"": 0},
    )

    config = SFTConfig(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.grad_accum,
        gradient_checkpointing=True,
        max_length=args.max_length,
        bf16=True,
        logging_steps=10,
        eval_strategy="epoch" if "val" in files else "no",
        save_strategy="epoch",
        save_total_limit=2,
        report_to="none",
    )
    trainer = SFTTrainer(
        model=model,
        args=config,
        train_dataset=data["train"],
        eval_dataset=data.get("val"),
        processing_class=tokenizer,
        peft_config=LoraConfig(
            r=args.rank,
            lora_alpha=args.rank * 2,
            lora_dropout=0.05,
            target_modules="all-linear",
            task_type="CAUSAL_LM",
        ),
    )
    trainer.train()

    adapter_dir = Path(args.out) / "adapter"
    trainer.save_model(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    print(f"Saved adapter to {adapter_dir}")


if __name__ == "__main__":
    main()
