from PyQt6.QtCore import Qt

from rtsp_streamer.config import Stream
from rtsp_streamer.tile import VideoTile


def test_selection_border(qtbot, fake_backend):
    t = VideoTile(Stream("A", "rtsp://h/1"), fake_backend)
    qtbot.addWidget(t)
    t.set_selected(True)
    assert t.selected is True
    assert t.property("selected") is True
    t.set_selected(False)
    assert t.selected is False


def test_double_click_emits(qtbot, fake_backend):
    t = VideoTile(Stream("A", "rtsp://h/1"), fake_backend)
    qtbot.addWidget(t)
    with qtbot.waitSignal(t.double_clicked, timeout=1000):
        qtbot.mouseDClick(t, Qt.MouseButton.LeftButton)


def test_left_click_emits_clicked(qtbot, fake_backend):
    t = VideoTile(Stream("A", "rtsp://h/1"), fake_backend)
    qtbot.addWidget(t)
    with qtbot.waitSignal(t.clicked, timeout=1000):
        qtbot.mouseClick(t, Qt.MouseButton.LeftButton)


def test_context_menu_actions_emit(qtbot, fake_backend):
    t = VideoTile(Stream("A", "rtsp://h/1"), fake_backend)
    qtbot.addWidget(t)
    actions = {a.text(): a for a in t.build_context_menu().actions()}
    with qtbot.waitSignal(t.snapshot_requested, timeout=1000):
        actions["Snapshot"].trigger()
    with qtbot.waitSignal(t.record_toggle_requested, timeout=1000):
        actions["Start Recording"].trigger()


def test_record_action_label_reflects_state(qtbot, fake_backend):
    t = VideoTile(Stream("A", "rtsp://h/1"), fake_backend)
    qtbot.addWidget(t)
    t.set_recording(True)
    labels = [a.text() for a in t.build_context_menu().actions()]
    assert "Stop Recording" in labels
    assert t.is_recording_indicator_visible() is True


def test_name_label_shows_stream_name(qtbot, fake_backend):
    t = VideoTile(Stream("Front Door", "rtsp://h/1"), fake_backend)
    qtbot.addWidget(t)
    assert t.name_label.text() == "Front Door"


def test_reconnecting_overlay_toggles(qtbot, fake_backend):
    t = VideoTile(Stream("A", "rtsp://h/1"), fake_backend)
    qtbot.addWidget(t)
    t.set_reconnecting(True)
    assert t.is_reconnecting_visible() is True
    t.set_reconnecting(False)
    assert t.is_reconnecting_visible() is False


def test_reconnect_tick_reconnects_dead_stream(qtbot, fake_backend):
    t = VideoTile(Stream("A", "rtsp://h/1"), fake_backend)
    qtbot.addWidget(t)
    fake_backend.alive = False
    t._reconnect_tick()
    assert t.is_reconnecting_visible() is True
    assert fake_backend.played == "rtsp://h/1"


def test_reconnect_tick_restores_on_recovery(qtbot, fake_backend):
    t = VideoTile(Stream("A", "rtsp://h/1"), fake_backend)
    qtbot.addWidget(t)
    fake_backend.alive = False
    t._reconnect_tick()
    fake_backend.alive = True
    t._reconnect_tick()
    assert t.is_reconnecting_visible() is False
