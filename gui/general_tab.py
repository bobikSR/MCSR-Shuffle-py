from PyQt6.QtCore import Qt
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

        self.detect_btn = QPushButton("Detect instances")
        self.detect_btn.setFixedWidth(btn_width)
        self.detect_btn.clicked.connect(self.on_detect_click)
        layout.addWidget(self.detect_btn, alignment=alignment)

        self.found_label = QLabel(" ")
        layout.addWidget(self.found_label, alignment=Qt.AlignmentFlag.AlignTop | alignment)

        self.start_btn = QPushButton("Start")
        self.start_btn.setFixedWidth(btn_width)
        self.start_btn.setDisabled(True)
        layout.addWidget(self.start_btn, alignment=alignment)

        self.setLayout(layout)

    def on_detect_click(self):
        self.shuffler.config = self.settings_ref.get_config_from_values()
        detect_str = self.shuffler.get_minecraft_instances()
        self.found_label.setText(detect_str)
        self.start_btn.setDisabled(not self.shuffler.can_play())