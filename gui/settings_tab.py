import json
from json import JSONDecodeError

from PyQt6.QtCore import QLocale
from PyQt6.QtGui import QIntValidator, QDoubleValidator
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QCheckBox, QHBoxLayout, QPushButton
import os


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        form = QFormLayout()
        layout.addLayout(form)

        int_validator = QIntValidator()
        double_validator = QDoubleValidator()
        double_validator.setLocale(QLocale(QLocale.Language.English))
        checkbox_size = 30
        int_size = 40
        double_size = 50
        hotkey_size = 60

        # form
        self.lower_bound = QLineEdit()
        self.lower_bound.setValidator(int_validator)
        self.lower_bound.setFixedWidth(int_size)
        form.addRow("Lower bound of interval:", self.lower_bound)

        self.upper_bound = QLineEdit()
        self.upper_bound.setValidator(int_validator)
        self.upper_bound.setFixedWidth(int_size)
        form.addRow("Upper bound of interval:", self.upper_bound)

        self.pause_hotkey = QLineEdit()
        self.pause_hotkey.setFixedWidth(hotkey_size)
        form.addRow("Pause hotkey:", self.pause_hotkey)

        self.exit_hotkey = QLineEdit()
        self.exit_hotkey.setFixedWidth(hotkey_size)
        form.addRow("Exit hotkey:", self.exit_hotkey)

        self.parallel_world_gen = QCheckBox()
        self.parallel_world_gen.setFixedWidth(checkbox_size)
        form.addRow("Parallel world generation:", self.parallel_world_gen)

        self.debug = QCheckBox()
        self.debug.setFixedWidth(checkbox_size)
        form.addRow("Debug:", self.debug)

        self.ensure_correct_instance_retry = QLineEdit()
        self.ensure_correct_instance_retry.setValidator(double_validator)
        self.ensure_correct_instance_retry.setFixedWidth(double_size)
        form.addRow("Ensure correct instance retry pause (s):", self.ensure_correct_instance_retry)

        self.before_switch_esc_press_pause = QLineEdit()
        self.before_switch_esc_press_pause.setValidator(double_validator)
        self.before_switch_esc_press_pause.setFixedWidth(double_size)
        form.addRow("Before switch 'esc' press pause (s):", self.before_switch_esc_press_pause)

        self.set_up_key_press_pause = QLineEdit()
        self.set_up_key_press_pause.setValidator(double_validator)
        self.set_up_key_press_pause.setFixedWidth(double_size)
        form.addRow("Set up key press pause (s):", self.set_up_key_press_pause)
        self.load_from_json()
        form.addRow(" ", None)

        # save button
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_to_json)
        self.save_button.setFixedWidth(100)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_from_json(self):
        if os.path.isfile("config.json"):
            config_path = "config.json"
        else:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        try:
            with open(config_path, "r") as config:
                loaded_config = json.load(config)
                self.lower_bound.setText(str(loaded_config["lower_bound"]))
                self.upper_bound.setText(str(loaded_config["upper_bound"]))
                self.pause_hotkey.setText(str(loaded_config["pause_hotkey"]))
                self.exit_hotkey.setText(str(loaded_config["exit_hotkey"]))
                self.parallel_world_gen.setChecked(loaded_config["parallel_world_gen"])
                self.debug.setChecked(loaded_config["DEBUG"])
                self.ensure_correct_instance_retry.setText(str(loaded_config["ensure_correct_instance_retry"]))
                self.before_switch_esc_press_pause.setText(str(loaded_config["before_switch_esc_press_pause"]))
                self.set_up_key_press_pause.setText(str(loaded_config["set_up_key_press_pause"]))
        except (FileNotFoundError, KeyError, JSONDecodeError):
            print("Unable to load settings!")
        return

    def save_to_json(self):
        if os.path.isfile("config.json"):
            config_path = "config.json"
        else:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        new_config = {
          "lower_bound": int(self.lower_bound.text().strip()),
          "upper_bound": int(self.upper_bound.text().strip()),
          "pause_hotkey": self.pause_hotkey.text().strip(),
          "exit_hotkey": self.exit_hotkey.text().strip(),
          "parallel_world_gen": self.parallel_world_gen.isChecked(),
          "ensure_correct_instance_retry": float(self.ensure_correct_instance_retry.text().strip()),
          "before_switch_esc_press_pause": float(self.before_switch_esc_press_pause.text().strip()),
          "set_up_key_press_pause": float(self.set_up_key_press_pause.text().strip()),
          "DEBUG": self.debug.isChecked()
        }
        json_str = json.dumps(new_config)
        try:
            with open(config_path, "w") as file:
                file.write(json_str)
        except (FileNotFoundError, Exception):
            print("Unable to save settings!")
        print("Saving!!!")
        return

