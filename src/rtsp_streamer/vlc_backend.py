"""VLC decode/record layer.

All playback, snapshotting, and recording goes through libvlc (python-vlc).
The module imports ``vlc`` lazily so the rest of the app — and its unit
tests — can run without a working libvlc. Widgets depend on the
``PlayerBackend`` Protocol, not on this concrete class, so they can be
tested with a fake.

Recording writes video-only directly to ``.mp4`` (``#transcode{acodec=none}``
drops the camera's audio — cameras commonly emit G.711 a-law, which MP4
cannot mux — while the H.264 video passes through without re-encoding).
libvlc finalizes the container on a clean stop.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Protocol, runtime_checkable

_ILLEGAL = set('<>:"/\\|?*')
_TIMESTAMP = "%Y%m%d-%H%M%S"
# libvlc instance options: hardware decode where available, never audio.
_INSTANCE_ARGS = ["--avcodec-hw=any", "--no-audio"]


class VlcUnavailable(RuntimeError):
    """Raised when libvlc cannot be imported or an instance cannot be built."""


def _embed_video(player, handle: int) -> None:
    """Embed libvlc's video output into a native window handle. The call is
    platform-specific: HWND on Windows, X11 window id on Linux/BSD, NSObject
    on macOS. (On Wayland the app runs under XWayland so the handle is an
    X11 id — see app._ensure_qt_platform.)"""
    if sys.platform.startswith("win"):
        player.set_hwnd(handle)
    elif sys.platform == "darwin":
        player.set_nsobject(handle)
    else:
        player.set_xwindow(handle)


def _sanitize(name: str) -> str:
    return "".join("_" if c in _ILLEGAL else c for c in name)


def snapshot_filename(stream_name: str, now: datetime) -> str:
    return f"{_sanitize(stream_name)}_{now:{_TIMESTAMP}}.png"


def recording_basename(stream_name: str, now: datetime) -> str:
    return f"{_sanitize(stream_name)}_{now:{_TIMESTAMP}}"


def ensure_output_dir(root: str, kind: str) -> str:
    """Return ``root/kind``, creating it if absent. Raises OSError if it cannot."""
    path = os.path.join(root, kind)
    os.makedirs(path, exist_ok=True)
    return path


@runtime_checkable
class PlayerBackend(Protocol):
    def attach(self, handle: int) -> None: ...
    def play(self, url: str) -> None: ...
    def stop(self) -> None: ...
    def take_snapshot(self, path: str) -> bool: ...
    def start_record(self, mkv_path: str) -> None: ...
    def stop_record(self) -> str: ...
    def is_recording(self) -> bool: ...
    def is_alive(self) -> bool: ...


# libvlc states that mean the stream is no longer rendering.
_DEAD_STATES = ("Error", "Ended", "Stopped", "NothingSpecial")


def _instance_args() -> list[str]:
    """libvlc args. RTSP_VLC_ARGS (space-separated) overrides the decode/vout
    defaults for tuning on quirky GPUs; --no-audio is always enforced."""
    override = os.environ.get("RTSP_VLC_ARGS")
    args = override.split() if override else list(_INSTANCE_ARGS)
    if "--no-audio" not in args:
        args.append("--no-audio")
    return args


def create_instance():
    """Build a libvlc Instance, or raise VlcUnavailable."""
    try:
        import vlc  # lazy: absence must not break import of this module
    except Exception as exc:  # ImportError, or OSError if libvlc dll missing
        raise VlcUnavailable("python-vlc / libvlc is not available") from exc
    if vlc is None:
        raise VlcUnavailable("python-vlc is not available")
    try:
        instance = vlc.Instance(_instance_args())
    except Exception as exc:
        raise VlcUnavailable("could not create a libvlc instance") from exc
    if instance is None:
        raise VlcUnavailable("libvlc returned a null instance")
    return instance


class VlcPlayerBackend:
    """Concrete PlayerBackend backed by a libvlc Instance."""

    def __init__(self, instance):
        self._instance = instance
        self._player = None
        self._url: str | None = None
        self._rec_player = None
        self._rec_path: str | None = None
        self._recording = False

    def _ensure_player(self):
        if self._player is None:
            self._player = self._instance.media_player_new()
        return self._player

    def attach(self, handle: int) -> None:
        player = self._ensure_player()
        _embed_video(player, handle)
        # Let Qt handle input; otherwise libvlc's vout window swallows the
        # clicks the tile needs for select / zoom / context menu.
        player.video_set_mouse_input(False)
        player.video_set_key_input(False)

    def play(self, url: str) -> None:
        self._url = url
        player = self._ensure_player()
        # RTSP over TCP is markedly more reliable than the UDP default for
        # Wi-Fi cameras (observed: UDP dropped frames where TCP was clean).
        media = self._instance.media_new(url, ":rtsp-tcp")
        player.set_media(media)
        player.play()

    def stop(self) -> None:
        if self._recording:
            self.stop_record()
        if self._player is not None:
            self._player.stop()

    def take_snapshot(self, path: str) -> bool:
        player = self._ensure_player()
        return player.video_take_snapshot(0, path, 0, 0) == 0

    def start_record(self, mp4_path: str) -> None:
        # Copy video, drop audio (MP4 cannot mux the camera's a-law track),
        # straight to an mp4 file. A separate player so recording is
        # independent of what the display tile is doing.
        sout = (
            f":sout=#transcode{{acodec=none}}"
            f":std{{access=file,mux=mp4,dst={mp4_path}}}"
        )
        media = self._instance.media_new(self._url or "", sout, ":sout-keep", ":rtsp-tcp")
        self._rec_player = self._instance.media_player_new()
        self._rec_player.set_media(media)
        self._rec_player.play()
        self._rec_path = mp4_path
        self._recording = True

    def stop_record(self) -> str:
        # libvlc finalizes the mp4 (writes the moov atom) on stop.
        if self._rec_player is not None:
            self._rec_player.stop()
        self._recording = False
        path = self._rec_path or ""
        self._rec_player = None
        self._rec_path = None
        return path

    def is_recording(self) -> bool:
        return self._recording

    def is_alive(self) -> bool:
        if self._player is None:
            return False
        state = str(self._player.get_state())
        return not any(state.endswith(d) for d in _DEAD_STATES)
