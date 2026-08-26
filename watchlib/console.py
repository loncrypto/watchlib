"""
Coloured terminal output.

One Console for the process. Creating one per printed line (as the earlier projects
did) rebuilds terminal detection on every tick for no benefit.
"""
from rich.console import Console
from rich.text import Text

from .format import format_change, format_number

_console = Console()

# Named colours so call sites say what they mean rather than carrying rgb triples.
COLORS = {
    "red": "bright_red",
    "green": "bright_green",
    "yellow": "bright_yellow",
    "silver": "rgb(192,192,192)",
    "grey": "rgb(120,120,120)",
    "lavender": "rgb(180,180,250)",
    "coral": "rgb(255,127,80)",
    "turquoise": "rgb(64,224,208)",
    "gold": "rgb(255,215,0)",
}

# Escalating colours for how busy a watch has been - the calmer the pool, the calmer
# the line. Ordered from most to least active; the first threshold met wins.
ACTIVITY_COLORS = [(20, "gold"), (10, "turquoise"), (5, "coral"), (0, "lavender")]


def style_for(color):
    return COLORS.get(color, color)


def print_colored(*segments):
    """Print (text, colour) pairs as one line."""
    line = Text()
    for text, color in segments:
        line.append(text, style=style_for(color))
    _console.print(line)


def activity_color(event_count):
    """Colour for a watch that has updated event_count times in its window."""
    for threshold, color in ACTIVITY_COLORS:
        if event_count >= threshold:
            return color
    return "lavender"


def print_quote(amount_in, label_in, amount_out, label_out, change=None, color="lavender",
                timestamp=None, target=None):
    """
    One watch line: time, what goes in, what comes out, and a trailing note.

        14:23 0.10 ETH = 877.53 BASECAT (-2%)      change given
        14:23 1.00 HYPE = 33,780 CHAMELEON (36,666) target given

    Pass `target` for limit orders: while waiting for a number to be reached, the
    number you are waiting for is more use than the distance to it.
    """
    import time

    stamp = timestamp or time.strftime("%H:%M")
    if target is not None:
        note, note_color = f"({format_number(target)})", "silver"
    else:
        note, note_color = format_change(change or 0)

    print_colored(
        (f"{stamp} ", "silver"),
        (f"{format_number(amount_in)} ", color),
        (f"{label_in} = ", "silver"),
        (f"{format_number(amount_out)} ", color),
        (f"{label_out} ", "silver"),
        (note, note_color),
    )


def print_alert(message, color="red"):
    """A line that should stand out from the stream of quotes."""
    print_colored(("  ! ", color), (message, color))


def print_info(message):
    print_colored((message, "grey"))
