# Bot behaviour settings. The bot token stays in config.py (not committed).

OWNER = "toxive"  # only this Discord username can use !addreply, !shutup, etc.

# Keyword replies
MUTE_SECONDS = 60  # after a keyword reply, ignore that user's keywords for this long
MUTE_EXEMPT = {"toxive"}

# AI replies (skipped automatically if the model file doesn't exist)
AI_ENABLED = True
AI_MODEL_PATH = "models/toxive-jr.gguf"
AI_THREADS = 4  # Pi 5 has 4 cores
AI_CONTEXT_TOKENS = 2048
AI_CONTEXT_MESSAGES = 12  # recent channel messages the model sees
AI_MAX_TOKENS = 80
AI_TEMPERATURE = 0.8

AI_REPLY_TO_NAME = True  # reply when someone says "junior"
AI_USER_COOLDOWN = 5  # seconds between direct AI replies to the same person

# Unprompted replies (toggle in Discord with !shutup / !talk)
AI_UNPROMPTED = True
AI_RANDOM_CHANCE = 0.02  # chance per message
AI_CHANNEL_COOLDOWN = 30 * 60  # at most one unprompted reply per channel per 30 minutes
AI_MIN_WORDS = 4  # ignore short messages

# The squirrel display reads this to know when the bot is thinking / talking
STATUS_FILE = "/tmp/toxive-jr-status"
