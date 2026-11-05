"""Load and persist application configuration (streams + output folder).

The config lives as ``config.json`` beside the executable. Loading never
raises: a missing, corrupt, or unknown-version file yields defaults so the
app always starts.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

SCHEMA_VERSION = 1


@dataclass
class Stream:
    name: str
    url: str


@dataclass
class AppConfig:
    streams: list[Stream] = field(default_factory=list)
    output_dir: str = ""
    version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.output_dir:
            self.output_dir = default_output_dir()


def default_output_dir() -> str:
    return str(Path.home() / "Videos" / "RTSP_Streamer")


def data_dir() -> str:
    """Where user data (config, logs) lives.

    A packaged (PyInstaller-frozen) build keeps it in the platform's per-user
    data location so it is always writable and independent of where the app is
    installed:
      - Windows: %APPDATA%\\RTSP_Streamer
      - macOS:   ~/Library/Application Support/RTSP_Streamer
      - Linux:   $XDG_CONFIG_HOME/RTSP_Streamer (default ~/.config/RTSP_Streamer)
    A dev checkout keeps it beside the launched script.
    """
    if getattr(sys, "frozen", False):
        if sys.platform.startswith("win"):
            root = os.environ.get("APPDATA") or os.path.expanduser("~")
        elif sys.platform == "darwin":
            root = os.path.expanduser("~/Library/Application Support")
        else:
            root = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
        base = os.path.join(root, "RTSP_Streamer")
        os.makedirs(base, exist_ok=True)
        return base
    if sys.argv and sys.argv[0]:
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.getcwd()


def config_path() -> str:
    return os.path.join(data_dir(), "config.json")


def load_config(path: str) -> AppConfig:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return AppConfig()

    if not isinstance(data, dict) or data.get("version") != SCHEMA_VERSION:
        return AppConfig()

    streams = [
        Stream(name=s.get("name", ""), url=s.get("url", ""))
        for s in data.get("streams", [])
        if isinstance(s, dict)
    ]
    return AppConfig(
        streams=streams,
        output_dir=data.get("output_dir", "") or default_output_dir(),
        version=SCHEMA_VERSION,
    )


def save_config(cfg: AppConfig, path: str) -> None:
    payload = {
        "version": SCHEMA_VERSION,
        "streams": [asdict(s) for s in cfg.streams],
        "output_dir": cfg.output_dir,
    }
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    os.replace(tmp, path)
