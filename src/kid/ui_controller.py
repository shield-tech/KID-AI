"""K.I.D local UI controller for model and runtime status."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from kid.config import Settings
from kid.diagnostics import collect_debug_report
from kid.hardware import inspect_hardware, model_warning
from kid.ollama import OllamaClient
from kid.runtime import RuntimeManager


@dataclass
class AppStatus:
    model: str
    mode: str
    message: str
    warnings: list[str]


class _Task(QThread):
    completed = Signal(object)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            self.completed.emit((True, self.fn()))
        except Exception as exc:  # pragma: no cover - UI surfaces the exception
            self.completed.emit((False, str(exc)))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings.from_env()
        self.client = OllamaClient(self.settings)
        self.runtime = RuntimeManager(self.settings)
        self.hardware = inspect_hardware(self.settings.data_dir)
        self._history: list[dict[str, str]] = []

        self.setWindowTitle("K.I.D — Local Intelligence")
        self.resize(960, 740)
        self.setStyleSheet(
            "QMainWindow, QWidget { background: #17191f; color: #edf2ff; }"
            "QLabel, QTextEdit, QLineEdit, QComboBox { color: #edf2ff; }"
            "QTextEdit, QLineEdit, QComboBox { background: #1f2632; border: 1px solid #3a4356; padding: 8px; }"
            "QPushButton { background: #3d6ccb; border: 0; padding: 9px 16px; color: white; }"
        )

        root = QWidget()
        layout = QVBoxLayout(root)

        self.title_label = QLabel("K.I.D · local-only assistant")
        self.hardware_label = QLabel(self._hardware_text())
        self.status_label = QLabel("Checking local Ollama…")
        self.model_box = QComboBox()
        self.mode_box = QComboBox()
        self.mode_box.addItems(["Standard", "Lightweight"])
        self.warning_label = QLabel("")
        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        self.prompt = QLineEdit()
        self.prompt.setPlaceholderText("Message K.I.D locally…")
        self.send_button = QPushButton("Send")
        self.refresh_button = QPushButton("Refresh")

        layout.addWidget(self.title_label)
        layout.addWidget(self.hardware_label)
        layout.addWidget(self.status_label)
        layout.addWidget(QLabel("Installed model selection"))
        layout.addWidget(self.model_box)
        layout.addWidget(self.mode_box)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.transcript, 1)
        layout.addWidget(self.prompt)
        layout.addWidget(self.send_button)
        layout.addWidget(self.refresh_button)
        self.setCentralWidget(root)

        self.mode_box.currentTextChanged.connect(self._apply_mode)
        self.model_box.currentTextChanged.connect(self._update_warning)
        self.send_button.clicked.connect(self._send)
        self.prompt.returnPressed.connect(self._send)
        self.refresh_button.clicked.connect(self.refresh_status)

        self.refresh_status()

    def _hardware_text(self) -> str:
        hardware = inspect_hardware(self.settings.data_dir)
        return (
            f"OS: {hardware.operating_system} · CPU: {hardware.cpu} ({hardware.logical_cpus} logical) · "
            f"RAM: {hardware.available_ram_gib:.1f}/{hardware.total_ram_gib:.1f} GiB available/total · "
            f"GPU: {hardware.gpu} · Disk free: {hardware.disk_free_gib:.1f} GiB"
        )

    def _apply_mode(self, mode: str) -> None:
        if mode == "Lightweight":
            if self.settings.lightweight_model in [self.model_box.itemText(i) for i in range(self.model_box.count())]:
                self.model_box.setCurrentText(self.settings.lightweight_model)
        elif self.settings.primary_model in [self.model_box.itemText(i) for i in range(self.model_box.count())]:
            self.model_box.setCurrentText(self.settings.primary_model)
        self._update_warning()

    def _update_warning(self, *_args) -> None:
        selected = self.model_box.currentText()
        warning = model_warning(
            selected,
            self.hardware.available_ram_gib,
            self.settings.model_ram_estimate(selected),
        )
        self.warning_label.setText(warning or "Model memory estimate: no immediate warning.")

    def refresh_status(self) -> None:
        self.status_label.setText("Checking Ollama status…")
        task = _Task(self.client.status)
        task.completed.connect(self._show_status)
        task.start()

    def _show_status(self, result) -> None:
        ok, status = result
        if not ok or not status.connected:
            self.status_label.setText(f"Ollama disconnected · {status.error if hasattr(status, 'error') else status}")
            self.model_box.clear()
            return

        self.hardware = inspect_hardware(self.settings.data_dir)
        self.hardware_label.setText(self._hardware_text())

        items = list(status.installed_models)
        self.model_box.blockSignals(True)
        self.model_box.clear()
        self.model_box.addItems(items)
        if self.settings.primary_model in items:
            self.model_box.setCurrentText(self.settings.primary_model)
        elif items:
            self.model_box.setCurrentText(items[0])
        self.model_box.blockSignals(False)

        self.status_label.setText(
            f"Ollama connected at {self.settings.ollama_url} · "
            f"Installed: {', '.join(items) or 'none'} · Loaded: {', '.join(status.loaded_models) or 'none'}"
        )
        self._update_warning()

    def _send(self) -> None:
        prompt = self.prompt.text().strip()
        if not prompt:
            return
        model = self.model_box.currentText()
        if not model:
            self.status_label.setText("No installed model selected. Install a local model with Ollama first.")
            return

        self.prompt.clear()
        self.transcript.append(f"<b>You:</b> {prompt}")
        self.send_button.setEnabled(False)
        self.status_label.setText(f"Sending to local model {model}…")

        task = _Task(lambda: self.client.generate(model, prompt, self._history))
        task.completed.connect(lambda result: self._show_reply(prompt, model, result))
        task.start()

    def _show_reply(self, prompt: str, model: str, result) -> None:
        self.send_button.setEnabled(True)
        ok, value = result
        if not ok:
            self.transcript.append(f"<b>K.I.D error:</b> {value}")
            self.status_label.setText("Local inference failed; no cloud fallback attempted.")
            return

        self.transcript.append(f"<b>K.I.D ({model}):</b> {value}")
        self._history.extend([
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": value},
        ])
        self.status_label.setText(f"Response generated locally with {model}.")


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:  # pragma: no cover - UI-only import branch
        print(f"K.I.D desktop dependencies are missing: {exc}", flush=True)
        return 2

    app = QApplication([])
    app.setApplicationName("K.I.D")
    window = MainWindow()
    window.show()
    return app.exec()
