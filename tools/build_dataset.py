"""Turn data/messages.jsonl into training examples (data/train.jsonl and data/val.jsonl).

Each example is the recent conversation in a channel followed by a message from you (toxive)
or from Toxive Jr. Toxive Jr's keyword gifs repeat a lot, so repeats are capped and Jr's share
of the dataset is limited, so the model mostly learns your voice.

    python tools/build_dataset.py
    python tools/build_dataset.py --context 8 --max-bot-share 0.1
"""
import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import chatformat  # noqa: E402
import settings  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--messages", default=str(BASE_DIR / "data" / "messages.jsonl"))
    p.add_argument("--out-dir", default=str(BASE_DIR / "data"))
    p.add_argument("--user", default=settings.OWNER, help="your Discord username")
    p.add_argument("--context", type=int, default=10, help="previous messages shown to the model")
    p.add_argument("--gap-hours", type=float, default=3, help="older messages than this aren't context")
    p.add_argument("--max-repeats", type=int, default=3, help="max copies of the same reply text")
    p.add_argument("--max-bot-share", type=float, default=0.15, help="max fraction of examples from Toxive Jr")
    p.add_argument("--val-share", type=float, default=0.05)
    p.add_argument("--seed", type=int, default=0)
    return p.parse_args()


def main():
    args = parse_args()
    random.seed(args.seed)

    by_channel = defaultdict(list)
    with open(args.messages, encoding="utf-8") as f:
        for row in f:
            m = json.loads(row)
            m["time"] = datetime.fromisoformat(m["time"])
            by_channel[m["channel_id"]].append(m)

    mine, bot = [], []
    repeats = Counter()
    skipped_echo = 0
    for messages in by_channel.values():
        messages.sort(key=lambda m: m["time"])
        for i, m in enumerate(messages):
            is_me = m["author"] == args.user
            if not (is_me or m["is_self"]) or m["text"].startswith("!"):
                continue
            prev = messages[max(0, i - args.context):i]
            prev = [p for p in prev if m["time"] - p["time"] < timedelta(hours=args.gap_hours)]
            if m["is_self"] and prev and prev[-1]["text"] == m["text"]:
                skipped_echo += 1  # the "hi" echo reply teaches nothing
                continue
            key = m["text"].lower()
            if repeats[key] >= args.max_repeats:
                continue
            repeats[key] += 1

            lines = [chatformat.line(p["name"], p["text"]) for p in prev]
            example = {
                "prompt": chatformat.build_prompt(lines),
                "completion": [{"role": "assistant", "content": m["text"]}],
            }
            (mine if is_me else bot).append(example)

    max_bot = int(len(mine) * args.max_bot_share / (1 - args.max_bot_share))
    random.shuffle(bot)
    examples = mine + bot[:max_bot]
    random.shuffle(examples)

    n_val = max(1, int(len(examples) * args.val_share)) if len(examples) > 20 else 0
    out_dir = Path(args.out_dir)
    for name, rows in (("val", examples[:n_val]), ("train", examples[n_val:])):
        with open(out_dir / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Your messages: {len(mine)}")
    print(f"Toxive Jr messages: {min(len(bot), max_bot)} used of {len(bot)} (skipped {skipped_echo} echoes)")
    print(f"Wrote {len(examples) - n_val} train / {n_val} val examples to {out_dir}")
    if len(mine) < 500:
        print("Warning: under 500 of your messages. The model may not pick up your style well.")


if __name__ == "__main__":
    main()
