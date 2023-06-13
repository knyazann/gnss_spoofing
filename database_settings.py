import pymongo

# устанавливаем соединение с MongoDB, 27017 - стандартный порт
db_client = pymongo.MongoClient("mongodb://localhost:27017/")  # или так MongoClient('localhost', 27017)

# подключаемся к БД signals_db, если её нет, то будет создана
current_db = db_client["gnss_spoofing_db"] 

# получаем колекции из нашей БД, если их нет, то будут созданы
## коллекция - это группа документов, которая хранится в БД MongoDB (эквалент таблицы в ркляционных базах)
packet_collection = current_db["packets"]
channel_collection = current_db["channels"]
normalization_collection = current_db["normalization"]