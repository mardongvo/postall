# -*- coding: utf-8 -*-

from datetime import datetime, date

def fix_json_field_name(field_name):
	return field_name.replace("-","_")

def value2str(v):
	if isinstance(v, bool):
		return "TRUE" if v else "FALSE"
	if isinstance(v, int):
		return "%d" %(v,)
	if isinstance(v, datetime) or isinstance(v, date):
		return v.strftime("'%Y-%m-%d'")
	if isinstance(v, str) or isinstance(v, unicode):
		return "'%s'" % (v.replace("'","''"),)
	raise Exception("value2str: unknown type")

LOCK_STATE_FREE = 0		#состояние редактирования
LOCK_STATE_BACKLOG = 1	#заказ подготовлен, редактирование недоступно, доступно удаление заказа
LOCK_STATE_BATCH = 2	#заказ перенесен, редактирование недоступно, удаление заказа недоступно
LOCK_STATE_FINAL = 0xFF #реестр заблокирован окончательно

class DBStorage:
	""" Класс работы с базой данных
	
	"""
	def __init__(self, connobj):
		self.conn = connobj
		self.key2field = {} #json ключ в имя поля
		self.field2key = {} #имя поля в json ключ
	def add_field_map(self, tablename, info_dict):
		if tablename not in self.key2field:
			self.key2field[tablename] = {}
		if tablename not in self.field2key:
			self.field2key[tablename] = {}
		for k in info_dict.keys():
			fld = fix_json_field_name(k)
			self.key2field[tablename][k] = fld
			self.field2key[tablename][fld] = k
	def _build_sql(self, tablename, command, data, key_field=None):
		""" Построение строки sql
		
		:param tablename: имя таблицы
		:param command: команда (INSERT, UPDATE, DELETE)
		:param data: dict() - данные
		:param key_field: поле-ключ таблицы
		:return: строка
		"""
		# фильтрация - убираем неизвестные поля и ключевое поле
		sql = ""
		if command == "INSERT":
			kk = filter(lambda a: a in self.key2field[tablename] or a == key_field, data.keys())
			sql = "insert into %s(%s) values (%s) returning %s;" %\
				  	( tablename,
					','.join( map(lambda a: self.key2field[tablename][a], kk) ),
					','.join( map(lambda a: value2str(data[a]), kk) ),
					key_field)
		if command == "UPDATE":
			kk = filter(lambda a: a in self.key2field[tablename] or a == key_field, data.keys())
			sql = "UPDATE %s set %s where %s=%s;" % \
				  	(tablename,
					','.join( map(lambda a: "%s=%s" % (self.key2field[tablename][a], value2str(data[a])), kk) ),
					 key_field, value2str(data[key_field]))
		if command == "DELETE":
			kk = filter(lambda a: a in self.key2field[tablename], data.keys())
			sql = "DELETE FROM %s where %s;" % \
				  	(tablename,
					 ' and '.join( map(lambda a: "%s=%s" % (self.key2field[tablename][a], value2str(data[a])), kk) ))
		if command == "SELECT":
			kk = filter(lambda a: a in self.key2field[tablename], data.keys())
			sql = "SELECT * FROM %s where %s %s;" % \
				  (tablename, ' and '.join( map(lambda a: "%s=%s" % (self.key2field[tablename][a], value2str(data[a])), kk) ), ("order by "+key_field) if key_field!=None else "" )
		return sql
	def _run_sql(self, sql, need_return=False):
		""" Функция выполнения sql, модифицирующих данные
		
		:param sql: строка sql запроса
		:param need_return: нужно ли вернуть результат (в sql содержится конструкция returning)
		:return: (int|bool, error)
		"""
		error = ""
		res = None
		try:
			cur = self.conn.cursor()
			cur.execute(sql)
			if need_return:
				res = cur.fetchone()[0]
			else:
				cnt = cur.rowcount
				if cnt != 1:
					res = False
					raise Exception(u'Измененных строк != 1;')
				else:
					res = True
			self.conn.commit()
		except Exception as e:
			try:
				self.conn.rollback()
			except: pass
			if need_return:
				res = 0
			else:
				res = False
			error += unicode(e)
		return res, error
	def _select_sql(self, tablename, sql, filter_fields=True):
		error = ""
		try:
			cur = self.conn.cursor()
			cur.execute(sql)
			for data in cur:
				res = {}
				for i in range(len(data)):
					fld = cur.description[i][0]
					v = data[i]
					if isinstance(v, str):
						v = v.decode("UTF-8")
					if filter_fields and fld in self.field2key[tablename]:
						res[self.field2key[tablename][fld]] = v
					else:
						fldname = fld
						if fld in self.field2key[tablename]: fldname = self.field2key[tablename][fld]
						res[fldname] = v
				yield res, ""
		except Exception as e:
			error += unicode(e)
			yield None, error
	def get_user_info(self, userid):
		for i in self._select_sql("USER_DICT", "select * from USER_DICT where db_user_id=%s;" % (value2str(userid),)):
			return i
		return {}, ""
	def get_contragent_info(self, srctype, srcid):
		res = None
		for i in self._select_sql("CONTRAGENT_DICT", "select * from CONTRAGENT_DICT where srctype=%s and srcid=%s;" % (value2str(srctype),value2str(srcid))):
			return i
		return {}, ""
	def get_reestr_list(self, fromdate, todate):
		if not(isinstance(fromdate, datetime) and isinstance(todate, datetime)):
			return [], u"Даты отбора реестров не являются объектом datetime"
		res = []
		for i in self._select_sql("REESTR_INFO", "select * from REESTR_INFO where db_create_date between %s and %s order by db_create_date desc, db_reestr_id;" % (value2str(fromdate),value2str(todate))):
				res.append(i)
		return res
	def get_letters_list(self, reestr_id):
		res = []
		for i in self._select_sql("LETTER_INFO", self._build_sql("LETTER_INFO", "SELECT", {"db_reestr_id":reestr_id}, "db_letter_id")):
			res.append(i)
		return res
	def get_reestr_info(self, reestr_id):
		for i in self._select_sql("REESTR_INFO", self._build_sql("REESTR_INFO", "SELECT", {"db_reestr_id":reestr_id})):
			return i
	def get_letter_info(self, letter_id):
		for i in self._select_sql("LETTER_INFO", self._build_sql("LETTER_INFO", "SELECT", {"db_letter_id":letter_id})):
			return i
	def add_reestr(self, reestr_info):
		""" Добавление реестра
		
		:param reestr_info: {"with-simple-notice":boolean, "db_user_id": '...', "db_create_date": datetime}
		:return: idd - integer, err - string
		"""
		return self._run_sql(self._build_sql("REESTR_INFO", "INSERT", reestr_info, "db_reestr_id"), True)
	def delete_reestr(self, reestr_info):
		""" Удаление реестра
		
		:param reestr_id: integer - db_reestr_id
		:return:
		"""
		inf, err = self.get_reestr_info(reestr_info["db_reestr_id"])
		if err == "":
			if inf["db_letter_count"]==0:
				return self._run_sql(self._build_sql("REESTR_INFO", "DELETE", {"db_reestr_id":reestr_info["db_reestr_id"],"db_locked":LOCK_STATE_FREE}, "db_reestr_id"), False)
		return False, u"Реестр не пустой"
	def sync_reestr(self, reestr_id):
		""" Синхронизация полей реестра после изменения писем
		
		:param reestr_id: integer - db_reestr_id
		:return:
		"""
		#синхронизация количества писем
		self._run_sql("with t as (select count(*) CNT from LETTER_INFO where db_reestr_id=%s) update REESTR_INFO set db_letter_count=t.CNT from t where db_reestr_id=%s" % (value2str(reestr_id),value2str(reestr_id)))
		#синхронизация состояния
		self._run_sql(
			"with t as (select count(*) CNT from LETTER_INFO where db_reestr_id=%s and db_locked=%s) update REESTR_INFO set db_locked=%s from t where db_reestr_id=%s and t.CNT>0" % (
			value2str(reestr_id), value2str(LOCK_STATE_BATCH), value2str(LOCK_STATE_BATCH), value2str(reestr_id)))
		self._run_sql(
			"with t as (select count(*) CNT from LETTER_INFO where db_reestr_id=%s and db_locked=%s) update REESTR_INFO set db_locked=%s, batch_name='' from t where db_reestr_id=%s and t.CNT=0" % (
			value2str(reestr_id), value2str(LOCK_STATE_BATCH), value2str(LOCK_STATE_FREE), value2str(reestr_id)))

	def modify_reestr(self, reestr_info):
		""" Изменение реестра
		
		:param reestr_info: dict() -
		:return:
		"""
		return self._run_sql(self._build_sql("REESTR_INFO", "UPDATE", reestr_info,
							"db_reestr_id"), False)
	def add_letter(self, letter_info):
		""" Добавление письма

		:param letter_info: dict() - configuration.LETTER_DEFAULTS
		:return: idd - integer, err - string
		"""
		#TODO: добавить проверку на статус реестра
		res = self._run_sql(self._build_sql("LETTER_INFO", "INSERT", letter_info, "db_letter_id"), True)
		self.sync_reestr(letter_info["db_reestr_id"])
		return res
	def modify_letter(self, letter_info):
		""" Изменение письма
		
		:param letter_info:
		:return:
		"""
		res = self._run_sql(self._build_sql("LETTER_INFO", "UPDATE", letter_info, "db_letter_id"), False)
		self.sync_reestr(letter_info["db_reestr_id"])
		return res
	def delete_letter(self, letter_info):
		""" Удаление письма, выполняется только для состояния LOCK_STATE_FREE
		:param letter_info: dict() - configuration.LETTER_DEFAULTS
		"""
		res = self._run_sql(self._build_sql("LETTER_INFO", "DELETE", {"db_letter_id":letter_info["db_letter_id"],"db_locked":LOCK_STATE_FREE}, "db_letter_id"), False)
		self.sync_reestr(letter_info["db_reestr_id"])
		return res
	def lock_letter(self, letter_info, state):
		""" Смена состояния блокировки письма
		:param letter_info: dict() - configuration.LETTER_DEFAULTS
		:param state: -- LOCK_STATE_*
		"""
		return self._run_sql(
			self._build_sql("LETTER_INFO", "UPDATE", {"db_letter_id": letter_info["db_letter_id"], "db_locked": state},
							"db_letter_id"), False)
	def lock_reestr(self, reestr_id, state):
		return self._run_sql(
			self._build_sql("REESTR_INFO", "UPDATE", {"db_reestr_id": reestr_id, "db_locked": state},
							"db_reestr_id"), False)
	def get_postindex_info(self, postindex):
		return {}
