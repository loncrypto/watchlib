"""
Optional audible alerts.

Everything here fails quietly. A missing player or a missing file should never take
down a watch that is otherwise working - the sound is a convenience, not the point.
"""
import os
import shutil
import subprocess

# Tried in order; the first one present on the system wins.
PLAYERS = ["mpg321", "mpg123", "ffplay", "aplay", "paplay"]

_QUIET_FLAGS = {
    "mpg321": ["-q"],
    "mpg123": ["-q"],
    "ffplay": ["-nodisp", "-autoexit", "-loglevel", "quiet"],
}


def find_player():
    """First available command-line audio player, or None."""
    for player in PLAYERS:
        if shutil.which(player):
            return player
    return None


def play_sound(path):
    """
    Play a sound file in the background. Returns True if playback was started.

    Non-blocking on purpose: a watch loop should not stall for the length of an
    alert sound.
    """
    if not path or not os.path.exists(path):
        return False
    player = find_player()
    if not player:
        return False
    try:
        subprocess.Popen(
            [player] + _QUIET_FLAGS.get(player, []) + [path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def make_speech(text, path):
    """
    Write a spoken-text mp3, for per-token alerts like "cake has gone down".

    Needs gtts (pip install gtts) and network access. Returns True on success;
    callers are expected to carry on without sound if it fails.
    """
    try:
        import gtts
    except ImportError:
        return False
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        gtts.gTTS(text).save(path)
        return True
    except Exception:
        return False
