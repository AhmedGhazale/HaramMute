import sys
import sounddevice as sd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QPlainTextEdit, QSystemTrayIcon, QMenu, QLineEdit
)
from PyQt6.QtCore import QThread
from PyQt6.QtGui import QIcon, QAction, QIntValidator
from app.audio_worker import AudioWorker
import os


# ----- CONFIG CONSTANTS -----
HARDCODED_INPUT = "CABLE Output (VB-Audio Virtual , MME"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Haram Mute")
        self.resize(500, 400)

        # UI State
        self.is_service_active = False



        # Build UI
        self.init_ui()
        self.setup_tray()

        # Setup Worker and Thread
        self.worker_thread = QThread()
        self.worker = AudioWorker()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.load_model)
        self.worker_thread.start()

        # Connect signals
        self.worker.log_signal.connect(self.log_to_console)
        self.worker.timing_signal.connect(self.update_timing)
        self.worker.model_loaded.connect(self.on_model_loaded)

        # # Load model in background
        # self.worker.load_model()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Input (Static)
        layout.addWidget(QLabel(f"<b>Input Device:</b> {HARDCODED_INPUT}"))

        # Output Selection
        layout.addWidget(QLabel("Output Device:"))
        self.output_dropdown = QComboBox()
        self.populate_devices()
        layout.addWidget(self.output_dropdown)

        # Config Parameters
        params_layout = QHBoxLayout()
        self.edit_block = self.create_input_field("Block Size", str(4048), params_layout)
        self.edit_buf = self.create_input_field("Max Buffer", str(16000), params_layout)
        self.edit_back = self.create_input_field("Back Offset", str(1024), params_layout)

        layout.addLayout(params_layout)

        # timing
        self.lbl_processing = QLabel("Processing: -- ms")
        self.lbl_block = QLabel("Block time: -- ms")
        self.lbl_rtf = QLabel("RT factor: --")

        layout.addWidget(self.lbl_processing)
        layout.addWidget(self.lbl_block)
        layout.addWidget(self.lbl_rtf)

        # Controls
        self.btn_toggle = QPushButton("Start Service")
        self.btn_toggle.setEnabled(False)  # 🔒 disabled initially
        self.btn_toggle.clicked.connect(self.toggle_service)
        self.btn_toggle.setStyleSheet("background-color: #808080; color: white; font-weight: bold; padding: 10px;")
        layout.addWidget(self.btn_toggle)

        self.btn_logs = QPushButton("Show/Hide Logs")
        self.btn_logs.clicked.connect(self.toggle_logs)
        layout.addWidget(self.btn_logs)

        # Log Console
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setVisible(False)
        layout.addWidget(self.console)

    def create_input_field(self, label_text, default_val, parent_layout):
        """Helper to create a label + QLineEdit with integer validation."""
        v_layout = QVBoxLayout()
        v_layout.addWidget(QLabel(label_text))

        line_edit = QLineEdit()
        line_edit.setText(default_val)

        # Restrict input to integers only
        validator = QIntValidator(0, 1000000)
        line_edit.setValidator(validator)

        v_layout.addWidget(line_edit)
        parent_layout.addLayout(v_layout)
        return line_edit
    def populate_devices(self):
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if d['max_output_channels'] > 0:
                self.output_dropdown.addItem(f"{d['name']} ({d['hostapi']})", i)

    def toggle_service(self):
        if not self.is_service_active:
            # Sync Config to Worker

            self.worker.block_size = int(self.edit_block.text())
            self.worker.max_buffer_size = int(self.edit_buf.text())
            self.worker.back = int(self.edit_back.text())

            self.worker.output_device_idx = self.output_dropdown.currentData()

            self.worker.start_stream()
            self.btn_toggle.setText("Stop Service")
            self.btn_toggle.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 10px;")
            self.is_service_active = True
        else:
            self.worker.stop_stream()
            self.btn_toggle.setText("Start Service")
            self.btn_toggle.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 10px;")
            self.is_service_active = False

    def toggle_logs(self):
        self.console.setVisible(not self.console.isVisible())

    def log_to_console(self, text):
        self.console.appendPlainText(text)

    # ----- TRAY LOGIC -----
    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        # Note: You should provide an actual .png or .ico file here
        self.tray_icon.setIcon(QIcon(self.resource_path('assets/icon.png')))

        tray_menu = QMenu()
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.showNormal)

        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_model_loaded(self):
        self.btn_toggle.setEnabled(True)
        self.btn_toggle.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 10px;")

    def update_timing(self, processing_ms, block_ms):
        self.lbl_processing.setText(f"Processing: {processing_ms:.1f} ms")
        self.lbl_block.setText(f"Block time: {block_ms:.1f} ms")

        rtf = processing_ms / block_ms if block_ms > 0 else 0
        self.lbl_rtf.setText(f"RT factor: {rtf:.2f}")

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()

    def closeEvent(self, event):
        """Override close to minimize to tray."""
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Essential for tray apps
    window = MainWindow()
    window.show()
    sys.exit(app.exec())