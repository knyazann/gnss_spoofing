import struct
import pymongo
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# устанавливаем соединение с MongoDB, 27017 - стандартный порт
db_client = pymongo.MongoClient("mongodb://localhost:27017/")  # или так MongoClient('localhost', 27017)

# подключаемся к БД signals_db, если её нет, то будет создана
current_db = db_client["signal_test_db"] 

# получаем колекции из нашей БД, если их нет, то будут созданы
## коллекция - это группа документов, которая хранится в БД MongoDB (эквалент таблицы в ркляционных базах)
collection_signals = current_db["signals"]
collection_parameters = current_db["parameters"]
normalization_collection = current_db["normalization"]

# Словарь с номерами навигационных систем
gnss_dict = {1: 'GPS', 2: 'ГЛОНАСС', 3: 'Galileo', 4: 'BeiDou', 5: 'SBAS'}
glonass_signal_0_dict = {0: 'сигнал СТ', 1: 'сигнал ВТ', 2: 'сигнал L1OCd', 3: 'сигнал L1OCp', 4: 'сигнал L1SCd', 5: 'сигнал L1SCp'}
glonass_signal_1_dict = {}
gps_signal_dict = {}
galileo_signal_dict = {}


def find_first_packet(data):
    packet_start = -1
    packet_end = -1

    for i in range(len(data) - 1):
        if data[i] == 0x10 and data[i+1] == 0x39:
            packet_start = i
            break
    
    if packet_start != -1:
        for i in range(packet_start + 1, len(data) - 1):
            if data[i] == 0x10 and data[i+1] == 0x03:
                packet_end = i
                break
    
    if packet_start != -1 and packet_end != -1:
        packet = data[packet_start:packet_end+2]
        return packet
    
    return None

def find_packets(file_content, identifier):
    flag = b'\x10'
    end_flag = b'\x10\x03'
    packets = []

    start_index = file_content.find(flag)
    while start_index != -1:
        identifier_index = start_index + len(flag)
        if file_content[identifier_index] == identifier:
            end_index = file_content.find(end_flag, identifier_index + 1)
            if end_index != -1:
                packet = file_content[start_index:end_index + 2]
                packets.append(packet)
            else:
                break
        start_index = file_content.find(flag, start_index + 1)

    return packets

def get_data_from_packet(packet):
    if packet[0] == 0x10 and packet[1] == 0x39 and packet[-1] == 0x03 and packet[-2] == 0x10:
        # Замена двух подряд идущих байт 0x10 на один байт 0x10
        modified_packet = packet.replace(b'\x10\x10', b'\x10')

        # Удаление двух начальных и четырех последних байт
        #processed_data = modified_data[2:-4]

        # Разделение пакета на переменные
        time_nav = struct.unpack("<d", modified_packet[2:10])[0] # распаковка бинарных данных из среза data[2:9] в формате <d, где <Q означает тип double
        shift = struct.unpack("<H", modified_packet[10:12])[0]
        size = struct.unpack("<H", modified_packet[12:14])[0]
        channels_info = modified_packet[14:-4]

        return time_nav, shift, size, channels_info
    else:
        return 'Неверный формат пакета'   

def channel_split(channels_info, channel_count):
    size_of_one_channel = int(len(channels_info) / channel_count)
    channels_measurements = []
    for i in range(0, len(channels_info), size_of_one_channel):
        channels_measurements.append(channels_info[i:i+size_of_one_channel])

    return channels_measurements

def get_measurements(channel):
    # Получение параметров спутника из первых двух байт
    satellite_bytes = int.from_bytes(channel[:2], byteorder='little')

    frequency_range = satellite_bytes & 0b00001111  # Биты 0-3
    satellite_number = (satellite_bytes >> 4) & 0b00111111 # Биты 4-9
    signal_type_num = (satellite_bytes >> 10) & 0b00000111  # Биты 10-12
    gnss_number = (satellite_bytes >> 13) & 0b00000111  # Биты 13-15

    channel_num = channel[2]
    liter_byte = channel[3]
    snr_byte = channel[4]
    snr = snr_byte * 0.2  # Расчет значения SNR в дБ

    Ready_S_byte = channel[5]
    sigma_S_byte = channel[6]
    sigma_V_byte = channel[7]
    sigma_Fi_byte = channel[8]
    rezerv_byte = channel[9]
    pr = int.from_bytes(channel[10:18], byteorder='little')
    pv = int.from_bytes(channel[18:26], byteorder='little')
    Fi_byte = int.from_bytes(channel[-8:], byteorder='little')

    return frequency_range,satellite_number,signal_type_num,gnss_number, channel_num,snr,pr,pv


def calculate_doppler_shift(pv):

    f = 1602.5625 * 10**6
    c = 299792458
    do = pv*(f/c)

    return do


def print_hex_packet(packet):
    hex_packet = ' '.join([f'{byte:02X}' for byte in packet])
    print(hex_packet)


filename = "imit.rez"
identifier = 0x39
with open(filename, 'rb') as file:
        file_content = file.read()

packets = find_packets(file_content, identifier)

for i in range(0, 1):

    ## Это всё для packets[0]!!!!!!
    time_nav, shift, size, channels_info = get_data_from_packet(packets[i])
    print_hex_packet(packets[i])
    print('time_nav', time_nav)
    print('size', bin(size)),
    print('channels_info', channels_info)

    signal_data = {
                'title': 'signal_title',
                'file_path': filename,
                'date': datetime.now(),
                'time_nav': time_nav,
                'size': size
            }

    # добавляем запись signal_data в коллекцию signals
    ins_signal_data = collection_signals.insert_one(signal_data)

    channels_measurements = channel_split(channels_info, size)
    for channel in range(0, size):
        channel_measurements = channels_measurements[channel]
        frequency_range,satellite_number,signal_type_num,gnss_number,channel_num,snr,pr,pv = get_measurements(channel_measurements)
        print('freq',frequency_range)
        print('satellite_number',satellite_number)
        print('signal_type',signal_type_num)
        print('navigation_system',gnss_dict[gnss_number])
        print('channel_number',channel_num)
        print('snr',snr)
        print('pr',pr)
        do = calculate_doppler_shift(pv)
        print('do',do)

        if frequency_range == 0:
            signal_type = glonass_signal_0_dict[signal_type_num]

        parameters = {
                'data': channels_measurements[channel],
                'frequency_range': frequency_range,
                'satellite_number': satellite_number,
                'signal_type': signal_type,
                'navigation_system': gnss_dict[gnss_number],
                'channel_number': channel_num,
                'snr': snr,
                'pseudo_range': pr,
                'doppler_shift': do,
                'signal': { "$db": "signal_db", "$ref" : "signals", "$id" : ins_signal_data.inserted_id}
                }

        # добавляем параметры в коллекцию parameters
        ins_parameters = collection_parameters.insert_one(parameters)


print(f"{packets[0]['title']}")

# Получение всех документов из коллекции
#documents = collection_parameters.find()

# Преобразование данных в список словарей
#data = [doc for doc in documents]
    
#df = pd.DataFrame(data)

# Сохранение DataFrame в CSV-файл
#df.to_csv('output.csv', index=False)





