"""Download message history from every server channel Toxive Jr can read into data/messages.jsonl.

Only servers the bot is in are exported. DMs are never read, so they never end up in training data.

Run from the bot folder (it uses the token in config.py):
    python tools/export_messages.py
    python tools/export_messages.py --after 2023-01-01 --limit 20000

The bot needs "Read Message History" in the channels you want. Re-running overwrites the file.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import discord  # noqa: E402

import chatformat  # noqa: E402
import config  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(BASE_DIR / "data" / "messages.jsonl"))
    p.add_argument("--after", help="only messages after this date, e.g. 2023-01-01")
    p.add_argument("--limit", type=int, default=None, help="newest N messages per channel (default: all)")
    p.add_argument("--guild", help="only this server (name or id)")
    return p.parse_args()


async def export_channel(channel, me, out, args, after):
    count = 0
    # Newest first, so --limit keeps recent messages; build_dataset.py sorts by time anyway
    async for m in channel.history(limit=args.limit, after=after, oldest_first=False):
        text = chatformat.message_text(m)
        if not text:
            continue
        out.write(json.dumps({
            "id": m.id,
            "guild": channel.guild.name,
            "channel_id": channel.id,
            "channel": channel.name,
            "time": m.created_at.isoformat(),
            "author": str(m.author),
            "name": m.author.display_name,
            "is_bot": m.author.bot,
            "is_self": m.author.id == me.id,
            "reply_to": m.reference.message_id if m.reference else None,
            "text": text,
        }, ensure_ascii=False) + "\n")
        count += 1
    return count


def main():
    args = parse_args()
    after = datetime.fromisoformat(args.after).replace(tzinfo=timezone.utc) if args.after else None
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    started = False

    async def threads(guild):
        """Active and archived threads (including forum posts) in a server."""
        found = {t.id: t for t in guild.threads}
        for parent in list(guild.text_channels) + list(guild.forums):
            try:
                async for t in parent.archived_threads(limit=None):
                    found[t.id] = t
            except discord.Forbidden:
                pass
        return list(found.values())

    @client.event
    async def on_ready():
        nonlocal started
        if started:  # on_ready fires again after a reconnect; don't restart the export
            return
        started = True
        total = 0
        try:
            with open(out_path, "w", encoding="utf-8") as out:
                for guild in client.guilds:
                    if args.guild and args.guild not in (guild.name, str(guild.id)):
                        continue
                    channels = list(guild.text_channels) + await threads(guild)
                    for channel in channels:
                        perms = channel.permissions_for(guild.me)
                        if not (perms.read_messages and perms.read_message_history):
                            continue
                        try:
                            n = await export_channel(channel, client.user, out, args, after)
                        except discord.Forbidden:
                            continue
                        total += n
                        print(f"{guild.name} #{channel.name}: {n}")
            print(f"Wrote {total} messages to {out_path}")
        finally:
            await client.close()

    client.run(config.TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
