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

class MockDBPC:
    """ Класс-имитатор
    """
    def __init__(self):
        self.retvals = {} # возвращаемые значения для вызовов
        self.logs = [] # лог вызовов фуккций с параметрами
    def add_retval(self, funcname, callnum, retval):
        self.retvals[(funcname, callnum)] = retval
    def call_func(self, funcname, *args):
        counter = "callcount_"+funcname
        if counter not in self.__dict__:
            self.__dict__[counter] = 1
        else:
            self.__dict__[counter] += 1
        key1 = (funcname, self.__dict__[counter])
        key2 = (funcname, 0)
        self.logs.append((key1,args))
        if key1 in self.retvals:
            return self.retvals[key1]
        if key2 in self.retvals:
            return self.retvals[key2]
        return None
    def __getattr__(self, item):
        return partial(self.call_func, item)
    """
    # DB
    def get_reestr_info(self, reestr_id):
        pass
    def get_user_info(self, user_id):
        pass
    def modify_letter(self, letter_info):
        pass
    def modify_reestr(self, reestr_info):
        pass
    # PC
    def add_backlog(self, letter_info):
        pass
    def get_backlog(self, idd, source):
        pass
    def add_batch(self, batch_date, ids):
        pass
    def add_backlog_to_batch(self, reestr_info, idd):
        pass
    """

class TestMock(TestCase):
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
            self.fail("method2 (unknown), call != None")

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
            #print("log content")
            #print(map(lambda a: a.msg, hndl.buffer))
            #print("mocker content")
            #print(mocker.logs)
            for func, args in mocker.logs:
                if func[0] == "modify_letter":
                    if args[0]["db_locked"] != expect_state:
                        self.fail(u"test_barcode_del: unexpected (%s, %s, %d) <> (%d)" %\
                                  (err1, err2, expect_state, args[0]["db_locked"]))
