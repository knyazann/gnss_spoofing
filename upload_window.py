from PyQt6.QtWidgets import QMainWindow,QWidget,QLabel,QLineEdit,QVBoxLayout,QFileDialog,QPushButton,QFileDialog,QMessageBox
from database_settings import packet_collection, channel_collection
from datetime import datetime
import gnssparser as gp

class UploadWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Загрузка пакета")
        self.setGeometry(100, 100, 300, 50)

        # Создание центрального виджета для нового окна
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Создание меток и полей для ввода названия сигнала и выбора файла
        title_label = QLabel("Введите название пакета:")
        self.packet_title_edit = QLineEdit()
        self.file_label = QLabel("Файл не выбран")

        # Создание кнопки выбора файла
        file_btn = QPushButton("Выбрать файл", self)
        file_btn.clicked.connect(self.choose_file)

        # Создание кнопки загрузки сигнала
        upload_btn = QPushButton("Загрузить пакет", self)
        upload_btn.clicked.connect(self.upload_file)

         # Создание вертикального лэйаута и добавление в него метки, поля и кнопки
        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addWidget(self.packet_title_edit)
        layout.addWidget(self.file_label)
        layout.addWidget(file_btn)
        layout.addWidget(upload_btn)

        # Установка лэйаута в центральный виджет
        central_widget.setLayout(layout)

    # Обработчик события для кнопки выбора файла
    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open file', '.', 'rez-files (*.rez)')
        self.file_path = file_path
        if file_path:
            self.file_label.setText(f"Выбранный файл: {file_path}")

    # Обработчик события для кнопки загрузки сигнала
    def upload_file(self):
        filename = self.file_path
        print('Выбранный файл:', filename) # Загрузка файла

        identifier = 0x39
        with open(filename, 'rb') as file:
            file_content = file.read()

        packets = gp.find_packets(file_content, identifier)


        ## Это всё для packets[0]!!!!!!
        time_nav, shift, size, channels_info = gp.get_data_from_packet(packets[0])
        gp.print_hex_packet(packets[0])
        print('time_nav', time_nav)
        print('size', bin(size)),
        print('channels_info', channels_info)

        packet_title = self.packet_title_edit.text()
        packet_data = {
                    'title': packet_title,
                    'file_path': filename,
                    'date': datetime.now(),
                    'time_nav': time_nav,
                    'size': size
                }

        # добавляем запись signal_data в коллекцию signals
        ins_signal_data = packet_collection.insert_one(packet_data)

        channels_measurements = gp.channel_split(channels_info, size)
        for channel in range(0, size):
            channel_measurements = channels_measurements[channel]
            frequency_range,satellite_number,signal_type_num,gnss_number,channel_num,snr,pr,pv = gp.get_measurements(channel_measurements)
            signal_name = packet_title + '_' + str(channel_num)
            print('freq',frequency_range)
            print('satellite_number',satellite_number)
            print('signal_type',signal_type_num)
            print('navigation_system',gp.gnss_dict[gnss_number])
            print('channel_number',channel_num)
            print('snr',snr)
            print('pr',pr)
            do = gp.calculate_doppler_shift(pv)
            print('do',do)

            if frequency_range == 0:
                signal_type = gp.glonass_signal_0_dict[signal_type_num]

            parameters = {
                    'signal_name': signal_name,
                    'frequency_range': frequency_range,
                    'satellite_number': satellite_number,
                    'signal_type': signal_type,
                    'navigation_system': gp.gnss_dict[gnss_number],
                    'channel_number': channel_num,
                    'snr': snr,
                    'pseudo_range': pr,
                    'doppler_shift': do,
                    'data': channels_measurements[channel],
                    'signal': { "$db": "signal_db", "$ref" : "signals", "$id" : ins_signal_data.inserted_id}
                    }

            # добавляем параметры в коллекцию parameters
            ins_parameters = channel_collection.insert_one(parameters)
        


        self.close() 
