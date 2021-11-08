# -*- coding: utf-8 -*-

import configuration as defconf
import logging
from dbstorage import LOCK_STATE_FINAL, LOCK_STATE_FREE, LOCK_STATE_BACKLOG, LOCK_STATE_BATCH
from user_identifier import UserIdentifier
from copy import deepcopy

"""
Схема обработки письма в функции barcode_add

                        +----------------------------+
                        |       STATE_START          |
                        | вычисляем состояние письма |   +---+
                        +-------------+--------------+--->ERR|
                                      |                  +---+
     +--------------------------------+---------------------------------+
     |                                |                                 |
+----v----+                     +-----v---------+           +-----------v-----------+
| STATE_0 |                     | STATE_1       |           | STATE_FF              |
| новое   |                     | уже добавлено |           | действий не требуется |
+----+----+                     +-----+---------+           +-----------+-----------+
     |                                |                                 |
+----v--------+                 +-----v---------------+                 |
| STATE_ADD   <-----------------+ STATE_CHECK         |                 |
| добавляем в |                 | проверить состояние |                 |
| кабинет     |   +---+         | письма в кабинете   |   +---+         |
+----+--------+--->ERR|         +-----+------------+--+--->ERR|         |
     |            +---+               |            |      +---+         |
     |                                |            |                    |
     |                                |            |                    |
+----v--------------+                 |            |     +--------------+
| STATE_CHECK_BATCH <-----------------+            |     |
| есть ли пакет     |   +---+                      |     |
++--+---------------+--->ERR|                      |     |        x
 |  |                   +---+                      |     |        xx----+
 |  |                                              |     |        x     |
 |  | +--------------------+                       |     |              |
 |  | | STATE_CREATE_BATCH +----------+            |     |       +------v-------------+
 |  +-> создать пакет      |   +---+  |            |     |       | ERR                |
 |    +--------------------+--->ERR|  |            |     |       |                    |
 |                             +---+  |            |     |   +---+ ERROR_PC           |
 |    +--------------------+          |            |     |   |   | ошибка при работе  |
 |    | STATE_ADD_TO_BATCH +----------+            |     |   |   | с кабинетом        |
 +----> добавить в пакет   |   +---+  |            |     |   |   |                    |
      +--------------------+--->ERR|  |            |     |   |   | ERROR_DB           |
                               +---+  |            |     |   |   | ошибка при работе  |
                                      |            |     |   |   | с БД               |
               +----------------------+            |     |   |   +-------+------------+
               |                                   |     |   |           |
      +--------v---------------------+             |     |   |           |
      | STATE_GET_INFO               |             |     |   |           |
      | получаем информацию о письме |   +---+     |     |   |           |
      +--------+---------------------+--->ERR|     |     |   |           |
               |                         +---+     |     |   |           |
               |                                   |     |   |           |
      +--------v------------+                      |     |   |           |
      | STATE_SAVE          <----------------------<---------+           |
      | сохраняем письмо    |   +---+                    |               |
      +--------+------------+--->ERR|                    |               |
               |                +---+                    |               |
               |                                         |               |
      +--------v------------+                            |               |
      |     STATE_END       <----------------------------+---------------+
      +---------------------+
"""

STATE_START = 1
STATE_0 = 2
STATE_1 = 3
STATE_FF = 4
STATE_ADD = 5
STATE_CHECK = 6
STATE_CHECK_BATCH = 7
STATE_CREATE_BATCH = 8
STATE_ADD_TO_BATCH = 9
STATE_GET_INFO = 10
STATE_SAVE = 11
STATE_END = 12
ERROR_PC = 100 + 0
ERROR_DB = 100 + 1
_ERR_404 = "HTTP code: 404"


def get_deep_value(reply, default_value, *keys):
    # get value from deep dictionary
    sub = reply
    for key in keys:
        if not isinstance(sub, dict):
            return default_value
        if key not in sub:
            return default_value
        sub = sub[key]
    return sub


def fill_letter_from_reply(letter, reply):
    letter["barcode"] = get_deep_value(reply, "", "barcode")
    letter["opm_index_oper"] = get_deep_value(reply, "", "online-payment-mark", "index-oper")
    letter["opm_id"] = get_deep_value(reply, "", "online-payment-mark", "online-payment-mark-id")
    letter["opm_value"] = get_deep_value(reply, 0, "online-payment-mark", "value")
    letter["total_rate_wo_vat"] = get_deep_value(reply, 0, "total-rate-wo-vat")
    letter["total_vat"] = get_deep_value(reply, 0, "total-vat")


