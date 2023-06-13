from PyQt6.QtWidgets import QDialog, QRadioButton, QVBoxLayout, QDialogButtonBox
from PyQt6.QtCore import pyqtSignal

class CustomDialog(QDialog):
    normalization_method_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Выбор метода нормализации")

        self.radio_button_min_max_scaler = QRadioButton("Масштабирование (Min-Max Scaling)")
        self.radio_button_standard_scaler = QRadioButton("Стандартизация (Standardization)")        

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.radio_button_min_max_scaler)
        layout.addWidget(self.radio_button_standard_scaler)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def accept(self):
        if self.radio_button_min_max_scaler.isChecked():
            self.normalization_method_selected.emit("Масштабирование")
        elif self.radio_button_standard_scaler.isChecked():
            self.normalization_method_selected.emit("Стандартизация")
        super().accept()