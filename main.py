from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

## Приложение не доберётся сюда, пока вы не выйдете и цикл событий не остановится