def barcode_add(dbstorage, postconn, reestr_info, letter_info):
    """ Добавление письма в кабинете сначала в новые, а потом в пакет
    
    :param dbstorage: объект DBStorage
    :param postconn: объект PostConnector
    :param reestr_info: dict(), информация о реестре
    :param letter_info: dict(), информация о письме
    :return:
    """
    log = logging.getLogger("postall")
    _state = STATE_START
    _error = ""
    _reestr = deepcopy(reestr_info)
    _letter = deepcopy(letter_info)
    while True:
        ########################
        if _state == STATE_START:
            _reestr, err = dbstorage.get_reestr_info(_reestr["db_reestr_id"])
            if err > "":
                _error = "barcode_add:(STATE_START):get_reestr_info>>" + err
                _state = ERROR_DB
                continue
            # если реестр заблокирован, ничего не делаем
            if (_reestr["db_locked"] == LOCK_STATE_FINAL) or \
                    (_letter["db_locked"] == LOCK_STATE_FINAL) or \
                    (_letter["db_locked"] == LOCK_STATE_BATCH):
                _state = STATE_FF
                continue
            if _letter["db_locked"] == LOCK_STATE_BACKLOG:
                _state = STATE_1
                continue
            if _letter["db_locked"] == LOCK_STATE_FREE:
                _state = STATE_0
                continue
        ########################
        if _state == STATE_0:
            # копируем постоянные поля
            for k, v in defconf.LETTER_CONSTANT_FIELDS.iteritems():
                _letter[k] = v
            # !!!
            # комментарий к отправлению должен быть - <ФИО>, <комментарий из письма>
            uinf, err = dbstorage.get_user_info(_letter["db_user_id"])
            if err > "":
                _error = "barcode_add:(STATE_0):get_user_info>>" + err
                _state = ERROR_DB
                continue
            _letter["order-num"] = UserIdentifier(uinf).get_fio() + u", " + _letter["comment"]
            _state = STATE_ADD
            continue
        ########################
        if _state == STATE_1:
            _state = STATE_CHECK
            continue
        ########################
        if _state == STATE_FF:
            _state = STATE_END
            continue
        ########################
        if _state == STATE_ADD:
            idd, err = postconn.add_backlog(_letter)
            if (err > "") or (idd == 0):
                _error = "barcode_add:(STATE_ADD):add_backlog>>" + err
                _state = ERROR_PC
                continue
            _letter["id"] = idd
            _letter["db_locked"] = LOCK_STATE_BACKLOG
            res, err = dbstorage.modify_letter(_letter)
            if err > "":
                _error = "barcode_add:(STATE_ADD):modify_letter>>" + err
                _state = ERROR_DB
                continue
            _state = STATE_CHECK_BATCH
            continue
        ########################
        if _state == STATE_CHECK:
            o0, err0 = postconn.get_backlog(_letter["id"], 0)
            o1, err1 = postconn.get_backlog(_letter["id"], 1)
            # письмо нигде не найдено
            if (err0 == _ERR_404) and (err1 == _ERR_404):
                _letter["id"] = 0
                _letter["db_locked"] = LOCK_STATE_FREE
                _state = STATE_ADD
                continue
            # письмо найдено в новых
            if (err0 == "") and (err1 == _ERR_404):
                _state = STATE_CHECK_BATCH
                continue
            # письмо найдено в пакете
            if (err0 == _ERR_404) and (err1 == ""):
                fill_letter_from_reply(_letter, o1)
                _letter["db_locked"] = LOCK_STATE_BATCH
                _state = STATE_SAVE
                continue
            _error = "barcode_add:(STATE_CHECK)>>" + err0 + "," + err1
            _state = ERROR_PC
            continue
        ########################
        if _state == STATE_CHECK_BATCH:
            if _reestr["batch-name"] == "":
                _state = STATE_CREATE_BATCH
                continue
            else:
                _state = STATE_ADD_TO_BATCH
                continue
        ########################
        if _state == STATE_CREATE_BATCH:
            batch_info, err = postconn.add_batch(_reestr["list-number-date"],
                                                 _letter["payment-method"] == "ONLINE_PAYMENT_MARK",
                                                 [_letter["id"]])
            if err > "":
                _error = "barcode_add:(STATE_CREATE_BATCH):add_batch>>" + err
                _state = ERROR_PC
                continue
            # если добавление пакета прошло успешно
            _reestr["batch-name"] = batch_info["batch-name"]
            res, err = dbstorage.modify_reestr(_reestr)
            if err > "":
                _error = "barcode_add:(STATE_CREATE_BATCH):modify_reestr>>" + err
                _state = ERROR_DB
                continue
            _state = STATE_GET_INFO
            continue
        ########################
        if _state == STATE_ADD_TO_BATCH:
            err = postconn.add_backlog_to_batch(_reestr["batch-name"], _letter["id"])
            if err > "":
                _error = "barcode_add:(STATE_ADD_TO_BATCH):add_backlog_to_batch>>" + err
                _state = ERROR_PC
                continue
            _state = STATE_GET_INFO
            continue
        ########################
        if _state == STATE_GET_INFO:
            inf, err = postconn.get_backlog(_letter["id"], 1)
            if err > "":
                _error = "barcode_add:(STATE_GET_INFO):get_backlog>>" + err
                _state = ERROR_PC
                continue
            fill_letter_from_reply(_letter, inf)
            _letter["db_locked"] = LOCK_STATE_BATCH
            _state = STATE_SAVE
            continue
        ########################
        if _state == STATE_SAVE:
            _letter["db_last_error"] = _error
            res, err = dbstorage.modify_letter(_letter)
            if err > "":
                _error = "barcode_add:(STATE_SAVE):modify_letter>>" + err
                _state = ERROR_DB
                continue
            _state = STATE_END
            continue
        ########################
        if _state == ERROR_PC:
            _letter["db_last_error"] = _error
            _state = STATE_SAVE
            continue
        ########################
        if _state == ERROR_DB:
            log.error(_error)
            _state = STATE_END
            continue
        ########################
        if _state == STATE_END:
            break


