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


def config_path() -> str:
    """Path to config.json beside the executable (cwd in a dev checkout)."""
    base = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv and sys.argv[0] else os.getcwd()
    return os.path.join(base, "config.json")


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
