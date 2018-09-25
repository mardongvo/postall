# -*- coding: utf-8 -*-
from pprint import pprint
from unittest import TestCase
from functools import partial

import sys
sys.path.append('..')
import logging
from commands import barcode_add, barcode_del, _ERR_404
from dbstorage import LOCK_STATE_FREE, LOCK_STATE_BATCH,\
    LOCK_STATE_BACKLOG, LOCK_STATE_FINAL
from copy import deepcopy
from datetime import date
import inspect

class MockDBPC:
    """ Класс-имитатор
    """
    def __init__(self):
        self.retvals = {} # возвращаемые значения для вызовов
        self.logs = [] # лог вызовов фуккций с параметрами
    def add_retval(self, funcname, callnum, retval):
        """
        
        :param funcname: имя имитируемой функции
        :param callnum:  номер вызова функции, 0 - для всех вызовов
        :param retval:  возвращаемое значение
        :return:
        """
        self.retvals[(funcname, callnum)] = retval
    def call_func(self, funcname, *args):
        counter = "callcount_"+funcname
        if counter not in self.__dict__:
            self.__dict__[counter] = 1
        else:
            self.__dict__[counter] += 1
        key1 = (funcname, self.__dict__[counter])
        key2 = (funcname, 0)
        self.logs.append((key1,deepcopy(args)))
        if key1 in self.retvals:
            return self.retvals[key1]
        if key2 in self.retvals:
            return self.retvals[key2]
        return None
    def __getattr__(self, item):
        return partial(self.call_func, item)

class TestMock(TestCase):
    """ Тест имитатора
    
    """
    def test1(self):
        m = MockDBPC()
        m.add_retval("method1",1,1)
        m.add_retval("method1",2,2)
        m.add_retval("method1",0,3)
        if m.method1() != 1:
            self.fail("method1, call 1 != 1")
        if m.method1() != 2:
            self.fail("method1, call 2 != 2")
        if m.method1() != 3:
            self.fail("method1, call 3(0) != 3")
        if m.method1() != 3:
            self.fail("method1, call 4(0) != 3")
        if m.method2("z") != None:
            self.fail("method2 (unknown), call result != None")

from logging.handlers import BufferingHandler

