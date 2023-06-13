from PyQt6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QLabel,QLineEdit,QPushButton,QTextEdit
from database_settings import packet_collection

# Словарь с сопоставлением фактических полей и желаемых названий
field_mapping = {
    "title": "Название сигнала",
    "file_path": "Расположение файла",
    "date": "Дата загрузки"
}

# Список полей, которые не нужно выводить
excluded_fields = ["_id","timestamps", "values"]

class SearchWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Поиск сигнала")
        self.setGeometry(100, 100, 350, 170)

        # Создание центрального виджета для нового окна
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # Создание элементов интерфейса окна поиска
        self.search_label = QLabel("Введите название сигнала:")
        self.search_input = QLineEdit()
        self.search_button = QPushButton("найти")
        self.search_button.clicked.connect(self.search_signal)
        self.result_text_edit = QTextEdit()

        # Создание компоновщика для размещения элементов интерфейса
        layout = QVBoxLayout()
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_button)
        layout.addWidget(self.result_text_edit)

        # Установка лэйаута в центральный виджет
        central_widget.setLayout(layout)

    
    def search_signal(self):
        search_title = self.search_input.text()
        
        # Поиск записи в MongoDB
        find_record = packet_collection.find_one({"title": search_title})
        
        if find_record:
            result_str = ""
            for key, value in find_record.items():
                if key not in excluded_fields:
                    if key == 'date':
                        # Форматирование даты в строку в формате "дд.мм.гггг чч:мм"
                        formatted_date = value.strftime("%d.%m.%Y %H:%M")
                        result_str += f"<b> {field_mapping[key]}:</b>  {formatted_date} <br>"
                    else:
                        result_str += f"<b> {field_mapping[key]}:</b> {value} <br>"
                
            self.result_text_edit.setHtml(result_str)
           
        else:
            self.result_text_edit.setPlainText("Запись не найдена.")
