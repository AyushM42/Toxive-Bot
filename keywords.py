import random
import re
import string
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = BASE_DIR / "media"

_yaml = YAML()  # round-trip mode keeps the comments in replies.yaml when the bot edits it
_yaml.preserve_quotes = True
_yaml.width = 4096


def words_in(text):
    return {w.strip(string.punctuation).lower() for w in text.split()}


MEDIA_TYPES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov"}


def resolve_file(name):
    """Path to a media file in the bot folder or media/. Only plain media file names are allowed."""
    name = Path(str(name)).name
    if Path(name).suffix.lower() not in MEDIA_TYPES:
        return None
    for folder in (BASE_DIR, MEDIA_DIR):
        path = folder / name
        if path.is_file():
            return path
    return None


class ReplyBook:
    """Keyword replies loaded from replies.yaml, reloaded whenever the file changes."""

    def __init__(self, path):
        self.path = Path(path)
        self.entries = []
        self._mtime = None
        self.reload()

    def reload(self):
        self._mtime = self.path.stat().st_mtime
        with open(self.path, encoding="utf-8") as f:
            self.entries = _yaml.load(f) or []
        print(f"Loaded {len(self.entries)} keyword replies")

    def reload_if_changed(self):
        try:
            if self.path.stat().st_mtime == self._mtime:
                return
            self.reload()
        except Exception as e:
            print(f"Could not reload {self.path.name}, keeping the old replies: {e}")

    def save(self):
        with open(self.path, "w", encoding="utf-8", newline="\n") as f:
            _yaml.dump(self.entries, f)
        self._mtime = self.path.stat().st_mtime

    def names(self):
        return [str(e.get("name", "?")) for e in self.entries]

    def add(self, triggers, text=None, file=None):
        entry = CommentedMap()
        entry["name"] = triggers[0]
        single = [t for t in triggers if " " not in t]
        phrases = [t for t in triggers if " " in t]
        if single:
            entry["words"] = _flow(single)
        if phrases:
            entry["contains"] = _flow(phrases)
        if text:
            entry["text"] = text
        if file:
            entry["file"] = file
        self.entries.append(entry)
        self.save()
        return entry

    def remove(self, name):
        for i, entry in enumerate(self.entries):
            if str(entry.get("name", "")).lower() == name.lower():
                del self.entries[i]
                self.save()
                return True
        return False

    def matching(self, text, username, now):
        """Entries that fire for this message, in file order."""
        return [e for e in self.entries if _matches(e, text, username, now) and random.random() < e.get("chance", 1)]


def _flow(items):
    seq = CommentedSeq(items)
    seq.fa.set_flow_style()  # [a, b] like the rest of the file
    return seq


def _matches(entry, text, username, now):
    if "only_users" in entry and username not in entry["only_users"]:
        return False
    if username in entry.get("except_users", []):
        return False
    if "hours" in entry:
        start, end = entry["hours"]
        if start < end:
            active = start <= now.hour < end
        else:
            active = now.hour >= start or now.hour < end
        if not active:
            return False

    if text in entry.get("exact", []):
        return True
    lowered = text.lower()
    if any(str(p).lower() in lowered for p in entry.get("contains", [])):
        return True
    words = words_in(text)
    if any(str(w).lower() in words for w in entry.get("words", [])):
        return True
    if "regex" in entry and re.search(entry["regex"], text, re.IGNORECASE):
        return True
    return False


def actions_for(entry):
    if "random" in entry:
        options = entry["random"]
        return [random.choices(options, weights=[o.get("weight", 1) for o in options])[0]]
    if "actions" in entry:
        return list(entry["actions"])
    return [entry]