class TestCommands(TestCase):
    def test_barcode_del(self):
        for err1, err2, expect_state in [
            (_ERR_404, "", LOCK_STATE_FREE),
            ("", _ERR_404, LOCK_STATE_FREE),
            (_ERR_404, _ERR_404, LOCK_STATE_FREE),
            (_ERR_404, "Something", LOCK_STATE_BATCH),
            ("", "Something", LOCK_STATE_FREE),
            ("Something", "Something", LOCK_STATE_BATCH),
        ]:
            mocker = MockDBPC()
            reestr = {"db_reestr_id": 1, "db_locked": LOCK_STATE_BATCH}
            letter = {"db_letter_id": 1, "db_locked": LOCK_STATE_BATCH, "id": 10,
                      "db_reestr_id": 1}
            log = logging.getLogger("postall")
            hndl = BufferingHandler(10)
            log.addHandler(hndl)
            mocker.add_retval("get_reestr_info", 0, (reestr, ""))
            mocker.add_retval("remove_backlogs",1, [(10, err1)])
            mocker.add_retval("remove_backlogs_from_shipment",1, [(10, err2)])
            mocker.add_retval("modify_letter",1, (True, ""))
            barcode_del(mocker, mocker, reestr, letter)
            for func, args in mocker.logs:
                if func[0] == "modify_letter":
                    if args[0]["db_locked"] != expect_state:
                        self.fail(u"test_barcode_del: unexpected (%s, %s, %d) <> (%d)" %\
                                  (err1, err2, expect_state, args[0]["db_locked"]))
    def test_barcode_add(self):
        _DEFAULT_REESTR = {"db_reestr_id": 1, "db_locked": LOCK_STATE_FREE,
                        "batch-name":""}
        _DEFAULT_LETTER = {"db_letter_id": 1, "db_locked": LOCK_STATE_FREE,
                        "id": 0,
                        "db_reestr_id": 1, "db_user_id": 1, "comment":"c"}
        _DEFAULT_CALLS = [("get_reestr_info", 0,
                        (
                        {"db_reestr_id": 1, "db_locked": LOCK_STATE_FREE,
                         "batch-name":"", "list-number-date": date(2018,9,1)}, "")),
                       ("get_user_info", 0,
                        (
                            {"fio": "", "admin": False, "db_user_id": 1},
                            "")),
                       ("add_backlog", 0, (111, "")),
                       ("modify_letter", 0, (True, "")),
                       ("add_batch", 0, ({"batch-name":"10"}, "")),
                       ("modify_reestr", 0, (True, "")),
                       ("get_backlog", 0, ({"barcode": "123456789"}, "")),
                       ]
        TEST_DATA = [
            # BATCH (do nothing)
            # 1
            {"reestr":{"db_reestr_id": 1, "db_locked": LOCK_STATE_BATCH},
             "letter": {"db_letter_id": 1, "db_locked": LOCK_STATE_BATCH, "id": 10,
                  "db_reestr_id": 1},
             "calls": [("get_reestr_info", 0,
                        ({"db_reestr_id": 1, "db_locked": LOCK_STATE_BATCH}, ""))
                       ],
             "errlog_length": 0,
             "func_check": None,
             "log_check": None
             },
            # NORMAL
            # 2
            {"reestr": deepcopy(_DEFAULT_REESTR),
             "letter": deepcopy(_DEFAULT_LETTER),
             "calls": deepcopy(_DEFAULT_CALLS),
             "errlog_length": 0,
             "func_check":
                 lambda logs: True if logs[-1][0][0]=='modify_letter' and \
                                      logs[-1][1][0]["db_locked"]==LOCK_STATE_BATCH \
                 else False,
             "log_check": None
             },
            # NETWORK FAIL
            # 3
            {"reestr": deepcopy(_DEFAULT_REESTR),
             "letter": deepcopy(_DEFAULT_LETTER),
             "calls": deepcopy(_DEFAULT_CALLS)+[("add_backlog", 1, (0, "Net fail"))],
             "errlog_length": 0,
             "func_check":
                 lambda logs: True \
                    if logs[-1][0][0] == 'modify_letter' and \
                       logs[-1][1][0]["db_last_error"].find("add_backlog")>=0 and \
                       logs[-1][1][0]["db_locked"] == LOCK_STATE_FREE \
                     else False,
             "log_check": None
             },
            # 4
            {"reestr": deepcopy(_DEFAULT_REESTR),
             "letter": deepcopy(_DEFAULT_LETTER),
             "calls": deepcopy(_DEFAULT_CALLS) + [
                 ("add_batch", 1, ({}, "Net fail"))],
             "errlog_length": 0,
             "func_check":
                 lambda logs: True \
                     if logs[-1][0][0] == 'modify_letter' and \
                        logs[-1][1][0]["db_last_error"].find(
                            "add_batch") >= 0 and \
                        logs[-1][1][0]["db_locked"] == LOCK_STATE_BACKLOG \
                     else False,
             "log_check": None
             },
            # 5
            {"reestr": deepcopy(_DEFAULT_REESTR),
             "letter": deepcopy(_DEFAULT_LETTER),
             "calls": deepcopy(_DEFAULT_CALLS) + [
                 ("get_backlog", 1, ({}, "Net fail"))],
             "errlog_length": 0,
             "func_check":
                 lambda logs: True \
                     if logs[-1][0][0] == 'modify_letter' and \
                        logs[-1][1][0]["db_last_error"].find(
                            "get_backlog") >= 0 and \
                        logs[-1][1][0]["db_locked"] == LOCK_STATE_BACKLOG \
                     else False,
             "log_check": None
             },
            # DB FAIL
            # 6
            {"reestr": deepcopy(_DEFAULT_REESTR),
             "letter": deepcopy(_DEFAULT_LETTER),
             "calls": deepcopy(_DEFAULT_CALLS) + [
                 ("get_user_info", 1, (False, "DB fail"))],
             "errlog_length": 1,
             "func_check": None,
             "log_check":
                 lambda buffer: True \
                     if buffer[-1].msg.find("get_user_info") >= 0 \
                     else False
             },
            # 7
            {"reestr": deepcopy(_DEFAULT_REESTR),
             "letter": deepcopy(_DEFAULT_LETTER),
             "calls": deepcopy(_DEFAULT_CALLS) + [
                 ("modify_letter", 2, (False, "DB fail"))],
             "errlog_length": 1,
             "func_check":
                 lambda logs: True if logs[-1][0][0]=='modify_letter' and \
                                      logs[-1][1][0]["db_locked"]==LOCK_STATE_BATCH \
                 else False,
             "log_check":
                 lambda buffer: True \
                     if buffer[-1].msg.find("modify_letter") >= 0 \
                     else False
             },
            # 8 'network cable was cutted'
            {"reestr": deepcopy(_DEFAULT_REESTR),
             "letter": deepcopy(_DEFAULT_LETTER),
             "calls": deepcopy(_DEFAULT_CALLS) + [
                 ("get_backlog", 1, ({}, "Net fail")),
                 ("modify_letter", 2, (False, "DB fail"))],
             "errlog_length": 1,
             "func_check":
                 lambda logs: True if logs[-1][0][0] == 'modify_letter' and \
                                      logs[-1][1][0][
                                          "db_locked"] == LOCK_STATE_BACKLOG \
                     else False,
             "log_check":
                 lambda buffer: True \
                     if buffer[-1].msg.find("modify_letter") >= 0 \
                     else False
             },

        ]
        test_number = 0
        fail_count = 0
        for td in TEST_DATA:
            test_number += 1
            mocker = MockDBPC()
            reestr = td["reestr"]
            letter = td["letter"]
            log = logging.getLogger("postall")
            hndl = BufferingHandler(10)
            log.addHandler(hndl)
            for func_name, ncall, result in td["calls"]:
                mocker.add_retval(func_name, ncall, result)
            barcode_add(mocker, mocker, reestr, letter)
            if len(hndl.buffer) != td["errlog_length"]:
                fail_count += 1
                print("---------------test_number=%d---------------" % (test_number,))
                print(u"test_barcode_add: unexpected errlog length (%d <> %d)" % \
                          (len(hndl.buffer), td["errlog_length"]))
                for i in hndl.buffer:
                    print(i)
            if td["log_check"] != None and not td["log_check"](hndl.buffer):
                fail_count += 1
                print("---------------test_number=%d---------------" % (
                test_number,))
                print("logger records:")
                for i in hndl.buffer:
                    print(i)
                lines = inspect.getsourcelines(td["log_check"])
                print(u"test_barcode_add: failed log check:\n%s" %
                      (''.join(lines[0]),))
            if td["func_check"] != None and not td["func_check"](mocker.logs):
                fail_count += 1
                print("---------------test_number=%d---------------" % (test_number,))
                print("logs:")
                for func, args in mocker.logs:
                    print((func, args))
                lines = inspect.getsourcelines(td["func_check"])
                print(u"test_barcode_add: failed check:\n%s" %
                          (''.join(lines[0]),))
            log.removeHandler(hndl)
        if fail_count > 0:
            self.fail("test failed, check output")
