import asyncio
import time
from datetime import datetime
from pathlib import Path
from random import random

import discord

import ai
import chatformat
import config
import settings
import status
from keywords import MEDIA_DIR, MEDIA_TYPES, ReplyBook, actions_for, resolve_file, words_in

BASE_DIR = Path(__file__).resolve().parent
book = ReplyBook(BASE_DIR / "replies.yaml")

HELP = (
    "`!addreply word, some phrase | reply text or gif link` (attach an image to send it)\n"
    "`!delreply <name>`  `!replies`  `!reload`\n"
    "`!shutup` / `!talk` turn unprompted AI replies off / on"
)


async def perform(message, action, user_message):
    unless = action.get("unless_contains")
    if unless and unless.lower() in user_message.lower():
        return
    content = user_message if action.get("echo") else action.get("text")
    file = None
    if action.get("file"):
        path = resolve_file(action["file"])
        if path is None:
            print(f"Missing file {action['file']}")
        else:
            file = discord.File(path)
    if not content and file is None:
        return
    kwargs = {"content": content}
    if file:
        kwargs["file"] = file
    if action.get("mode", "reply") == "send":
        await message.channel.send(**kwargs)
    else:
        await message.reply(**kwargs)


def run_discord_bot():
    TOKEN = config.TOKEN
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    muted_until = {}  # username -> time the keyword mute ends
    last_ai_reply = {}  # username -> time of last direct AI reply
    last_unprompted = {}  # channel id -> time of last unprompted AI reply
    unprompted = {"on": settings.AI_UNPROMPTED}

    async def handle_command(message, raw):
        command, _, rest = raw[1:].partition(" ")
        command = command.lower()
        rest = rest.strip()

        if command == "addreply":
            triggers, _, text = rest.partition("|")
            triggers = [t.strip().lower() for t in triggers.split(",") if t.strip()]
            text = text.strip() or None
            file = None
            if message.attachments:
                attachment = message.attachments[0]
                name = Path(attachment.filename).name
                if Path(name).suffix.lower() not in MEDIA_TYPES:
                    await message.reply("That attachment isn't an image or video.")
                    return True
                MEDIA_DIR.mkdir(exist_ok=True)
                await attachment.save(MEDIA_DIR / name)
                file = name
            if not triggers or not (text or file):
                await message.reply("Usage: `!addreply word, some phrase | reply text` (or attach an image)")
                return True
            entry = book.add(triggers, text, file)
            await message.reply(f"Added **{entry['name']}**: {', '.join(triggers)}")
        elif command == "delreply":
            if book.remove(rest):
                await message.reply(f"Removed **{rest}**")
            else:
                await message.reply(f"No reply named **{rest}**. Try `!replies`.")
        elif command == "replies":
            await message.reply(("Replies: " + ", ".join(book.names()))[:1900] + "\n" + HELP)
        elif command == "reload":
            book.reload()
            await message.reply(f"Reloaded {len(book.entries)} replies")
        elif command == "shutup":
            unprompted["on"] = False
            await message.reply("Fine. I'll only talk when spoken to.")
        elif command == "talk":
            unprompted["on"] = True
            await message.reply("Ready to comply.")
        else:
            return False
        return True

    async def keyword_replies(message, user_message, username):
        muted = time.time() < muted_until.get(username, 0)
        responded = False
        should_mute = False
        for entry in book.matching(user_message, username, datetime.now()):
            if muted and not entry.get("ignore_mute"):
                continue
            print(f"{entry.get('name')} triggered")
            try:
                for action in actions_for(entry):
                    await perform(message, action, user_message)
            except Exception as e:
                print(e)
            responded = True
            should_mute = should_mute or entry.get("mute", True)

        if muted and not responded:
            print("User muted, message not processed")
        if should_mute and username not in settings.MUTE_EXEMPT:
            muted_until[username] = time.time() + settings.MUTE_SECONDS
        if responded:
            status.set_state("talking")
        return responded

    def ai_reason(message, user_message, username):
        now = time.time()
        ref = message.reference
        if client.user in message.mentions:
            reason = "mention"
        elif ref and isinstance(ref.resolved, discord.Message) and ref.resolved.author == client.user:
            reason = "reply"
        elif settings.AI_REPLY_TO_NAME and "junior" in words_in(user_message):
            reason = "name"
        else:
            if (
                unprompted["on"]
                and len(user_message.split()) >= settings.AI_MIN_WORDS
                and now - last_unprompted.get(message.channel.id, 0) > settings.AI_CHANNEL_COOLDOWN
                and now >= muted_until.get(username, 0)
                and random() < settings.AI_RANDOM_CHANCE
            ):
                last_unprompted[message.channel.id] = now
                return "random"
            return None

        if now - last_ai_reply.get(username, 0) < settings.AI_USER_COOLDOWN:
            return None
        last_ai_reply[username] = now
        return reason

    async def ai_reply(message, user_message, username):
        if message.author.bot or not ai.available():
            return
        reason = ai_reason(message, user_message, username)
        if reason is None:
            return
        print(f"AI reply ({reason})")

        history = [m async for m in message.channel.history(limit=settings.AI_CONTEXT_MESSAGES, before=message)]
        lines = []
        for m in list(reversed(history)) + [message]:  # history comes newest first
            if text := chatformat.message_text(m):
                lines.append(chatformat.line(m.author.display_name, text))

        status.set_state("thinking")
        try:
            async with message.channel.typing():
                text, path = await asyncio.to_thread(ai.generate, lines)
        except Exception as e:
            print(f"AI error: {e}")
            status.set_state("idle")
            return
        if not text and path is None:
            status.set_state("idle")
            return

        kwargs = {"content": text or None}
        if path:
            kwargs["file"] = discord.File(path)
        if reason == "random":
            await message.channel.send(**kwargs)
        else:
            await message.reply(**kwargs)
        status.set_state("talking")

    def load_model():
        try:
            ai.load()
        except Exception:
            pass  # ai.load already printed why

    @client.event
    async def on_ready():
        print(f'{client.user} is now running.')
        status.set_state("idle")
        if ai.available():
            asyncio.create_task(asyncio.to_thread(load_model))
        else:
            print(f"No model at {ai.MODEL_PATH}, AI replies are off")

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        book.reload_if_changed()

        username = str(message.author)
        raw = str(message.content)
        if username == settings.OWNER and raw.startswith("!"):
            try:
                if await handle_command(message, raw):
                    return
            except Exception as e:
                print(e)
                await message.reply(f"That didn't work: {e}")
                return

        user_message = raw.strip("!")
        channel = str(message.channel)
        print(f"{username} said: '{user_message}' ({channel})")

        if not await keyword_replies(message, user_message, username):
            await ai_reply(message, user_message, username)

    client.run(TOKEN)
