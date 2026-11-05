"""Application bootstrap: logging, VLC availability check, main window, loop."""
from __future__ import annotations

import os
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from .config import config_path, load_config
from .logging_setup import setup_logging
from .main_window import MainWindow
from .vlc_backend import VlcPlayerBackend, VlcUnavailable, create_instance

_VLC_HELP = (
    "RTSP_Streamer needs VLC (64-bit, version 3.0 or newer) installed.\n\n"
    "Windows/macOS: get it from https://www.videolan.org/\n"
    "Linux: install your distribution's VLC package (e.g. 'sudo apt install vlc',\n"
    "or enable RPM Fusion/EPEL on Fedora/RHEL), then restart the app."
)


def _ensure_qt_platform() -> None:
    """On Linux, default Qt to the X11 (xcb) platform so the app runs under
    X11 or XWayland — the native-window video embedding (set_xwindow) needs an
    X11 window id. Only sets a default; an explicit QT_QPA_PLATFORM wins.
    Must run before any QApplication is created."""
    if sys.platform.startswith("linux"):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")


def _log_path() -> str:
    return os.path.join(os.path.dirname(config_path()), "app.log")


def check_vlc_or_explain():
    """Return a libvlc Instance, or None after showing an explanatory modal."""
    try:
        return create_instance()
    except VlcUnavailable:
        QMessageBox.critical(None, "VLC required", _VLC_HELP)
        return None


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    _ensure_qt_platform()  # must precede QApplication construction
    app = QApplication.instance() or QApplication(argv)

    setup_logging(_log_path())

    instance = check_vlc_or_explain()
    if not instance:
        return 1

    config = load_config(config_path())
    window = MainWindow(
        config, config_path(), lambda: VlcPlayerBackend(instance)
    )
    window.resize(960, 600)
    window.show()
    return app.exec()
