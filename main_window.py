from PyQt6.QtWidgets import QMainWindow,QHBoxLayout,QVBoxLayout,QWidget
from PyQt6.QtWidgets import QTableWidget,QTableWidgetItem,QPushButton,QMessageBox
from PyQt6.QtGui import QAction
from upload_window import UploadWindow
from search_window import SearchWindow
from custom_dialog import CustomDialog
from database_settings import packet_collection, channel_collection, normalization_collection
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import numpy as np
import csv
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Сигналы ГНСС")
        self.setGeometry(100, 100, 600, 300)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Создание меню
        toolbar = self.addToolBar('Toolbar')

        # Создание действия "Новый сигнал"
        upload_action = QAction("Новый сигнал", self)
        upload_action.triggered.connect(self.open_upload_window)
        toolbar.addAction(upload_action)

        toolbar.addSeparator() # разделитель между кнопками

        # Создание действия "Просмотр данных"
        view_action = QAction("Просмотр данных", self)
        view_action.triggered.connect(self.view_data)
        toolbar.addAction(view_action)

        toolbar.addSeparator() # разделитель между кнопками

        # Создание действия "Поиск"
        search_action = QAction("Поиск", self)
        search_action.triggered.connect(self.open_search_window)
        toolbar.addAction(search_action)

        # Создание действия "Нормализованные данные" (ФАЙЛЫ cvs и путь их)
        normilized_action = QAction("Нормализованные данные", self)
        normilized_action.triggered.connect(self.view_normilized_data)
        toolbar.addAction(normilized_action)
        
        self.show()

    # Обработчик открытия окна для загрузки файла
    def open_upload_window(self):
        self.upload_window = UploadWindow()
        self.upload_window.show()

    # Обработчик открытия окна для поиска
    def open_search_window(self):
        self.search_window = SearchWindow()
        self.search_window.show()    

    def view_data(self):
 
        # создание таблицы
        central_widget = QWidget()
        self.table = QTableWidget(self)
        signal_count = 11
        self.table.setRowCount(signal_count)
        self.table.setColumnCount(8)
        headers = ['Название','Дата загрузки','ГНСС','№ спутника','Тип сигнала','SNR, дБ','Псевдодальность, м','Доплеровский сдвиг']
        self.table.setHorizontalHeaderLabels(headers)

        # создание кнопки нормализации
        self.search_btn = QPushButton("Нормализовать данные", self)
        self.search_btn.clicked.connect(self.normalization_method)

        # создание кнопки удаления
        self.delete_btn = QPushButton("Удалить запись", self)
        self.delete_btn.clicked.connect(self.delete_record)

        # заполнение таблицы значениями
        packets = list(packet_collection.find())       
        row = 0

        for packet in packets:

            formatted_date = packet['date'].strftime("%d.%m.%Y %H:%M")

            channels = list(channel_collection.find())
            for channel in channels:

                
                # складывается из названия пакета и номера канала   
                # channel_name = packet['title'] + '_' + str(channel['channel_number']) 
                channel_name = QTableWidgetItem(f"{packet['title']}_{channel['channel_number']}") 
                upload_date = QTableWidgetItem(f"{formatted_date}")    
                gnss_name = QTableWidgetItem(f"{channels[1]['navigation_system']}")
                satellite_number = QTableWidgetItem(f"{channel['satellite_number']}")
                signal_type = QTableWidgetItem(f"{channel['signal_type']}")
                signal_snr = QTableWidgetItem(f"{round(channel['snr'],2)}")
                signal_pr = QTableWidgetItem(f"{channel['pseudo_range']}")
                signal_do = QTableWidgetItem(f"{channel['doppler_shift']}")

                self.table.setItem(row, 0, channel_name)
                self.table.setItem(row, 1, upload_date)
                self.table.setItem(row, 2, gnss_name)
                self.table.setItem(row, 3, satellite_number)
                self.table.setItem(row, 4, signal_type)
                self.table.setItem(row, 5, signal_snr)
                self.table.setItem(row, 6, signal_pr)
                self.table.setItem(row, 7, signal_do)

                row += 1

            
        
        # Возможность выбрать несколько строк таблицы с помощью Ctrl 
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)

        # Установка ширины столбцов по содержимому
        self.table.resizeColumnsToContents()

        # Компоновка
        layout = QHBoxLayout(central_widget)
        layout.addWidget(self.table)
        layout_btn = QVBoxLayout()
        layout_btn.addWidget(self.search_btn)
        layout_btn.addWidget(self.delete_btn)
        layout.addLayout(layout_btn)
        
        self.setCentralWidget(central_widget)      
        

        # Присоединение выбора элемента таблицы к функции получения данных
        self.table.itemSelectionChanged.connect(self.get_title)

        self.table.show()

    # Функция получения сигнала при клике в таблице
    def get_title(self):

        selected_items = self.table.selectedItems()
        if selected_items:
            # Получаем номер строки выбранной ячейки
            row = selected_items[0].row()
            # Получаем название сигнала
            self.selected_title = self.table.item(row, 0).text()
            self.selected_channel = channel_collection.find_one({"signal_name": self.selected_title})

    
    def delete_record(self):

        # Создаем диалоговое окно с уведомлением об удалении
        msg_box = QMessageBox()
        msg_box.setText(f"Вы действительно хотите удалить {self.selected_title} ?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        result = msg_box.exec()

        # Обрабатываем результат диалога
        if result == QMessageBox.StandardButton.Ok:
            # Выполняем удаление записи
            channel_collection.delete_one({"signal_name": self.selected_title})
        else:
            # Отменяем удаление
            msg_box.close()

    def normalization_method(self):

        self.dialog = CustomDialog()
        self.dialog.normalization_method_selected.connect(self.normalize_data)
        self.dialog.exec()

    def normalize_data(self, method):

        records = channel_collection.find({}, {"signal_name":1, "satellite_number":1, "snr": 1, "pseudo_range": 1, "doppler_shift": 1})

        if method == "Масштабирование":
            scaler = MinMaxScaler()
        elif method == "Стандартизация":
            scaler = StandardScaler() 
        else:
            QMessageBox.critical(None, "Ошибка", "Не выбран метод нормализации.")
              

        # Извлечение данных и нормализация
        snr_values = []
        pr_values = []
        do_values = []
        
        for record in records:
            snr_values.append(record["snr"])
            pr_values.append(record["pseudo_range"])
            do_values.append(record["doppler_shift"])
        
        snr_values_array = np.array(snr_values)
        pr_values_array = np.array(pr_values)
        do_values_array = np.array(do_values)

        records_copy = channel_collection.find({}, {"signal_name":1, "satellite_number":1, "snr": 1, "pseudo_range": 1, "doppler_shift": 1})

        normalized_snr = scaler.fit_transform(snr_values_array.reshape(-1, 1))
        normalized_pr = scaler.fit_transform(pr_values_array.reshape(-1, 1))
        normalized_do = scaler.fit_transform(do_values_array.reshape(-1, 1))

        print('данные нормализовались')

        # Создание записей с нормализованными значениями
        for i, record in enumerate(records_copy):
          
            normalized_record = {
                
                "signal_name": record["signal_name"],
                "satellite_number": record["satellite_number"],
                "snr": normalized_snr[i][0],
                "pr": normalized_pr[i][0],
                "do": normalized_do[i][0],
                "signal": { "$db": "gnss_spoofing_db", "$ref" : "packets", "$id" : record["_id"]}
            }
          
            # Сохранение нормализованной записи в новой коллекции
            normalization_collection.insert_one(normalized_record)
        
        # Получение всех документов из коллекции normalization_collection
        documents = normalization_collection.find()

        # Открытие файла CSV для записи
        with open("output.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Запись заголовков столбцов
            writer.writerow(["signal", "satellite №", "SNR", "pseudo_range", "doppler_shift"])

            # Запись данных из документов в CSV
            for document in documents:
                signal_name = document["signal_name"]
                satellite_number = document["satellite_number"]
                snr = document["snr"]
                pr = document["pr"]
                do = document["do"]

                writer.writerow([signal_name, satellite_number, snr, pr, do])

        print("Данные успешно записаны в файл CSV.")

    def view_normilized_data(self):

        print('hi')

