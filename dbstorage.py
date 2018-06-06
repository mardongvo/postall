# -*- coding: utf-8 -*-

import psycopg2
import configuration as defconf

class DBStorage:
	def __init__(self):
		self.conn = None
	def connect(self, connstring=defconf.DB_CONNECTION):
		return True, err
	def get_user_info(self, userid):
		return {"fio":, "admin":False}
	def get_contragent_info(self, srctype, srcid):
		return {}, err
	def get_reestr_list(self, fromdate, todate):
		return [], err
	def add_reestr(self, userid, ...):
		return id, err
	def add_letter(self, reestr_id, ...):
		return id, err
	def modify_letter(self, letter_id, letter_info):
		return True, err
	def lock_letter(self, letter_id, flag):
		return err
	def lock_reestr(self, reestr_id, flag):
		return err
	def get_reestr_info(self, reestr_id):
		return {}, err
	def get_letter_info(self, letter_id):
		return {}, err
	def set_reestr_ext_id(self, reestr_id, ext_id):
		return err
	def set_letter_ext_id(self, letter_id, ext_id):
		return err
	def set_letter_barcode(self, letter_id, barcode):
		return err
