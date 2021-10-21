from pymongo import MongoClient


"""
тестовый сбор производился на произвольных пользователях: grebenyukda, nedopekin, balandin
собрано 154 элемента, что соответствует информации на страницах профилей данных пользователей
замечена небольшая аномалия: время от времени instagram в списке выдает на одного подписчика меньше,
соответственно данные о подписчиках загружаются в соответствии с этим списком. Возможны дубли в
ответе сервера. В базу данных попадают только уникальные значения.
"""

client = MongoClient('localhost', 27017)
db = client.instagram

request = input('Enter username and type of request [followed, follows] using space: ').split()
type_of_request = True if request[1].lower() == 'followed' else False
collection = db[request[0]]

for idx, elem in enumerate(collection.find({'follow_flag': type_of_request}), 1):
    print(f'{idx})', elem.get('username'))
