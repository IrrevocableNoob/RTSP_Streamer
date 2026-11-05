import sys

from rtsp_streamer.config import (
    AppConfig,
    Stream,
    config_path,
    default_output_dir,
    load_config,
    save_config,
)


def test_config_path_uses_appdata_when_frozen_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr("rtsp_streamer.config.sys.platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    import os
    assert config_path() == os.path.join(str(tmp_path), "RTSP_Streamer", "config.json")


def test_config_path_uses_xdg_when_frozen_linux(monkeypatch, tmp_path):
    import os
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr("rtsp_streamer.config.sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert config_path() == os.path.join(str(tmp_path), "RTSP_Streamer", "config.json")


def test_config_path_beside_script_when_not_frozen(monkeypatch):
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    assert config_path().endswith("config.json")


def test_load_missing_returns_defaults(tmp_path):
    cfg = load_config(str(tmp_path / "nope.json"))
    assert cfg.version == 1
    assert cfg.streams == []
    assert cfg.output_dir == default_output_dir()


def test_roundtrip_preserves_streams(tmp_path):
    p = str(tmp_path / "config.json")
    save_config(
        AppConfig(streams=[Stream("Front", "rtsp://h/1")], output_dir="D:/out"), p
    )
    cfg = load_config(p)
    assert cfg.streams[0].name == "Front"
    assert cfg.streams[0].url == "rtsp://h/1"
    assert cfg.output_dir == "D:/out"


def test_corrupt_json_returns_defaults(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("{not json")
    assert load_config(str(p)).streams == []


def test_unknown_version_returns_defaults(tmp_path):
    p = tmp_path / "config.json"
    p.write_text('{"version": 99, "streams": [], "output_dir": "x"}')
    assert load_config(str(p)).version == 1
