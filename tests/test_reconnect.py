import pytest

from rtsp_streamer.reconnect import ReconnectSupervisor, backoff_delay


def _sup(alive_seq):
    state = {"i": 0, "reconnects": 0, "events": []}

    def is_alive():
        v = alive_seq[min(state["i"], len(alive_seq) - 1)]
        state["i"] += 1
        return v

    def reconnect():
        state["reconnects"] += 1

    def on_state(r):
        state["events"].append(r)

    return ReconnectSupervisor(is_alive, reconnect, on_state), state


def test_alive_never_reconnects():
    sup, st = _sup([True, True, True])
    for _ in range(3):
        sup.tick(1.0)
    assert st["reconnects"] == 0
    assert st["events"] == []


def test_drop_triggers_overlay_and_immediate_reconnect():
    sup, st = _sup([False])
    sup.tick(1.0)
    assert st["events"][0] is True
    assert st["reconnects"] == 1


def test_backoff_spacing_between_attempts():
    sup, st = _sup([False, False, False])
    for _ in range(3):
        sup.tick(1.0)
    # attempts at tick 1 (cooldown 0) and tick 2 (backoff_delay(0)=1s elapsed);
    # tick 3 is still inside backoff_delay(1)=2s, so no third attempt.
    assert st["reconnects"] == 2


def test_recovery_resets_and_clears_overlay():
    sup, st = _sup([False, True])
    sup.tick(1.0)
    sup.tick(1.0)
    assert st["events"] == [True, False]
    assert st["reconnects"] == 1


@pytest.mark.parametrize(
    "attempt,delay",
    [(0, 1), (1, 2), (2, 4), (3, 8), (4, 16), (5, 30), (10, 30)],
)
def test_backoff(attempt, delay):
    assert backoff_delay(attempt) == float(delay)


def test_negative_attempt_is_minimum():
    assert backoff_delay(-5) == 1.0
