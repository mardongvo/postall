# -*- coding: utf-8 -*-

import base64

def to_base64(str):
	return base64.b64encode(str.encode()).decode("utf-8")

DB_CONNECTION="host=127.0.0.1 port=5432 dbname=postall user=... password=..." #database path/auth
PROXY_URL="..." #http proxy, set None for no-proxy
#see https://otpravka.pochta.ru/specification#/authorization-token
ACCESS_TOKEN	= "....."
LOGIN_PASSWORD	= to_base64("login:pass")
POST_SERVER = "https://otpravka-api.pochta.ru"

#нижеследующие словари определяют структуру таблиц БД
#учитывайте это при изменении класса DBStorage

#https://otpravka.pochta.ru/specification#/orders-creating_order
#также определяет структуру для БД
LETTER_DEFAULT = {
    #"area-to": "", #Район (Опционально)
    #"building-to": "", #Часть здания: Строение (Опционально)
    "comment": "", #Комментарий:Номер заказа. Внешний идентификатор заказа, который формируется отправителем(Опционально)
    #"corpus-to": "", #Часть здания: Корпус (Опционально)
    #"courier": False, #Отметка 'Курьер'  true или false (Опционально)
    #"dimension": { #Линейные размеры (Опционально)
    #  "height": 0,
    #  "length": 0,
    #  "width": 0
    #},
    #"given-name": "", #Имя получателя
    #"hotel-to": "", #Название гостиницы (Опционально)
    "house-to": "", #Часть адреса: Номер здания
    "index-to": 0, #Почтовый индекс Целое число
    #"insr-value": 0, #Сумма объявленной ценности (копейки),  (Опционально)
    #"letter-to": "string", #Часть здания: Литера (Опционально)
    #"location-to": "string", #Микрорайон (Опционально)
    "mass": 0, #Вес РПО (в граммах)
    #"middle-name": "string", #Отчество получателя (Опционально)
    #"num-address-type-to": "string", #Номер для а/я, войсковая часть, войсковая часть ЮЯ, полевая почта (Опционально)
    "order-num": "", #Номер заказа. Внешний идентификатор заказа, который формируется отправителем, 
    #"payment": 0, #Сумма наложенного платежа (копейки)  (Опционально)
    "place-to": "", #Населенный пункт
    "recipient-name": "", #Наименование получателя одной строкой (ФИО, наименование организации)
    "region-to": "", #Область, регион
    "room-to": "", #Часть здания: Номер помещения (Опционально)
    #"slash-to": "string", #Часть здания: Дробь (Опционально)
    #"sms-notice-recipient": 0, #Признак услуги SMS уведомления (Опционально)
    "street-to": "", #Часть адреса: Улица
    #"surname": "", #Фамилия получателя
    #"tel-address": 0, #Телефон получателя (может быть обязательным для некоторых типов отправлений) (Опционально)
    #"with-order-of-notice": true, #Отметка 'С заказным уведомлением' true или false (Опционально)
    "with-simple-notice": True, #Отметка 'С простым уведомлением' (Опционально)
    #"wo-mail-rank": true #Отметка 'Без разряда' (Опционально)
}

#эти поля преполагаются постоянными и их хранение в базе не предполагется
#можно переместить в струкруту выше
LETTER_CONSTANT_FIELDS = {
    "address-type-to": "DEFAULT", #Тип адреса DEFAULT, PO_BOX, DEMAND
    "envelope-type": "DL", #Тип конверта - ГОСТ Р 51506-99. (Опционально), https://otpravka.pochta.ru/specification#/enums-base-envelope-type
    "fragile": False, #Установлена ли отметка 'Осторожно/Хрупкое'?,  true или false
    "mail-direct": 643, #Код страны Россия: 643
    "mail-type": "LETTER", #Вид РПО. https://otpravka.pochta.ru/specification#/enums-base-mail-type
    "manual-address-input": True, #Отметка 'Ручной ввод адреса'  true или false
    "payment-method": "STAMP", #Способ оплаты  (Опционально) CASHLESS,  STAMP, FRANKING https://otpravka.pochta.ru/specification#/enums-payment-methods
    "postoffice-code": "", #Индекс места приема (Опционально)
    "mail-category": "ORDERED", #Категория РПО: SIMPLE, ORDERED, ORDINARY, WITH_DECLARED_VALUE, WITH_DECLARED_VALUE_AND_CASH_ON_DELIVERY, COMBINED, https://otpravka.pochta.ru/specification#/enums-base-mail-category
}

#дополнительные поля для БД
LETTER_DB_FIELDS = {
	"db_letter_id": "sequence", #=integer autoincrement, serial
	"db_reestr_id": 0,#
	"id":0, #идентификатор с сайта
	"barcode":"", #ШПИ
	"db_mass_pages": 0, #количество страниц, используется для вычисления массы
	"db_user_id": "", #идентификатор пользователя
	"db_locked": 0, #заблокировано для изменений, возможно только присвоение barcode или разблокировка при удалении с 
	"db_last_error": "", #последняя ошибка
}

#поля для реестра
REESTR_DB_FIELDS = {
	"db_reestr_id": "sequence", #=integer autoincrement, serial
	"db_create_date": "date", #
	"list-number-date": "date", #aka sending-date (Опционально) Дата сдачи в почтовое отделение (yyyy-MM-dd)
	"batch-name": "", #Номер партии
    "with-simple-notice": False, #Отметка 'С простым уведомлением' (Опционально)
	"db_user_id": "", #идентификатор пользователя
	"db_locked": 0, #заблокировано для изменений
	"db_comment":"", #комментарий
	"db_letter_count": 0 #количество писем TODO: оставить или заменить динамикой?
}

LETTER_KEY_FIELD = "db_letter_id"
REESTR_KEY_FIELD = "db_reestr_id"

#контрагенты - основа
#дополнительно добавляются поля из LETTER_DEFAULTS, заканчивающиеся на -to
CONTRAGENT_DB_FIELDS = {
	"srctype": 0, #тип источника
	"srcid": "", #идентификатор в источнике
	"recipient-name": "",  # Наименование получателя одной строкой (ФИО, наименование организации)
}

#пользователи
USER_DB_FIELDS = {
	"db_user_id": "",
	"fio": "",
	"admin": 0,
}

#информация о своей организации, используется при печати конвертов
FROM_INFO = {
	"name":"", #наименование своей организации
	"addr": "",  # адрес своей организации
	"index": "",  # индекс адреса своей организации
	"fio": "",  # ФИО ответственного
}