from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel

from mcsr_shuffle_py.gui.settings_tab import SettingsTab
from mcsr_shuffle_py.shuffle_class import MCSRShuffle


class GeneralTab(QWidget):
    def __init__(self, settings_tab: SettingsTab):
        super().__init__()
        layout = QVBoxLayout()
        btn_width = 150
        alignment = Qt.AlignmentFlag.AlignHCenter

        self.shuffler = MCSRShuffle()
        self.shuffler.config = settings_tab.get_config_from_values()
        self.settings_ref = settings_tab

        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(5)

        self.detect_btn = QPushButton("Detect instances")
        self.detect_btn.setFixedWidth(btn_width)
        self.detect_btn.clicked.connect(self.on_detect_click)
        layout.addWidget(self.detect_btn, alignment=alignment)

        self.found_label = QLabel(" ")
        layout.addWidget(self.found_label, alignment=alignment)

        layout.addStretch(2)

        self.start_btn = QPushButton("Start")
        self.start_btn.setFixedWidth(btn_width)
        self.start_btn.setDisabled(True)
        self.start_btn.clicked.connect(self.on_start_click)
        layout.addWidget(self.start_btn, alignment=alignment)

        self.state_label = QLabel(" ")
        layout.addWidget(self.state_label, alignment=alignment)

        self.progress_label = QLabel(" ")
        layout.addWidget(self.progress_label, alignment=alignment)

        layout.addStretch(3)

        self.pause_btn = QPushButton("Pause/Unpause")
        self.pause_btn.setFixedWidth(btn_width)
        self.pause_btn.setDisabled(True)
        self.pause_btn.clicked.connect(self.on_pause_click)
        layout.addWidget(self.pause_btn, alignment=alignment)

        self.stop_btn = QPushButton("Stop shuffle")
        self.stop_btn.setFixedWidth(btn_width)
        self.stop_btn.setDisabled(True)
        self.stop_btn.clicked.connect(self.on_stop_click)
        layout.addWidget(self.stop_btn, alignment=alignment)

        self.thread = QThread()
        self.setLayout(layout)

    def on_detect_click(self):
        self.shuffler.config = self.settings_ref.get_config_from_values()
        detect_str = self.shuffler.get_minecraft_instances()
        if detect_str == "":
            self.found_label.setText("An error occurred while detecting instances, see the latest log for more.")
        else:
            self.found_label.setText(detect_str)
        self.start_btn.setDisabled(not self.shuffler.can_play())
        self.state_label.setText(" ")
        self.progress_label.setText(" ")

    def on_start_click(self):
        self.shuffler.config = self.settings_ref.get_config_from_values()

        self.thread = QThread()
        self.shuffler.moveToThread(self.thread)
        self.thread.started.connect(self.shuffler.run)

        self.shuffler.finished_signal.connect(self.shuffle_finished)
        self.shuffler.finished_signal.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)

        self.shuffler.finished_error_signal.connect(self.shuffle_finished_with_error)
        self.shuffler.finished_error_signal.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)

        self.shuffler.pause_signal.connect(self.pause_signal)
        self.shuffler.completion_signal.connect(self.completion_signal)

        self.start_btn.setDisabled(True)
        self.state_label.setText("State: Running")
        self.progress_label.setText(f"Completions: 0/{len(self.shuffler.minecraft_instances)}")

        self.thread.start()

        self.pause_btn.setDisabled(False)
        self.stop_btn.setDisabled(False)

    def shuffle_finished(self):
        if all(inst.is_completed for inst in self.shuffler.minecraft_instances):
            self.state_label.setText("State: Finished!")
        else:
            self.state_label.setText(" ")
            self.progress_label.setText(" ")
            self.found_label.setText(" ")
        self.start_btn.setDisabled(True)
        self.pause_btn.setDisabled(True)
        self.stop_btn.setDisabled(True)
        self.shuffler.reset_values()

    def shuffle_finished_with_error(self):
        self.found_label.setText(" ")
        self.progress_label.setText(" ")
        self.state_label.setText("An error occurred during shuffling, see latest log for more.")
        self.start_btn.setDisabled(True)
        self.pause_btn.setDisabled(True)
        self.stop_btn.setDisabled(True)

    def pause_signal(self):
        self.state_label.setText(f"State: {'Paused' if self.shuffler.paused else 'Running'}")

    def completion_signal(self):
        self.progress_label.setText(f"Completions: {self.shuffler.completions}/{len(self.shuffler.minecraft_instances)}")

    def on_pause_click(self):
        self.shuffler.pause_shuffle()

    def on_stop_click(self):
        self.shuffler.exit_shuffle()