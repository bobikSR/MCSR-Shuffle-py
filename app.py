from PyQt6.QtWidgets import QMainWindow, QWidget, QApplication, QVBoxLayout, QTabWidget
from PyQt6.QtCore import QSize
from general_tab import GeneralTab
from settings_tab import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self,):
        super().__init__()
        self.first_draw = True

        self.setWindowTitle("MCSR Shuffle")
        self.setFixedSize(QSize(400,450))

        layout = QVBoxLayout()
        tabs = QTabWidget()
        tabs.currentChanged.connect(self.tab_changed)
        self.settings_tab = SettingsTab()
        self.general_tab = GeneralTab(self.settings_tab)
        tabs.addTab(self.general_tab, "general")
        tabs.addTab(self.settings_tab, "settings")
        layout.addWidget(tabs)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def tab_changed(self, idx: int):
        if self.first_draw:
            self.first_draw = False
            return
        if idx == 1: # changed to settings tab, nothing to check
            return
        self.general_tab.on_changed_to_general()


if __name__ == "__main__":
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec()