"""
Tests for watchlib. No network, no waiting - run directly:

    python tests/test_watchlib.py

The direction logic gets the most attention here on purpose: an inverted change is
the kind of bug that reports a confident wrong number instead of failing, and one
like it has shipped before.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from watchlib import Watcher, format_change, format_number, relative_change  # noqa: E402
from watchlib.console import activity_color  # noqa: E402
from watchlib.format import format_duration  # noqa: E402


def approx(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


# -- direction -------------------------------------------------------------

def test_price_up_is_positive():
    assert approx(relative_change(100, 110), 10.0)


def test_price_down_is_negative():
    assert approx(relative_change(100, 90), -10.0)


def test_more_tokens_means_cheaper():
    # Same money buys 8% more tokens -> the token got cheaper, so negative.
    change = relative_change(100, 108, higher_means_cheaper=True)
    assert change < 0
    assert approx(change, -7.4074074074074066)


def test_fewer_tokens_means_dearer():
    change = relative_change(100, 90, higher_means_cheaper=True)
    assert change > 0


def test_direction_flag_actually_flips_sign():
    plain = relative_change(100, 150)
    flipped = relative_change(100, 150, higher_means_cheaper=True)
    assert plain > 0 and flipped < 0


def test_zero_baseline_is_not_a_crash():
    assert relative_change(0, 50) == 0.0
    assert relative_change(100, 0, higher_means_cheaper=True) == 0.0


# -- formatting ------------------------------------------------------------

def test_format_number_scales_precision():
    assert format_number(1234567) == "1,234,567"
    assert format_number(12.3456) == "12.35"
    assert format_number(0.12345) == "0.1235"
    assert format_number(0.00001234) == "0.000012"
    assert format_number(0) == "0"


def test_format_change_shows_sign_and_color():
    text, color = format_change(5.2)
    assert text.startswith("(+") and color == "green"
    text, color = format_change(-5.2)
    assert text.startswith("(-") and color == "red"
    text, color = format_change(0)
    assert color == "silver"


def test_format_duration():
    assert format_duration(45) == "45s"
    assert format_duration(120) == "2m"
    assert format_duration(3600) == "1h"
    assert format_duration(3900) == "1h5m"


def test_activity_color_escalates():
    assert activity_color(0) == "lavender"
    assert activity_color(5) == "coral"
    assert activity_color(10) == "turquoise"
    assert activity_color(25) == "gold"


# -- watcher decisions -----------------------------------------------------

def make_watcher(values, **kwargs):
    it = iter(values)
    kwargs.setdefault("interval", 0)
    kwargs.setdefault("max_ticks", len(values))
    rendered = []
    alerts = []
    w = Watcher(
        fetch=lambda: next(it, values[-1]),
        label="TEST",
        render=lambda v, c, color: rendered.append((v, c)),
        on_alert=lambda v, c, n: alerts.append((v, c, n)),
        **kwargs,
    )
    return w, rendered, alerts


def test_quiet_market_does_not_reprint():
    # Baseline plus three near-identical readings: only the baseline line prints.
    w, rendered, _ = make_watcher([100, 100.1, 100.2, 100.1], print_threshold_pct=1)
    w.run()
    assert len(rendered) == 1


def test_movement_beyond_threshold_prints():
    w, rendered, _ = make_watcher([100, 105, 110], print_threshold_pct=1)
    w.run()
    assert len(rendered) > 1


def test_alert_fires_past_threshold():
    w, _, alerts = make_watcher([100, 75], alert_threshold_pct=20, print_threshold_pct=1)
    w.run()
    assert len(alerts) == 1
    assert alerts[0][1] <= -20


def test_alert_does_not_fire_below_threshold():
    w, _, alerts = make_watcher([100, 95], alert_threshold_pct=20, print_threshold_pct=1)
    w.run()
    assert alerts == []


def test_alert_threshold_backs_off():
    w, _, alerts = make_watcher(
        [100, 75, 74, 73], alert_threshold_pct=20, alert_backoff=2, print_threshold_pct=1
    )
    w.run()
    # After the first alert at -20%, the bar moves to -40%; -26% must not re-alert.
    assert len(alerts) == 1
    assert approx(w.alert_threshold_pct, 40.0)


def test_alert_uses_direction_flag():
    # Quantity going up by a third means roughly -25%: an alert, not a celebration.
    w, _, alerts = make_watcher(
        [100, 133], alert_threshold_pct=20, print_threshold_pct=1, higher_means_cheaper=True
    )
    w.run()
    assert len(alerts) == 1


def test_errors_do_not_stop_the_watch():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("gecici rpc hatasi")
        return 100 + calls["n"]

    rendered = []
    w = Watcher(fetch=flaky, label="TEST", interval=0, max_ticks=4,
                print_threshold_pct=0.1, render=lambda v, c, color: rendered.append(v))
    w.run()
    assert calls["n"] >= 4  # kept going past the failure


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ok  {test.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL  {test.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} gecti")
    sys.exit(1 if failed else 0)
