"""Shared test fixtures.

``fake_vlc`` stubs enough of the python-vlc surface for the backend's state
machine and record/remux wiring to be tested without a real libvlc. The
real libvlc calls are verified by the manual checklist in README.md.
"""
import re

import pytest


class _FakePlayer:
    def __init__(self):
        self.hwnd = None
        self.media = None
        self._played = False

    def set_hwnd(self, hwnd):
        self.hwnd = hwnd

    def video_set_mouse_input(self, enabled):
        self.mouse_input = enabled

    def video_set_key_input(self, enabled):
        self.key_input = enabled

    def set_media(self, media):
        self.media = media

    def play(self):
        self._played = True
        return 0

    def stop(self):
        self._played = False

    def is_playing(self):
        # A record/remux player "finishes" immediately in tests.
        return False

    def get_state(self):
        return getattr(self, "_state", "State.Playing")

    def video_take_snapshot(self, num, path, width, height):
        with open(path, "wb") as fh:
            fh.write(b"\x89PNG\r\n")
        return 0  # libvlc: 0 == success


class _FakeInstance:
    def __init__(self, ns):
        self._ns = ns

    def media_player_new(self):
        return _FakePlayer()

    def media_new(self, mrl, *options):
        opts = " ".join(options)
        match = re.search(r"mux=(\w+)", opts)
        if match:
            self._ns.last_mux = match.group(1)
        return object()


class _FakeVlc:
    def __init__(self):
        self.last_mux = None
        self.instance = _FakeInstance(self)


@pytest.fixture
def fake_vlc():
    return _FakeVlc()


class _FakeBackend:
    """In-memory PlayerBackend for widget/window tests."""

    def __init__(self):
        self.attached = None
        self.played = None
        self.stopped = False
        self.snapshots = []
        self.last_mkv = None
        self._recording = False
        self.alive = True
        self.snapshot_ok = True

    def attach(self, hwnd):
        self.attached = hwnd

    def is_alive(self):
        return self.alive

    def play(self, url):
        self.played = url

    def stop(self):
        self.stopped = True

    def take_snapshot(self, path):
        if not self.snapshot_ok:
            return False
        self.snapshots.append(path)
        return True

    def start_record(self, mkv_path):
        self.last_mkv = mkv_path
        self._recording = True

    def stop_record(self):
        self._recording = False
        return (self.last_mkv or "rec.mkv")[:-4] + ".mp4"

    def is_recording(self):
        return self._recording


@pytest.fixture
def fake_backend():
    return _FakeBackend()


@pytest.fixture
def fake_factory():
    """Returns a callable producing fresh fake backends (for MainWindow)."""
    return lambda: _FakeBackend()
