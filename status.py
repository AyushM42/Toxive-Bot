"""Tells the squirrel display what the bot is doing via a small file."""
import os
import time

import settings


def set_state(state):
    # Write then rename, so the display never reads a half-written file
    tmp = settings.STATUS_FILE + ".tmp"
    try:
        with open(tmp, "w") as f:
            f.write(f"{state} {time.time()}")
        os.replace(tmp, settings.STATUS_FILE)
    except OSError:
        pass  # no display (e.g. running on Windows)