def barcode_del(dbstorage, postconn, reestr_info, letter_info):
    """ Удаление письма с сайта
    
    :param dbstorage: объект DBStorage
    :param postconn: объект PostConnector
    :param reestr_info: dict(), информация о реестре
    :param letter_info: dict(), информация о письме
    :return:
    """
    log = logging.getLogger("postall")
    _error = ""
    _reestr = deepcopy(reestr_info)
    _letter = deepcopy(letter_info)
    _reestr, err = dbstorage.get_reestr_info(reestr_info["db_reestr_id"])
    if err > "":
        log.error("barcode_del:():get_reestr_info>>" + err)
        return
    if _letter["db_locked"] == LOCK_STATE_FINAL:
        return
    if _reestr["db_locked"] == LOCK_STATE_FINAL:
        return
    linf = {"db_letter_id": _letter["db_letter_id"],
            "db_locked": _letter["db_locked"],
            "id": _letter["id"],
            "db_last_error": "",
            "barcode": "",
            "db_reestr_id": _letter["db_reestr_id"]}
    del_result = [i[1] for i in postconn.remove_backlogs([_letter["id"]])] + \
                 [i[1] for i in postconn.remove_backlogs_from_shipment([_letter["id"]])]
    if len(del_result) != 2:
        log.error("barcode_del:():len(del_result) != 2")
    # письма нет на сайте
    if (del_result[0] == _ERR_404) and (del_result[1] == _ERR_404):
        linf["id"] = 0
        linf["db_locked"] = LOCK_STATE_FREE
    # письмо удалено
    elif (del_result[0] == "") or (del_result[1] == ""):
        linf["id"] = 0
        linf["db_locked"] = LOCK_STATE_FREE
    # ошибка при удалении
    else:
        linf["db_last_error"] = \
            (del_result[0] if (del_result[0] != "") and
                              (del_result[0] != _ERR_404) else "") + \
            (del_result[1] if (del_result[1] != "") and
                              (del_result[1] != _ERR_404) else "")
    res, err = dbstorage.modify_letter(linf)
    if err > "":
        log.error("barcode_del:():modify_letter>>" + err)


def set_date(dbstorage, postconn, reestr_info, batch_date):
    """ Установить дату реестра. Если реестр уже есть на сайте, то и на сайте
    
    :param reestr_info: dict(), информация о реестре
    :param batch_date: дата в виде datetime/date
    :return:
    """
    reestr_info["list-number-date"] = batch_date
    if reestr_info["db_locked"] == LOCK_STATE_BATCH:  # если реестр выгружен
        err = postconn.modify_batch(reestr_info["batch-name"], reestr_info["list-number-date"])
        if err > "":
            logging.error("Commands:set_date::modify_batch>>" + err)
        else:
            res, err = dbstorage.modify_reestr(reestr_info)
            if err > "":
                logging.error("Commands:set_date::modify_reestr>>" + err)
    if reestr_info["db_locked"] == LOCK_STATE_FREE:
        res, err = dbstorage.modify_reestr(reestr_info)
        if err > "":
            logging.error("Commands:set_date::modify_reestr>>" + err)


def barcode_add_all(dbstorage, postconn, reestr_info, user_ident):
    for data, err in dbstorage.get_letters_list(reestr_info["db_reestr_id"]):
        if err == "":
            if (reestr_info["db_locked"] == LOCK_STATE_FINAL) or \
                    (user_ident.get_user_id() != data["db_user_id"] and user_ident.is_admin() == 0):
                data["db_locked"] = LOCK_STATE_FINAL
            barcode_add(dbstorage, postconn, reestr_info, data)
        else:
            logging.error("Commands:barcode_add_all::get_letters_list>>" + err)


def barcode_del_all(dbstorage, postconn, reestr_info, user_ident):
    for data, err in dbstorage.get_letters_list(reestr_info["db_reestr_id"]):
        if err == "":
            if (reestr_info["db_locked"] == LOCK_STATE_FINAL) or \
                    (user_ident.get_user_id() != data["db_user_id"] and user_ident.is_admin() == 0):
                data["db_locked"] = LOCK_STATE_FINAL
            barcode_del(dbstorage, postconn, reestr_info, data)
        else:
            logging.error("Commands:barcode_add_all::get_letters_list>>" + err)
