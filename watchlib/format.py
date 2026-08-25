"""
Number formatting for terminal output.

Pure functions - no printing, no colour, no state. Splitting them out means the
"is this number rendered sensibly" question can be tested without capturing stdout.
"""


def format_number(value):
    """
    Show a number at a precision that suits its size.

    A token price can be 0.0000004 and a token amount 3,000,000 in the same line;
    a fixed number of decimals makes one of them unreadable. This keeps roughly the
    same number of significant digits either way.
    """
    value = float(value)
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if abs(value) >= 1:
        return f"{value:,.2f}"
    if abs(value) >= 0.01:
        return f"{value:,.4f}"
    if value == 0:
        return "0"
    return f"{value:.6f}"


def format_change(percentage, decimals=1):
    """
    Percentage change as (text, colour name).

    The sign is always shown so a rise never reads as a plain number, and the colour
    is decided here rather than at each call site.
    """
    if percentage > 0:
        return f"(+{percentage:.{decimals}f}%)", "green"
    if percentage < 0:
        return f"({percentage:.{decimals}f}%)", "red"
    return "(0%)", "silver"


def format_duration(seconds):
    """Compact elapsed time: 45s, 12m, 3h4m."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes}m" if minutes else f"{hours}h"


def relative_change(baseline, current, higher_means_cheaper=False):
    """
    Percentage change from baseline to current.

    higher_means_cheaper flips the sign, for when the number being watched is a
    quantity rather than a price: if the same money buys more tokens than before,
    the token got cheaper, so the change should read negative. Getting this backwards
    is a silent bug - it produces a plausible number pointing the wrong way - so it
    is a named argument here rather than a reciprocal buried in caller code.
    """
    if baseline == 0:
        return 0.0
    if higher_means_cheaper:
        if current == 0:
            return 0.0
        return (baseline / current - 1) * 100
    return (current / baseline - 1) * 100
