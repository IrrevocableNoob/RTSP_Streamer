import os

from rtsp_streamer import app as app_module
from rtsp_streamer.app import _ensure_qt_platform, main


def test_main_exits_cleanly_without_vlc(qtbot, monkeypatch):
    # qtbot guarantees a QApplication already exists, so main() reuses it.
    monkeypatch.setattr(app_module, "check_vlc_or_explain", lambda: False)
    assert main([]) == 1


def test_qt_platform_defaults_to_xcb_on_linux(monkeypatch):
    monkeypatch.setattr("rtsp_streamer.app.sys.platform", "linux")
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
    _ensure_qt_platform()
    assert os.environ["QT_QPA_PLATFORM"] == "xcb"


def test_qt_platform_respects_existing_override(monkeypatch):
    monkeypatch.setattr("rtsp_streamer.app.sys.platform", "linux")
    monkeypatch.setenv("QT_QPA_PLATFORM", "wayland")
    _ensure_qt_platform()
    assert os.environ["QT_QPA_PLATFORM"] == "wayland"


def test_qt_platform_untouched_off_linux(monkeypatch):
    monkeypatch.setattr("rtsp_streamer.app.sys.platform", "win32")
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
    _ensure_qt_platform()
    assert "QT_QPA_PLATFORM" not in os.environ
