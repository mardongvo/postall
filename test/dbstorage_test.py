# -*- coding: utf-8 -*-
import unittest

import sys
sys.path.append('..')

from datetime import datetime
from dbstorage import DBStorage
import configuration as defconf
from copy import copy

class MockCursor:
	rowcount = 1
	def __init__(self):
		pass
	def execute(self, sql, param=None):
		pass
	def fetchone(self):
		return ()

class MockDB:
	def __init__(self, cursor_class):
		self.cursor_class = cursor_class
	def cursor(self):
		return self.cursor_class()
	def commit(self):
		pass
	def rollback(self):
		pass

class CursorErr(MockCursor):
	rowcount = 1
	def execute(self, sql, param=None):
		raise Exception('common exception')

class CursorPrint(MockCursor):
	rowcount = 0
	def execute(self, sql, param=None):
		print(sql)
		return None
	def fetchone(self):
		return (0,)

class test_DB(unittest.TestCase):
	def test_field_map(self):
		self.connobj = MockDB(CursorErr)
		self.db = DBStorage(self.connobj)
		self.db.add_field_map("REESTR_INFO", defconf.REESTR_DB_FIELDS)
		self.db.add_field_map("LETTER_INFO", defconf.LETTER_DEFAULT)
		self.db.add_field_map("LETTER_INFO", defconf.LETTER_DB_FIELDS)
		self.db.add_field_map("USER_DICT", defconf.USER_DB_FIELDS)
		contragent_struct = copy(defconf.CONTRAGENT_DB_FIELDS)
		for k, v in defconf.LETTER_DEFAULT.iteritems():
			if k.endswith("-to"):
				contragent_struct[k] = v
		self.db.add_field_map("CONTRAGENT_DICT", contragent_struct)
		self.db.add_field_map("POSTINDEX", defconf.POSTINDEX_DB_FIELDS)
		self.db.add_field_map("COMMAND_QUEUE", defconf.COMMAND_DB_FIELDS)
		#проверяем взаимно однозначное соответсвие названий полей в БД и в структуре dict()
		for tbl in ["REESTR_INFO", "LETTER_INFO", "USER_DICT", "CONTRAGENT_DICT", "POSTINDEX", "COMMAND_QUEUE"]:
			self.assertTrue(tbl in self.db.key2field)
			for k in self.db.key2field[tbl].keys():
				self.assertTrue( k==self.db.field2key[tbl][self.db.key2field[tbl][k]] )
	def test_sql(self):
		self.connobj = MockDB(CursorPrint)
		self.db = DBStorage(self.connobj)
		test_struct = {"db_int":0, "db_str":"", "db_date":"date", "db_bool":True}
		v = {"db_int":10, "db_str":u'testТест', "db_date":datetime(2018,1,1), "db_bool":True}
		self.db.add_field_map("TESTTABLE", test_struct)
		test_cases = [
			("INSERT",u"insert into TESTTABLE(db_bool,db_date,db_int,db_str) values (TRUE,'2018-01-01',10,'testТест') returning db_int;"),
			("UPDATE",u"UPDATE TESTTABLE set db_bool=TRUE,db_date='2018-01-01',db_int=10,db_str='testТест' where db_int=10;"),
			("DELETE",u"DELETE FROM TESTTABLE where db_bool=TRUE and db_date='2018-01-01' and db_int=10 and db_str='testТест';"),
			("SELECT",u"SELECT * FROM TESTTABLE where  db_bool=TRUE and db_date='2018-01-01' and db_int=10 and db_str='testТест' order by db_int;")
		]
		for i in test_cases:
			self.assertTrue(self.db._build_sql("TESTTABLE", i[0], v, "db_int") == i[1])
		#print(self.db._build_sql("TESTTABLE", "SELECT", {}, "db_int"))
	#TODO: проверить value2str

if __name__=='__main__':
	unittest.main()
