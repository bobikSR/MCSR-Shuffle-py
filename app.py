from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QWidget, QApplication, QPushButton, QVBoxLayout, QTabWidget
from PyQt6.QtCore import QSize, Qt
from gui.general_tab import GeneralTab
from gui.settings_tab import SettingsTab
from gui.about_tab import AboutTab


class MainWindow(QMainWindow):
    def __init__(self,):
        super().__init__()
        self.setWindowTitle("MCSR Shuffle")
        self.setFixedSize(QSize(400,450))
        layout = QVBoxLayout()
        tabs = QTabWidget()


        tabs.addTab(GeneralTab(), "general")
        tabs.addTab(SettingsTab(), "settings")
        tabs.addTab(AboutTab(), "about")
        layout.addWidget(tabs)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


if __name__ == "__main__":
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec()