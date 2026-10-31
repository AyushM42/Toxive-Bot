"""Prompt format shared by the dataset builder (training) and the bot (inference).

Training and inference must format conversations identically, so both import from here.
"""

SYSTEM_PROMPT = (
    "You are Toxive Jr, a member of a friend group's Discord server. "
    "Read the recent messages and write the next message in your usual style: short, casual, no explanations."
)
NO_CONTEXT = "(no recent messages)"


def message_text(message):
    """Text of a discord.Message, with attachments as [img:filename] placeholders."""
    parts = [message.clean_content.strip()]
    parts += [f"[img:{a.filename}]" for a in message.attachments]
    parts += [f"[sticker:{s.name}]" for s in message.stickers]
    return " ".join(p for p in parts if p)


def line(name, text):
    return f"{name}: {text}"


def build_prompt(lines):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(lines) if lines else NO_CONTEXT},
    ]
