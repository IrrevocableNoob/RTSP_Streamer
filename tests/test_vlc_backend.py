import os
import sys
from datetime import datetime

import pytest

from rtsp_streamer.vlc_backend import (
    VlcPlayerBackend,
    VlcUnavailable,
    _instance_args,
    create_instance,
    ensure_output_dir,
    recording_basename,
    snapshot_filename,
)


def test_instance_args_default(monkeypatch):
    monkeypatch.delenv("RTSP_VLC_ARGS", raising=False)
    args = _instance_args()
    assert "--avcodec-hw=any" in args
    assert "--no-audio" in args


def test_instance_args_override_enforces_no_audio(monkeypatch):
    monkeypatch.setenv("RTSP_VLC_ARGS", "--avcodec-hw=none --vout=direct3d9")
    assert _instance_args() == ["--avcodec-hw=none", "--vout=direct3d9", "--no-audio"]


def test_snapshot_filename():
    assert snapshot_filename("Front Door", datetime(2026, 10, 29, 13, 5, 9)) == (
        "Front Door_20261029-130509.png"
    )


def test_recording_basename_has_no_extension():
    assert recording_basename("Back", datetime(2026, 10, 29, 13, 5, 9)) == (
        "Back_20261029-130509"
    )


def test_snapshot_filename_sanitizes_illegal_chars():
    out = snapshot_filename('a/b:c?', datetime(2026, 10, 29, 13, 5, 9))
    assert out == "a_b_c__20261029-130509.png"


def test_ensure_output_dir_creates(tmp_path):
    p = ensure_output_dir(str(tmp_path), "snapshots")
    assert os.path.isdir(p)
    assert p.endswith("snapshots")


def test_ensure_output_dir_unwritable_raises(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise OSError("read-only")

    monkeypatch.setattr(os, "makedirs", boom)
    with pytest.raises(OSError):
        ensure_output_dir(str(tmp_path), "recordings")


def test_create_instance_missing_vlc(monkeypatch):
    monkeypatch.setitem(sys.modules, "vlc", None)
    with pytest.raises(VlcUnavailable):
        create_instance()


def test_start_record_writes_mp4(fake_vlc):
    b = VlcPlayerBackend(fake_vlc.instance)
    b._url = "rtsp://h/1"
    b.start_record("C:/out/recordings/cam.mp4")
    assert b.is_recording()
    assert fake_vlc.last_mux == "mp4"


def test_stop_record_returns_path_and_clears(fake_vlc):
    b = VlcPlayerBackend(fake_vlc.instance)
    b._url = "rtsp://h/1"
    b.start_record("C:/out/recordings/cam.mp4")
    out = b.stop_record()
    assert out == "C:/out/recordings/cam.mp4"
    assert not b.is_recording()


def test_is_alive_reflects_player_state(fake_vlc):
    b = VlcPlayerBackend(fake_vlc.instance)
    b.attach(0)
    assert b.is_alive() is True
    b._player._state = "State.Ended"
    assert b.is_alive() is False


def test_is_alive_false_without_player(fake_vlc):
    b = VlcPlayerBackend(fake_vlc.instance)
    assert b.is_alive() is False


def test_attach_releases_mouse_and_key_input(fake_vlc, monkeypatch):
    # libvlc must not grab mouse/keyboard, or clicks never reach the Qt tile.
    monkeypatch.setattr("rtsp_streamer.vlc_backend.sys.platform", "win32")
    b = VlcPlayerBackend(fake_vlc.instance)
    b.attach(12345)
    assert b._player.hwnd == 12345
    assert b._player.mouse_input is False
    assert b._player.key_input is False


def test_embed_uses_hwnd_on_windows(fake_vlc, monkeypatch):
    from rtsp_streamer.vlc_backend import _embed_video
    monkeypatch.setattr("rtsp_streamer.vlc_backend.sys.platform", "win32")
    p = fake_vlc.instance.media_player_new()
    _embed_video(p, 42)
    assert p.hwnd == 42 and p.xwindow is None and p.nsobject is None


def test_embed_uses_xwindow_on_linux(fake_vlc, monkeypatch):
    from rtsp_streamer.vlc_backend import _embed_video
    monkeypatch.setattr("rtsp_streamer.vlc_backend.sys.platform", "linux")
    p = fake_vlc.instance.media_player_new()
    _embed_video(p, 42)
    assert p.xwindow == 42 and p.hwnd is None and p.nsobject is None


def test_embed_uses_nsobject_on_macos(fake_vlc, monkeypatch):
    from rtsp_streamer.vlc_backend import _embed_video
    monkeypatch.setattr("rtsp_streamer.vlc_backend.sys.platform", "darwin")
    p = fake_vlc.instance.media_player_new()
    _embed_video(p, 42)
    assert p.nsobject == 42 and p.hwnd is None and p.xwindow is None
