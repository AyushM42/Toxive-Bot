"""Chat with the fine-tuned adapter on the PC before exporting it to the Pi.

    python training/chat.py

Type messages as "name: text" (or just text, which is sent as you). An empty line
asks Toxive Jr to reply. "/reset" clears the conversation.
"""
import sys
from pathlib import Path

import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer, BitsAndBytesConfig

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import chatformat  # noqa: E402
import settings  # noqa: E402

ADAPTER = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "training" / "out" / "adapter"


def main():
    tokenizer = AutoTokenizer.from_pretrained(ADAPTER)
    # 4-bit like training, so even a 7B model fits in 12 GB
    model = AutoPeftModelForCausalLM.from_pretrained(
        ADAPTER,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16),
        dtype=torch.bfloat16,
        device_map={"": 0},
    )
    lines = []
    print("Type messages, then an empty line for Toxive Jr's reply. /reset clears.")
    while True:
        text = input("> ").strip()
        if text == "/reset":
            lines = []
            continue
        if text:
            name, sep, rest = text.partition(":")
            lines.append(text if sep and " " not in name else chatformat.line(settings.OWNER, text))
            continue

        inputs = tokenizer.apply_chat_template(
            chatformat.build_prompt(lines[-settings.CONTEXT_MESSAGES - 1:]),
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        ).to(model.device)
        out = model.generate(**inputs, max_new_tokens=80, do_sample=True, temperature=0.8, top_p=0.9, repetition_penalty=1.1)
        reply = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        print(f"Toxive Jr: {reply}")
        lines.append(chatformat.line("Toxive Jr", reply))


if __name__ == "__main__":
    main()
