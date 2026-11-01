# Bot behaviour settings. The bot token stays in config.py (not committed).

OWNER = "toxive"  # only this Discord username can use !addreply, !shutup, etc.

# Keyword replies
MUTE_SECONDS = 60  # after a keyword reply, ignore that user's keywords for this long
MUTE_EXEMPT = {"toxive"}

# Conversation context, shared by training (tools/build_dataset.py) and the bot so they match
CONTEXT_MESSAGES = 8  # previous messages the model sees
CONTEXT_GAP_HOURS = 3  # older messages than this aren't part of the conversation
MAX_LINE_CHARS = 300  # long messages are cut to this in prompts

# AI replies (skipped automatically if the model file doesn't exist)
AI_ENABLED = True
AI_MODEL_PATH = "models/toxive-jr.gguf"
AI_THREADS = 3  # leave one of the Pi 5's 4 cores for Discord, the display and the OS
AI_CONTEXT_TOKENS = 2048
AI_PROMPT_TOKENS = 700  # oldest messages are dropped past this; long prompts are slow on the Pi
AI_MAX_TOKENS = 80
AI_TEMPERATURE = 0.8
# Links in AI replies are removed unless they're from one of these sites
AI_LINK_DOMAINS = {"tenor.com", "giphy.com", "discord.com", "discordapp.com", "discordapp.net", "youtube.com", "youtu.be"}

AI_REPLY_TO_NAME = True  # reply when someone says "junior"
AI_USER_COOLDOWN = 5  # seconds between direct AI replies to the same person

# Unprompted replies (toggle in Discord with !shutup / !talk)
AI_UNPROMPTED = True
AI_RANDOM_CHANCE = 0.02  # chance per message
AI_CHANNEL_COOLDOWN = 30 * 60  # at most one unprompted reply per channel per 30 minutes
AI_MIN_WORDS = 4  # ignore short messages

# The squirrel display reads this to know when the bot is thinking / talking
STATUS_FILE = "/tmp/toxive-jr-status"
