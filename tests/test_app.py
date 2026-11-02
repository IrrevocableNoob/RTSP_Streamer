from rtsp_streamer import app as app_module
from rtsp_streamer.app import main


def test_main_exits_cleanly_without_vlc(qtbot, monkeypatch):
    # qtbot guarantees a QApplication already exists, so main() reuses it.
    monkeypatch.setattr(app_module, "check_vlc_or_explain", lambda: False)
    assert main([]) == 1
