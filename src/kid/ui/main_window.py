"""K.I.D local system dashboard and chat window."""

from __future__ import annotations

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
from kid.hardware import inspect_hardware, model_warning
from kid.ollama import OllamaClient


class _Task(QThread):
    completed = Signal(object)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            self.completed.emit((True, self.fn()))
        except Exception as exc:  # surfaced in the application, not swallowed
            self.completed.emit((False, str(exc)))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings.from_env()
        self.client = OllamaClient(self.settings)
        self.hardware = inspect_hardware(self.settings.data_dir)
        self.setWindowTitle("K.I.D — Key Intelligence Driver")
        self.resize(900, 680)
        self.setStyleSheet(
            "QMainWindow, QWidget { background: #17191f; color: #e7e9ef; font-size: 14px; }"
            "QTextEdit, QLineEdit, QComboBox { background: #222630; border: 1px solid #3b414e; padding: 8px; }"
            "QPushButton { background: #3859a8; border: 0; padding: 9px; }"
        )
        root = QWidget()
        layout = QVBoxLayout(root)
        self.status_label = QLabel("Checking local Ollama…")
        self.hardware_label = QLabel(self._hardware_text())
        self.model_box = QComboBox()
        self.model_box.addItems([*self.settings.models().values()])
        self.model_box.setCurrentText(self.settings.primary_model)
        self.mode_box = QComboBox()
        self.mode_box.addItems(["Standard", "Lightweight"])
        self.warning_label = QLabel("")
        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        self.prompt = QLineEdit()
        self.prompt.setPlaceholderText("Message K.I.D locally…")
        self.send_button = QPushButton("Send")
        self.refresh_button = QPushButton("Refresh local status")
        layout.addWidget(QLabel("K.I.D · Local Intelligence"))
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
        self.model_box.currentTextChanged.connect(self._update_warning)
        self.mode_box.currentTextChanged.connect(self._select_mode)
        self.send_button.clicked.connect(self._send)
        self.prompt.returnPressed.connect(self._send)
        self.refresh_button.clicked.connect(self.refresh_status)
        self._history: list[dict[str, str]] = []
        self._update_warning()
        self.refresh_status()

    def _hardware_text(self) -> str:
        h = self.hardware
        return (
            f"{h.operating_system} · CPU: {h.cpu} ({h.logical_cpus} logical CPUs) · "
            f"RAM: {h.available_ram_gib:.1f}/{h.total_ram_gib:.1f} GiB available/total · "
            f"GPU: {h.gpu} · Free disk: {h.disk_free_gib:.1f} GiB"
        )

    def _select_mode(self, mode: str) -> None:
        if mode == "Lightweight":
            self.model_box.setCurrentText(self.settings.lightweight_model)
        elif self.settings.primary_model in [self.model_box.itemText(i) for i in range(self.model_box.count())]:
            self.model_box.setCurrentText(self.settings.primary_model)

    def _update_warning(self, *_args) -> None:
        selected = self.model_box.currentText()
        if self.mode_box.currentText() == "Standard" and self.hardware.available_ram_gib <= self.settings.memory_pressure_gib:
            if self.settings.lightweight_model in [self.model_box.itemText(i) for i in range(self.model_box.count())]:
                self.model_box.setCurrentText(self.settings.lightweight_model)
                self.mode_box.setCurrentText("Lightweight")
                selected = self.settings.lightweight_model
        warning = model_warning(
            selected,
            self.hardware.available_ram_gib,
            self.settings.model_ram_estimate(selected),
        )
        self.warning_label.setText(warning or "Model memory estimate: no immediate warning.")

    def refresh_status(self) -> None:
        self.status_label.setText("Checking Ollama /api/tags and loaded models…")
        task = _Task(self.client.status)
        task.completed.connect(self._show_status)
        self._status_task = task
        task.start()

    def _show_status(self, result) -> None:
        ok, value = result
        if not ok or not value.connected:
            error = value if not ok else value.error
            self.status_label.setText(f"Ollama disconnected · {error}")
            return
        self.hardware = inspect_hardware(self.settings.data_dir)
        self.hardware_label.setText(self._hardware_text())
        installed = list(value.installed_models)
        current = self.model_box.currentText()
        self.model_box.blockSignals(True)
        self.model_box.clear()
        self.model_box.addItems(installed)
        if current in installed:
            self.model_box.setCurrentText(current)
        self.model_box.blockSignals(False)
        self.status_label.setText(
            f"Ollama connected at {self.settings.ollama_url} · Installed: {', '.join(installed) or 'none'} · "
            f"Loaded: {', '.join(value.loaded_models) or 'none'}"
        )
        self._update_warning()

    def _send(self) -> None:
        prompt = self.prompt.text().strip()
        model = self.model_box.currentText()
        if not prompt:
            return
        if not model:
            self.status_label.setText("No installed model selected. Install a model yourself with Ollama, then refresh.")
            return
        self.prompt.clear()
        self.transcript.append(f"<b>You:</b> {prompt}")
        self.send_button.setEnabled(False)
        self.status_label.setText(f"Sending to local model {model}…")
        task = _Task(lambda: self.client.generate(model, prompt, self._history))
        task.completed.connect(lambda result: self._show_reply(prompt, model, result))
        self._chat_task = task
        task.start()

    def _show_reply(self, prompt: str, model: str, result) -> None:
        self.send_button.setEnabled(True)
        ok, value = result
        if not ok:
            self.transcript.append(f"<b>K.I.D error:</b> {value}")
            self.status_label.setText("Local inference failed; no cloud fallback was attempted.")
            return
        self.transcript.append(f"<b>K.I.D ({model}):</b> {value}")
        self._history.extend([{"role": "user", "content": prompt}, {"role": "assistant", "content": value}])
        self.status_label.setText(f"Response generated locally with {model}.")
