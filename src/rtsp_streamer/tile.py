"""A single camera tile: a thin header bar (name, recording dot, reconnect
notice) above a dedicated native video surface libvlc renders into.

The header sits ABOVE the video rather than floating over it: Qt cannot
reliably composite a widget on top of an embedded native video window on
Windows (an on-top overlay renders opaque and hides the video). A
non-overlapping header avoids that entirely. The tile never reparents on
zoom (that would invalidate the HWND); the window hides siblings and
resizes instead.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from .config import Stream
from .reconnect import ReconnectSupervisor
from .vlc_backend import PlayerBackend

_HEALTH_INTERVAL_MS = 1000

_STYLE = """
VideoTile { background: #111; }
VideoTile[selected="true"] { border: 2px solid #4da6ff; }
VideoTile[selected="false"] { border: 2px solid transparent; }
"""


class VideoTile(QFrame):
    double_clicked = pyqtSignal(object)
    clicked = pyqtSignal(object)
    snapshot_requested = pyqtSignal(object)
    record_toggle_requested = pyqtSignal(object)

    def __init__(self, stream: Stream, backend: PlayerBackend):
        super().__init__()
        self._stream = stream
        self._backend = backend
        self._attached = False
        self._recording = False

        self.setStyleSheet(_STYLE)
        self.setProperty("selected", False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

        # Header bar: name, recording dot, reconnecting notice. Lives ABOVE
        # the video (never on top of it) so it cannot hide the native surface.
        self._header = QWidget(self)
        self._header.setStyleSheet("background: #222;")
        hbar = QHBoxLayout(self._header)
        hbar.setContentsMargins(6, 2, 6, 2)
        hbar.setSpacing(6)

        self.name_label = QLabel(stream.name, self._header)
        self.name_label.setStyleSheet("color: white;")

        self._rec_dot = QLabel(self._header)
        self._rec_dot.setFixedSize(12, 12)
        self._rec_dot.setStyleSheet("background: red; border-radius: 6px;")
        self._rec_dot.setVisible(False)

        self._reconnect_label = QLabel("Reconnecting…", self._header)
        self._reconnect_label.setStyleSheet("color: #ffcc44;")
        self._reconnect_label.setVisible(False)

        hbar.addWidget(self.name_label)
        hbar.addWidget(self._rec_dot)
        hbar.addStretch(1)
        hbar.addWidget(self._reconnect_label)

        # Dedicated bare native widget libvlc renders into. Nothing overlaps
        # it, so the foreign HWND presents its frames unobstructed.
        self._video = QWidget(self)
        self._video.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self._video.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self._video.setStyleSheet("background: #000;")

        column = QVBoxLayout(self)
        column.setContentsMargins(2, 2, 2, 2)
        column.setSpacing(0)
        column.addWidget(self._header)
        column.addWidget(self._video, 1)

        # Quietly supervise the stream: on a drop, show the reconnecting
        # notice and re-issue play() on a backoff cadence — no dialogs,
        # no focus stealing.
        self._supervisor = ReconnectSupervisor(
            is_alive=self._backend.is_alive,
            reconnect=lambda: self._backend.play(self._stream.url),
            on_state=self.set_reconnecting,
        )
        self._health_timer = QTimer(self)
        self._health_timer.setInterval(_HEALTH_INTERVAL_MS)
        self._health_timer.timeout.connect(self._reconnect_tick)

    # --- backend lifecycle -------------------------------------------------
    @property
    def stream(self) -> Stream:
        return self._stream

    @property
    def backend(self) -> PlayerBackend:
        return self._backend

    def showEvent(self, event):
        super().showEvent(event)
        if not self._attached:
            self._backend.attach(int(self._video.winId()))
            self._backend.play(self._stream.url)
            self._attached = True
            self._health_timer.start()

    def _reconnect_tick(self) -> None:
        self._supervisor.tick(_HEALTH_INTERVAL_MS / 1000.0)


    # --- selection ---------------------------------------------------------
    def set_selected(self, value: bool) -> None:
        self.setProperty("selected", value)
        self.style().unpolish(self)
        self.style().polish(self)

    @property
    def selected(self) -> bool:
        return bool(self.property("selected"))

    # --- recording / reconnect indicators ---------------------------------
    def set_recording(self, value: bool) -> None:
        self._recording = value
        self._rec_dot.setVisible(value)

    def is_recording_indicator_visible(self) -> bool:
        # isHidden() reflects the explicit on/off state regardless of whether
        # an ancestor is currently shown (so it is correct in headless tests).
        return not self._rec_dot.isHidden()

    def set_reconnecting(self, value: bool) -> None:
        self._reconnect_label.setVisible(value)

    def is_reconnecting_visible(self) -> bool:
        return not self._reconnect_label.isHidden()

    # --- mouse / context menu ---------------------------------------------
    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
        super().mousePressEvent(event)

    def build_context_menu(self) -> QMenu:
        menu = QMenu(self)
        snap = QAction("Snapshot", menu)
        snap.triggered.connect(lambda: self.snapshot_requested.emit(self))
        menu.addAction(snap)

        label = "Stop Recording" if self._recording else "Start Recording"
        rec = QAction(label, menu)
        rec.triggered.connect(lambda: self.record_toggle_requested.emit(self))
        menu.addAction(rec)
        return menu

    def _on_context_menu(self, pos):
        self.build_context_menu().exec(self.mapToGlobal(pos))
