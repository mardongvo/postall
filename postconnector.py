# -*- coding: utf-8 -*-

import requests
import json
import configuration as defconf
from datetime import datetime, date


def extract_errors(obj):
    """Извлечение информации об ошибках из ответа json
    
    :param obj: dict()
    :return: str
    """
    res = ""
    if ("errors" in obj) and len(obj["errors"]) > 0:
        for err in obj["errors"]:
            if "error-codes" in err:
                for ecod in err["error-codes"]:
                    res += "(%s) %s, %s; " % (
                        (ecod["code"] if "code" in ecod else ""),
                        (ecod["description"] if "description" in ecod else ""),
                        (ecod["details"] if "details" in ecod else "")
                    )
    return res


class PostConnector:
    """Класс реализации REST запросов на сервер почты
    
    При создании заказов/добавлении заказов в партию
    обратите внимание, что сущесвуют следующие ошибки:
    DIFFERENT_TRANSPORT_TYPE - Способы пересылки отправления и партии отличаются
    DIFFERENT_MAIL_TYPE - Типы почтовых отправлений не совпадают
    DIFFERENT_MAIL_CATEGORY - Категории почтовых отправления не совпадают
    DIFFERENT_MAIL_RANK - Разряд отправления и партии отличаются
    
    Не смешивайте разные типы и категории в одном реестре
    
    Каждому кабинету Почты России на API устанавливается лимит запросов в сутки.
    При превышении выдается ошибка 509
    """

    def __init__(self, connobj):
        """Инициализация
        connobj - объект requests.Session для обмена по http протоколу 
        """
        self.httpconn = connobj
        self.proxy = None
        self.access_token = ""
        self.login_password = ""
        # если не пуст, производится фильтрация letter_info при добавлении в кабинет
        self.letter_filter = set()

    def set_parameters(self, post_server=defconf.POST_SERVER, token=defconf.ACCESS_TOKEN,
                       login_password=defconf.LOGIN_PASSWORD, proxyurl=defconf.PROXY_URL, letter_filter=set()):
        """Установка параметров
        
        https://otpravka.pochta.ru/specification#/orders-creating_order
        token -- Токен авторизации приложения
        login_password -- Ключ авторизации пользователя
        proxyurl -- HTTP прокси в стандратной для requests нотации
        """
        self.proxy = {"http": proxyurl, "https": proxyurl} if proxyurl > "" else None
        self.access_token = token
        self.login_password = login_password
        self.post_server = post_server
        self.request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json;charset=UTF-8",
            "Authorization": "AccessToken " + self.access_token,
            "X-User-Authorization": "Basic " + self.login_password
        }
        self.letter_filter = letter_filter

    def add_backlog(self, letter_info):
        """Добавление заказа
        https://otpravka.pochta.ru/specification#/orders-creating_order
        letter_info - объект типа словарь
        """
        path = "/1.0/user/backlog"
        error = ""
        idd = 0
        _letter = {}
        for k in letter_info.keys():
            if (k in self.letter_filter) or (len(self.letter_filter) == 0):
                _letter[k] = letter_info[k]
        try:
            response = self.httpconn.put(self.post_server + path, headers=self.request_headers,
                                         data=json.dumps([_letter]), proxies=self.proxy)
            if response.status_code != requests.codes.OK:
                raise Exception("HTTP code: " + str(response.status_code))
            obj = json.loads(response.text)
            if ("result-ids" in obj) and len(obj["result-ids"]) > 0:
                idd = obj["result-ids"][0]
            error += extract_errors(obj)
        except Exception as e:
            error += str(e)
        return idd, error

    def get_backlog(self, backlog_id, source=1):
        """ Получение информации по заказу
        https://otpravka.pochta.ru/specification#/orders-search_order_byid
        https://otpravka.pochta.ru/specification#/batches-find_order_by_id
        backlog_id - идентификатор заказа
        :param source: 0 - /1.0/backlog/{id}, 1 - /1.0/shipment/{id},
        """
        error = ""
        obj = {}
        try:
            path = ""
            if source == 0:
                path = "/1.0/backlog/%d" % (backlog_id,)
            if source == 1:
                path = "/1.0/shipment/%d" % (backlog_id,)
            response = self.httpconn.get(self.post_server + path, headers=self.request_headers, proxies=self.proxy)
            if response.status_code != requests.codes.OK:
                raise Exception("HTTP code: " + str(response.status_code))
            obj = json.loads(response.text)
            error += extract_errors(obj)
        except Exception as e:
            error += str(e)
        return obj, error

    def add_backlogs(self, letter_info_array):
        """Добавление нескольких заказов. Итератор
        Предполагается, что в одном реестре может быть сколь угодно много писем,
        а сервера имеют неизвестное ограничение на количество байт в одном запросе,
        поэтому добавление идет по одному письму
        letter_info_array - массив словарей
        """
        for letter_info in letter_info_array:
            yield self.add_backlog(letter_info)

    def add_backlog_to_batch(self, batch_name, backlog_id):
        """Перенос заказов в партию
        batch_name -- номер партии
        backlog_id -- идентификатор заказа
        """
        path = "/1.0/batch/%s/shipment" % (batch_name,)
        error = ""
        try:
            response = self.httpconn.post(self.post_server + path, headers=self.request_headers,
                                          data=json.dumps([backlog_id]), proxies=self.proxy)
            if response.status_code != requests.codes.OK:
                raise Exception("HTTP code: " + str(response.status_code))
            obj = json.loads(response.text)
            error += extract_errors(obj)
        except Exception as e:
            error += str(e)
        return error

    def add_batch(self, send_date, use_online_balance, backlog_ids):
        """Создание партии из заказов
        send_date -- Дата сдачи в почтовое отделение, объект datetime (yyyy-MM-dd)
        use_online_balance -- boolean, Использование онлайн баланса (ЗОО)
        backlog_ids -- массив идентификаторов заказов
        """
        path = "/1.0/user/shipment?"
        if isinstance(send_date, datetime) or isinstance(send_date, date):
            path = path + "sending-date=" + send_date.strftime("%Y-%m-%d")
        if use_online_balance:
            path = path + "&use-online-balance=true"
        errors = {}
        batch_info = {}
        batch_name = None
        for bid in backlog_ids:
            errors[bid] = ""
        # 1 создание партии из одного заказа
        bid = backlog_ids[0]
        try:
            response = self.httpconn.post(self.post_server + path, headers=self.request_headers, data=json.dumps([bid]),
                                          proxies=self.proxy)
            if response.status_code != requests.codes.OK:
                raise Exception("HTTP code: " + str(response.status_code))
            obj = json.loads(response.text)
            if ("batches" in obj) and (len(obj["batches"]) > 0):
                batch_info = obj["batches"][0]
                if "batch-name" in batch_info:
                    batch_name = batch_info["batch-name"]
            errors[bid] += extract_errors(obj)
        except Exception as e:
            errors[bid] += str(e)
        # 2 добавление в существующую партию
        if batch_name is not None:
            if len(backlog_ids) > 1:
                for bid in backlog_ids[1:]:
                    errors[bid] = self.add_backlog_to_batch(batch_name, bid)
        else:
            errors[bid] += ("," if errors[bid] > "" else "") + u'Партия писем не создана'
        return (batch_info, errors)

    def modify_batch(self, batch_name, send_date):
        """Изменение дня отправки в почтовое отделение
        send_date -- Дата сдачи в почтовое отделение, объект datetime (yyyy-MM-dd)
        """
        error = ""
        try:
            path = "/1.0/batch/%s/sending/%d/%d/%d" % (batch_name, send_date.year, send_date.month, send_date.day)
            response = self.httpconn.post(self.post_server + path, headers=self.request_headers, proxies=self.proxy)
            if response.status_code != requests.codes.OK:
                raise Exception("HTTP code: " + str(response.status_code))
            obj = json.loads(response.text)
            error += extract_errors(obj)
        except Exception as e:
            error += str(e)
        return error

    def remove_backlogs_from_shipment(self, backlog_ids):
        """Удаление заказов из партии, итератор
        backlog_ids -- массив идентификаторов заказов
        """
        path = "/1.0/shipment"
        for bid in backlog_ids:
            error = ""
            try:
                response = self.httpconn.delete(self.post_server + path, headers=self.request_headers,
                                                data=json.dumps([bid]), proxies=self.proxy)
                if response.status_code != requests.codes.OK:
                    raise Exception("HTTP code: " + str(response.status_code))
                else:
                    obj = json.loads(response.text)
                    error += extract_errors(obj)
            except Exception as e:
                error += str(e)
            yield bid, error

    def remove_backlogs(self, backlog_ids):
        """Удаление новых заказов
        backlog_ids -- массив идентификаторов заказов
        """
        path = "/1.0/backlog"
        for bid in backlog_ids:
            error = ""
            try:
                response = self.httpconn.delete(self.post_server + path, headers=self.request_headers,
                                                data=json.dumps([bid]), proxies=self.proxy)
                if response.status_code != requests.codes.OK:
                    raise Exception("HTTP code: " + str(response.status_code))
                else:
                    obj = json.loads(response.text)
                    error += extract_errors(obj)
            except Exception as e:
                error += str(e)
            yield bid, error
