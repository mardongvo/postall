# -*- coding: utf-8 -*-

import Tkinter as tk
import copy
from dbstorage import LOCK_STATE_FREE, LOCK_STATE_BACKLOG, LOCK_STATE_BATCH, LOCK_STATE_FINAL
from datetime import datetime

DEFAULT_WIDTH = 20

#цвета фона для различия позиций в списке
COLORS = (
	("#cccdff", "#7e80c9"),
	("#ffc9c9", "#c97e7e")
)

class UIReestrElement(tk.Frame):
	"""UI класс представления реестра
	"""
	GUI_DEF = [
		{'key': 'db_reestr_id', 'title': u'Номер', 'type': 'text', 'edit': False, 'maxsize': 10, 'row': 0},
		{'key': 'db_create_date', 'title': u'Дата создания', 'type': 'date', 'edit': False, 'maxsize': 12, 'row': 0},
		{'key': 'batch-name', 'title': u'Номер(сайт)', 'type': 'text', 'edit': False, 'maxsize': 10, 'row': 1},
		{'key': 'list-number-date', 'title': u'Дата отправки', 'type': 'date', 'edit': True, 'maxsize': 12, 'row': 1},
		{'key': 'db_letter_count', 'title': u'Кол-во', 'type': 'integer', 'edit': False, 'maxsize': 10, 'row': 0},
		{'key': 'with-simple-notice', 'title': u'С уведомл.', 'type': 'bool', 'edit': False, 'maxsize': 10, 'row': 1},
		{'key': 'db_comment', 'title': u'Комм.', 'type': 'text', 'edit': False, 'maxsize': 20, 'row': 0},
		{'key': 'fio', 'title': u'ФИО', 'type': 'text', 'edit': False, 'maxsize': 20, 'row': 1},
	]

	def __init__(self, master, bgcolor=0, action_callback=None):
		self.reestr_info = {}
		self.action_callback = action_callback
		#create widgets
		tk.Frame.__init__(self, master)
		self["bg"] = COLORS[bgcolor][0]
		##########
		gridcol = {}
		for i in map(lambda a: a['row'], self.GUI_DEF):
			gridcol[i] = 0
		for c in self.GUI_DEF:
			col = gridcol[c['row']]
			L1 = tk.Label(self, text = c['title'])
			L1.grid({"column":col, "row":c['row'], "sticky":"NSW"})
			L1["width"] = -1
			L1["bg"] = COLORS[bgcolor][0]
			ent = tk.Entry(self)
			#ent["background"] = COLORS[bgcolor][1]
			ent["readonlybackground"] = COLORS[bgcolor][0]
			if not c['edit']:
				ent.config(state='readonly')
			ent.grid({"column":col+1, "row":c['row'], "sticky":"NSW"})
			if 'maxsize' in c:
				ent["width"] = c['maxsize']
			else:
				ent["width"] = DEFAULT_WIDTH
			c['widget'] = ent
			gridcol[c['row']] += 2
		#кнопки
		self.btn_date = tk.Button(self, text = u"Изменить дату отправки", command=self.onClickDate, bg=COLORS[bgcolor][0])
		self.btn_date.grid({"column":max(gridcol.values())+1, "row":0, "sticky":"NSEW"})
		#
		self.btn_lock = tk.Button(self, text=u"Заблокировать окончательно", command=self.onClickLock, bg=COLORS[bgcolor][0])
		self.btn_lock.grid({"column":max(gridcol.values())+2, "row":1, "sticky":"NSEW"})
		#
		self.btn_delete = tk.Button(self, text=u"Удалить", command = self.onClickDelete, bg=COLORS[bgcolor][0])
		self.btn_delete.grid({"column":max(gridcol.values())+2, "row":0, "sticky":"NSEW"})
	def set_data(self, reestr_info):
		""" Скопировать данные реестра, заполнить entry
		"""
		self.reestr_info = copy.copy(reestr_info)
		for c in self.GUI_DEF:
			c["widget"].config(state='normal') #необходимо для редактирования
			c["widget"].delete(0,"end")
			if c["key"] in self.reestr_info:
				v = self.reestr_info[c["key"]]
				if isinstance(v, bool):
					v = u'Да' if v else u'Нет'
				if isinstance(v, int):
					v = str(v)
				if isinstance(v, datetime):
					v = v.strftime("%d.%m.%Y")
				c["widget"].insert("end", v)
			if not c["edit"]:
				c["widget"].config(state='readonly')
		self.set_lock(self.reestr_info["db_locked"])
	def set_lock(self, lock_state):
		""" Установить доступность элементов согласно статусу блокировки
		"""
		self.btn_date["state"] = "disabled"
		self.btn_lock["state"] = "disabled"
		self.btn_delete["state"] = "disabled"
		for c in self.GUI_DEF:
			c["widget"].config(state='readonly')
		if lock_state == LOCK_STATE_FREE:
			self.btn_delete["state"] = "normal"
			for c in self.GUI_DEF:
				if c["edit"]:
					c["widget"].config(state='normal')
		if lock_state == LOCK_STATE_BATCH:
			self.btn_date["state"] = "normal"
		if lock_state == LOCK_STATE_FINAL:
			pass
	def sync(self):
		""" Перенсит данные из формы в reestr_info
		Пока только дата отправки
		"""
		for c in self.GUI_DEF:
			if c["key"] == 'list-number-date':
				try:
					v = datetime.strptime(c["widget"].get(), "%Y-%m-%d")
					self.reestr_info[c["key"]] = v
				except ValueError:
					pass #TODO: log errors
	def onClickDate(self):
		self.sync()
		if self.action_callback:
			self.action_callback("DATE", self.reestr_info)
	def onClickLock(self):
		if self.action_callback:
			self.action_callback("LOCK", self.reestr_info)
	def onClickDelete(self):
		if self.action_callback:
			self.action_callback("DELETE", self.reestr_info)
