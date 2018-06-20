# -*- coding: utf-8 -*-

class UserIdentifier:
	""" Класс информации о пользователе
	"""
	def __init__(self, dbstorage, user_id):
		self.user_info = {}
		inf = dbstorage.get_user_info(user_id)
		if inf[1] == "":
			self.user_info = inf[0]
	def get_fio(self):
		if "fio" in self.user_info:
			return self.user_info["fio"]
		return ""
	def get_user_id(self):
		if "db_user_id" in self.user_info:
			return self.user_info["db_user_id"]
		return ""
	def is_admin(self):
		if "admin" in self.user_info:
			return self.user_info["admin"]
		return 0
