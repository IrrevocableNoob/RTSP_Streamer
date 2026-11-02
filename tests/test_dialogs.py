from PyQt6.QtWidgets import QMessageBox

from rtsp_streamer.dialogs import AddStreamDialog, SettingsDialog, confirm_delete


def test_add_dialog_builds_url(qtbot):
    d = AddStreamDialog()
    qtbot.addWidget(d)
    d.name_edit.setText("Back")
    d.url_edit.setText("u:p@10.0.0.9/live")
    assert d.get_values() == ("Back", "rtsp://u:p@10.0.0.9/live")


def test_ok_disabled_when_blank(qtbot):
    d = AddStreamDialog()
    qtbot.addWidget(d)
    d.name_edit.setText("Back")
    d.url_edit.setText("")
    assert d.ok_button.isEnabled() is False


def test_ok_enabled_when_both_filled(qtbot):
    d = AddStreamDialog()
    qtbot.addWidget(d)
    d.name_edit.setText("Back")
    d.url_edit.setText("10.0.0.9/live")
    assert d.ok_button.isEnabled() is True


def test_settings_returns_folder(qtbot):
    d = SettingsDialog("D:/out")
    qtbot.addWidget(d)
    assert d.get_output_dir() == "D:/out"
    d.folder_edit.setText("E:/new")
    assert d.get_output_dir() == "E:/new"


def test_settings_ok_disabled_when_blank(qtbot):
    d = SettingsDialog("D:/out")
    qtbot.addWidget(d)
    assert d.ok_button.isEnabled() is True
    d.folder_edit.setText("")
    assert d.ok_button.isEnabled() is False


def test_confirm_delete_yes(qtbot, monkeypatch):
    monkeypatch.setattr(
        QMessageBox, "question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )
    assert confirm_delete(None, "Cam") is True


def test_confirm_delete_no(qtbot, monkeypatch):
    monkeypatch.setattr(
        QMessageBox, "question",
        lambda *a, **k: QMessageBox.StandardButton.No,
    )
    assert confirm_delete(None, "Cam") is False
