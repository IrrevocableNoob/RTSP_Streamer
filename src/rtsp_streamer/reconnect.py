"""Reconnect backoff policy and the supervisor that drives it.

The supervisor is pure logic: a periodic ``tick(dt)`` consults a liveness
check and, while the stream is down, re-issues the reconnect action on an
exponential-backoff cadence and reports the reconnecting state. It holds no
Qt or VLC references, so it is fully unit-testable; the tile owns a timer
that calls ``tick`` once a second.
"""
from __future__ import annotations

from typing import Callable

_MAX_DELAY = 30.0


def backoff_delay(attempt: int) -> float:
    """Seconds to wait before retry number ``attempt`` (0-based).

    attempt 0 -> 1s, then 2, 4, 8, 16, capped at 30s. Negative -> 1s.
    """
    return min(_MAX_DELAY, 2.0 ** max(0, attempt))


class ReconnectSupervisor:
    def __init__(
        self,
        is_alive: Callable[[], bool],
        reconnect: Callable[[], None],
        on_state: Callable[[bool], None],
    ):
        self._is_alive = is_alive
        self._reconnect = reconnect
        self._on_state = on_state
        self._attempt = 0
        self._reconnecting = False
        self._cooldown = 0.0

    def tick(self, dt: float) -> None:
        if self._is_alive():
            if self._reconnecting:
                self._reconnecting = False
                self._attempt = 0
                self._cooldown = 0.0
                self._on_state(False)
            return

        if not self._reconnecting:
            self._reconnecting = True
            self._cooldown = 0.0
            self._on_state(True)

        self._cooldown -= dt
        if self._cooldown <= 0:
            self._reconnect()
            self._cooldown = backoff_delay(self._attempt)
            self._attempt += 1
