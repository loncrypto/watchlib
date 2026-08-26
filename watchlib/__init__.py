"""
watchlib - watch a changing number in the terminal.

Formatting, colours, thresholds and alerts, with no idea what the number means.
Hand it a function that returns one:

    from watchlib import Watcher

    Watcher(
        fetch=lambda: pool.quote_buy(0.1),
        input_amount=0.1, input_label="ETH", output_label="BASECAT",
        higher_means_cheaper=True,   # more tokens per ETH = price fell
        alert_threshold_pct=20,
    ).run()

Nothing here is chain-specific, so the same loop works for a Solana pool, an API
response, or anything else worth watching drift.
"""
from .console import (
    BUY_COLOR,
    COLORS,
    SELL_COLOR,
    WATCH_COLOR,
    activity_color,
    print_alert,
    print_colored,
    print_info,
    print_quote,
)
from .format import (
    format_change,
    format_duration,
    format_number,
    parse_amount,
    relative_change,
)
from .sound import find_player, make_speech, play_sound
from .watch import Watcher

__version__ = "0.1.0"

__all__ = [
    "Watcher",
    "COLORS",
    "BUY_COLOR",
    "SELL_COLOR",
    "WATCH_COLOR",
    "activity_color",
    "print_alert",
    "print_colored",
    "print_info",
    "print_quote",
    "format_change",
    "format_duration",
    "parse_amount",
    "format_number",
    "relative_change",
    "find_player",
    "make_speech",
    "play_sound",
]
