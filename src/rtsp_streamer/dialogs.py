"""Modal dialogs: add a stream, edit settings, confirm a delete."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .urls import build_rtsp_url


class AddStreamDialog(QDialog):
    """Collect a friendly name and the URL body (scheme is prepended)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add Stream")

        self.name_edit = QLineEdit(self)
        self.url_edit = QLineEdit(self)
        self.url_edit.setPlaceholderText("user:pass@host:554/path")

        form = QFormLayout()
        form.addRow("Name", self.name_edit)
        form.addRow("URL (rtsp:// prepended)", self.url_edit)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._buttons)

        self.name_edit.textChanged.connect(self._refresh_ok)
        self.url_edit.textChanged.connect(self._refresh_ok)
        self._refresh_ok()

    def _refresh_ok(self) -> None:
        both = bool(self.name_edit.text().strip()) and bool(self.url_edit.text().strip())
        self.ok_button.setEnabled(both)

    def get_values(self) -> tuple[str, str]:
        return self.name_edit.text().strip(), build_rtsp_url(self.url_edit.text())


class SettingsDialog(QDialog):
    """Single setting: the output folder for snapshots and recordings."""

    def __init__(self, initial: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Settings")

        self.folder_edit = QLineEdit(initial, self)
        browse = QPushButton("Browse…", self)
        browse.clicked.connect(self._browse)

        row = QHBoxLayout()
        row.addWidget(self.folder_edit)
        row.addWidget(browse)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(buttons)

        self.folder_edit.textChanged.connect(self._refresh_ok)
        self._refresh_ok()

    def _refresh_ok(self) -> None:
        self.ok_button.setEnabled(bool(self.folder_edit.text().strip()))

    def _browse(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Output folder", self.folder_edit.text()
        )
        if chosen:
            self.folder_edit.setText(chosen)

    def get_output_dir(self) -> str:
        return self.folder_edit.text()


def confirm_delete(parent: QWidget | None, stream_name: str) -> bool:
    reply = QMessageBox.question(
        parent,
        "Delete stream",
        f"Delete '{stream_name}'?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes
