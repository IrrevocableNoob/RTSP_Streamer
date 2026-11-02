"""The main window: toolbar, auto-fit grid of tiles, selection, zoom, and
the snapshot/record wiring.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Callable

from PyQt6.QtWidgets import (
    QGridLayout,
    QMainWindow,
    QToolBar,
    QWidget,
)
from PyQt6.QtGui import QAction

from .config import AppConfig, Stream, save_config
from .dialogs import AddStreamDialog, SettingsDialog, confirm_delete
from .grid import grid_dimensions
from .tile import VideoTile
from .vlc_backend import (
    PlayerBackend,
    ensure_output_dir,
    recording_basename,
    snapshot_filename,
)

MAX_STREAMS = 16
_log = logging.getLogger("rtsp_streamer")


class MainWindow(QMainWindow):
    def __init__(
        self,
        config: AppConfig,
        config_path: str,
        backend_factory: Callable[[], PlayerBackend],
    ):
        super().__init__()
        self.setWindowTitle("RTSP_Streamer")
        self._config = config
        self._config_path = config_path
        self._backend_factory = backend_factory

        self.tiles: list[VideoTile] = []
        self.selected_tile: VideoTile | None = None
        self.zoomed_tile: VideoTile | None = None

        toolbar = QToolBar()
        self.addToolBar(toolbar)
        self.add_button = QAction("+", self)
        self.remove_button = QAction("−", self)  # minus sign
        self.settings_button = QAction("⚙", self)  # gear
        self.add_button.triggered.connect(self._on_add_clicked)
        self.remove_button.triggered.connect(self.remove_selected)
        self.settings_button.triggered.connect(self._on_settings_clicked)
        toolbar.addAction(self.add_button)
        toolbar.addAction(self.remove_button)
        toolbar.addAction(self.settings_button)

        central = QWidget()
        self._grid = QGridLayout(central)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(2)
        self.setCentralWidget(central)

        # Startup: open every remembered stream.
        for stream in self._config.streams:
            self._build_tile(stream)
        self.relayout()
        self._refresh_toolbar()

    # --- tile creation -----------------------------------------------------
    def _build_tile(self, stream: Stream) -> VideoTile:
        backend = self._backend_factory()
        tile = VideoTile(stream, backend)
        tile.double_clicked.connect(self.toggle_zoom)
        tile.clicked.connect(self._select)
        tile.snapshot_requested.connect(self._on_snapshot)
        tile.record_toggle_requested.connect(self._on_record_toggle)
        self.tiles.append(tile)
        return tile

    def add_stream(self, stream: Stream) -> bool:
        if len(self.tiles) >= MAX_STREAMS:
            _log.info("refused add: at max of %d streams", MAX_STREAMS)
            return False
        self._config.streams.append(stream)
        self._build_tile(stream)
        self.relayout()
        self._persist()
        self._refresh_toolbar()
        return True

    def remove_selected(self) -> None:
        tile = self.selected_tile
        if tile is None:
            return
        if not confirm_delete(self, tile.stream.name):
            return
        tile.backend.stop()
        self.tiles.remove(tile)
        self._config.streams = [s for s in self._config.streams if s is not tile.stream]
        self.selected_tile = None
        if self.zoomed_tile is tile:
            self.zoomed_tile = None
        tile.setParent(None)
        tile.deleteLater()
        self.relayout()
        self._persist()
        self._refresh_toolbar()

    # --- selection / zoom --------------------------------------------------
    def _select(self, tile: VideoTile) -> None:
        self.selected_tile = tile
        for t in self.tiles:
            t.set_selected(t is tile)
        self._refresh_toolbar()

    def toggle_zoom(self, tile: VideoTile) -> None:
        self.zoomed_tile = None if self.zoomed_tile is tile else tile
        self.relayout()

    def relayout(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

        if self.zoomed_tile is not None:
            for t in self.tiles:
                t.setVisible(t is self.zoomed_tile)
            self._grid.addWidget(self.zoomed_tile, 0, 0)
            self.zoomed_tile.setParent(self.centralWidget())
            self.zoomed_tile.setVisible(True)
            return

        for t in self.tiles:
            t.setVisible(True)
        rows, cols = grid_dimensions(len(self.tiles))
        for index, tile in enumerate(self.tiles):
            tile.setParent(self.centralWidget())
            self._grid.addWidget(tile, index // cols, index % cols)
            tile.setVisible(True)

    # --- snapshot / record -------------------------------------------------
    def _on_snapshot(self, tile: VideoTile) -> None:
        try:
            folder = ensure_output_dir(self._config.output_dir, "snapshots")
        except OSError as exc:
            self._warn_output(exc)
            return
        path = os.path.join(folder, snapshot_filename(tile.stream.name, datetime.now()))
        if tile.backend.take_snapshot(path):
            self.statusBar().showMessage(f"Snapshot saved: {path}", 5000)
        else:
            _log.warning("snapshot failed for %s", tile.stream.name)
            self.statusBar().showMessage("Snapshot failed (no frame available yet).", 5000)

    def _on_record_toggle(self, tile: VideoTile) -> None:
        if tile.backend.is_recording():
            tile.backend.stop_record()
            tile.set_recording(False)
            return
        try:
            folder = ensure_output_dir(self._config.output_dir, "recordings")
        except OSError as exc:
            self._warn_output(exc)
            return
        mp4 = os.path.join(
            folder, recording_basename(tile.stream.name, datetime.now()) + ".mp4"
        )
        tile.backend.start_record(mp4)
        tile.set_recording(True)

    def _warn_output(self, exc: OSError) -> None:
        _log.warning("output folder not writable: %s", exc)
        self.statusBar().showMessage(f"Could not write to output folder: {exc}", 5000)

    # --- toolbar actions ---------------------------------------------------
    def _on_add_clicked(self) -> None:
        dialog = AddStreamDialog(self)
        if dialog.exec():
            name, url = dialog.get_values()
            self.add_stream(Stream(name, url))

    def _on_settings_clicked(self) -> None:
        dialog = SettingsDialog(self._config.output_dir, self)
        if dialog.exec():
            self._config.output_dir = dialog.get_output_dir()
            self._persist()

    # --- persistence -------------------------------------------------------
    def _persist(self) -> None:
        save_config(self._config, self._config_path)

    def _refresh_toolbar(self) -> None:
        self.add_button.setEnabled(len(self.tiles) < MAX_STREAMS)
        self.remove_button.setEnabled(self.selected_tile is not None)
