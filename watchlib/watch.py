"""
The watch loop: poll a number, notice when it moves, shout when it moves too far.

Deliberately knows nothing about prices, tokens or chains - it is handed a function
that returns a number. That is what lets the same loop watch a Uniswap quote, a
Solana pool, or anything else worth staring at.
"""
import time
from collections import deque

from .console import activity_color, print_alert, print_info, print_quote
from .format import format_number, relative_change


class Watcher:
    """
    Poll `fetch()` on an interval and report how its value drifts from the start.

    Two thresholds, doing different jobs:

      print_threshold_pct  - how much movement since the last printed line is worth
                             printing again. Stops a quiet market filling the screen
                             with identical rows.
      alert_threshold_pct  - how far below the starting value counts as an alert.
                             Raised by alert_backoff after each alert, so one long
                             slide reports at widening intervals instead of every tick.

    Set higher_means_cheaper when the fetched number is a quantity rather than a
    price - "tokens per 1 ETH" going up means the token got cheaper.
    """

    def __init__(self, fetch, *, label="", input_amount=None, input_label="",
                 output_label="", interval=5, print_threshold_pct=1.0,
                 alert_threshold_pct=20.0, alert_backoff=1.5,
                 higher_means_cheaper=False, render=None, on_alert=None,
                 sound_path=None, activity_window_seconds=3600, max_errors=None,
                 max_ticks=None):
        self.fetch = fetch
        self.label = label or output_label
        self.input_amount = input_amount
        self.input_label = input_label
        self.output_label = output_label
        self.interval = interval
        self.print_threshold_pct = print_threshold_pct
        self.alert_threshold_pct = alert_threshold_pct
        self.alert_backoff = alert_backoff
        self.higher_means_cheaper = higher_means_cheaper
        self.render = render or self._default_render
        self.on_alert = on_alert
        self.sound_path = sound_path
        self.activity_window_seconds = activity_window_seconds
        self.max_errors = max_errors
        self.max_ticks = max_ticks

        self.baseline = None
        self.last_printed = None
        self.alert_count = 0
        self.color = "lavender"
        self._events = deque()

    # -- rendering ----------------------------------------------------------

    def _default_render(self, value, change, color):
        if self.input_amount is not None:
            print_quote(self.input_amount, self.input_label, value,
                        self.output_label or self.label, change, color)
        else:
            print_quote(1, self.label, value, self.output_label, change, color)

    def _record_activity(self):
        """Track how often updates land, so the colour can reflect how lively it is."""
        now = int(time.time())
        self._events.append(now)
        while self._events and now - self._events[0] > self.activity_window_seconds:
            self._events.popleft()
        self.color = activity_color(len(self._events))

    # -- decisions ----------------------------------------------------------

    def change_from_start(self, value):
        return relative_change(self.baseline, value, self.higher_means_cheaper)

    def change_from_last(self, value):
        return relative_change(self.last_printed, value, self.higher_means_cheaper)

    def should_print(self, value):
        if self.last_printed is None:
            return True
        moved = abs(self.change_from_last(value)) >= self.print_threshold_pct
        return moved or self.should_alert(value)

    def should_alert(self, value):
        return self.change_from_start(value) <= -self.alert_threshold_pct

    # -- running ------------------------------------------------------------

    def _fetch_initial(self):
        """Keep trying for a first reading; without a baseline nothing else means anything."""
        attempts = 0
        while True:
            try:
                value = self.fetch()
                if value:
                    return value
            except Exception as e:
                print_info(f"ilk deger alinamadi: {e}")
            attempts += 1
            if self.max_errors and attempts >= self.max_errors:
                raise RuntimeError(f"{self.max_errors} denemede ilk deger alinamadi")
            time.sleep(self.interval)

    def _handle_alert(self, value, change):
        self.alert_count += 1
        message = (f"{self.label}: %{abs(change):.0f} dustu "
                   f"({format_number(value)}) - alarm #{self.alert_count}")
        print_alert(message)

        # Widen the bar so a continuing slide does not alert on every single tick.
        self.alert_threshold_pct *= self.alert_backoff
        print_info(f"    sonraki alarm esigi: %{self.alert_threshold_pct:.0f}")

        if self.sound_path:
            from .sound import play_sound
            play_sound(self.sound_path)
        if self.on_alert:
            self.on_alert(value, change, self.alert_count)

    def run(self):
        """
        Watch until interrupted.

        Ctrl+C pauses rather than exits - a second Ctrl+C while paused quits. Watching
        is usually something you want to step away from and come back to, not lose.
        """
        self.baseline = self._fetch_initial()
        self.last_printed = self.baseline
        self.render(self.baseline, 0.0, self.color)

        ticks = 0
        errors = 0

        while True:
            if self.max_ticks is not None and ticks >= self.max_ticks:
                return self
            ticks += 1

            try:
                value = self.fetch()
                if not value:
                    time.sleep(self.interval)
                    continue
                errors = 0

                if self.should_print(value):
                    change = self.change_from_start(value)
                    self._record_activity()
                    self.render(value, change, self.color)
                    self.last_printed = value

                    if self.should_alert(value):
                        self._handle_alert(value, change)

                time.sleep(self.interval)

            except KeyboardInterrupt:
                print_info(f"\n{self.label}: {self.alert_count} alarm verildi")
                try:
                    input("duraklatildi - devam icin Enter, cikis icin Ctrl+C: ")
                except KeyboardInterrupt:
                    print_info("cikiliyor")
                    return self
            except Exception as e:
                errors += 1
                print_info(f"hata: {e}")
                if self.max_errors and errors >= self.max_errors:
                    print_alert(f"{self.max_errors} ardisik hata - durduruluyor")
                    return self
                time.sleep(self.interval)
