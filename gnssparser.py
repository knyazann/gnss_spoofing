import struct

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
