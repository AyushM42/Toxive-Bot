"""Tells the squirrel display what the bot is doing via a small file."""
import time

import settings


def set_state(state):
    try:
        with open(settings.STATUS_FILE, "w") as f:
            f.write(f"{state} {time.time()}")
    except OSError:
        pass  # no display (e.g. running on Windows)
