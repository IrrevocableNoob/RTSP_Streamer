from rtsp_streamer import main_window as mw
from rtsp_streamer.config import AppConfig, Stream, load_config
from rtsp_streamer.main_window import MainWindow


def _win(qtbot, tmp_path, fake_factory, streams=None):
    cfg = AppConfig(streams=list(streams or []), output_dir=str(tmp_path))
    w = MainWindow(cfg, str(tmp_path / "c.json"), fake_factory)
    qtbot.addWidget(w)
    return w


def test_add_relayouts_and_persists(qtbot, tmp_path, fake_factory):
    w = _win(qtbot, tmp_path, fake_factory)
    assert w.add_stream(Stream("A", "rtsp://h/1")) is True
    assert len(w.tiles) == 1
    assert load_config(str(tmp_path / "c.json")).streams[0].name == "A"


def test_sixteen_max(qtbot, tmp_path, fake_factory):
    w = _win(qtbot, tmp_path, fake_factory)
    for i in range(16):
        assert w.add_stream(Stream(f"S{i}", f"rtsp://h/{i}")) is True
    assert w.add_stream(Stream("X", "rtsp://h/x")) is False
    assert len(w.tiles) == 16
    assert w.add_button.isEnabled() is False


def test_minus_disabled_without_selection(qtbot, tmp_path, fake_factory):
    w = _win(qtbot, tmp_path, fake_factory)
    assert w.remove_button.isEnabled() is False


def test_select_enables_remove(qtbot, tmp_path, fake_factory):
    w = _win(qtbot, tmp_path, fake_factory, [Stream("A", "rtsp://h/1")])
    w.tiles[0].clicked.emit(w.tiles[0])
    assert w.selected_tile is w.tiles[0]
    assert w.remove_button.isEnabled() is True


def test_remove_selected_deletes_and_persists(qtbot, tmp_path, fake_factory, monkeypatch):
    monkeypatch.setattr(mw, "confirm_delete", lambda *a, **k: True)
    w = _win(qtbot, tmp_path, fake_factory, [Stream("A", "rtsp://h/1")])
    w.tiles[0].clicked.emit(w.tiles[0])
    w.remove_selected()
    assert len(w.tiles) == 0
    assert load_config(str(tmp_path / "c.json")).streams == []


def test_zoom_toggles(qtbot, tmp_path, fake_factory):
    w = _win(qtbot, tmp_path, fake_factory, [Stream("A", "rtsp://h/1")])
    w.toggle_zoom(w.tiles[0])
    assert w.zoomed_tile is w.tiles[0]
    w.toggle_zoom(w.tiles[0])
    assert w.zoomed_tile is None


def test_startup_builds_tiles_for_config(qtbot, tmp_path, fake_factory):
    w = _win(
        qtbot, tmp_path, fake_factory,
        [Stream("A", "rtsp://h/1"), Stream("B", "rtsp://h/2")],
    )
    assert len(w.tiles) == 2


def test_snapshot_calls_backend(qtbot, tmp_path, fake_factory):
    w = _win(qtbot, tmp_path, fake_factory, [Stream("A", "rtsp://h/1")])
    tile = w.tiles[0]
    tile.snapshot_requested.emit(tile)
    assert len(tile.backend.snapshots) == 1
    assert tile.backend.snapshots[0].endswith(".png")


def test_record_toggle_starts_and_stops(qtbot, tmp_path, fake_factory):
    w = _win(qtbot, tmp_path, fake_factory, [Stream("A", "rtsp://h/1")])
    tile = w.tiles[0]
    tile.record_toggle_requested.emit(tile)
    assert tile.backend.is_recording() is True
    assert tile.is_recording_indicator_visible() is True
    tile.record_toggle_requested.emit(tile)
    assert tile.backend.is_recording() is False
    assert tile.is_recording_indicator_visible() is False


def test_snapshot_handles_unwritable_dir(qtbot, tmp_path, fake_factory, monkeypatch):
    def boom(*a, **k):
        raise OSError("read-only")

    monkeypatch.setattr(mw, "ensure_output_dir", boom)
    w = _win(qtbot, tmp_path, fake_factory, [Stream("A", "rtsp://h/1")])
    tile = w.tiles[0]
    tile.snapshot_requested.emit(tile)  # must not raise
    assert len(tile.backend.snapshots) == 0


def test_failed_snapshot_surfaces_message(qtbot, tmp_path, fake_factory):
    w = _win(qtbot, tmp_path, fake_factory, [Stream("A", "rtsp://h/1")])
    tile = w.tiles[0]
    tile.backend.snapshot_ok = False
    tile.snapshot_requested.emit(tile)
    assert w.statusBar().currentMessage() != ""
