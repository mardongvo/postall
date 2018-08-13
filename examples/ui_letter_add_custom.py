# -*- coding: utf-8 -*-

import Tkinter as tk
import tkFileDialog
from copy import copy
from functools import partial
import logging
from ui_letter import pages_to_mass
import codecs
import re

DEFAULT_WIDTH = 20

class UILetterAdd(tk.Frame):
	"""UI класс для добавления письма
	Пример кастомного класса: несколько типов контрагентов, пакетное добавление
	"""
	def __init__(self, master, default_values={}, action_callback=None):
		"""
		
		:param master:
		:param default_values: dict() - какие-либо значения для письма по-умолчанию
		:param action_callback:
		"""
		tk.Frame.__init__(self, master)
		self.action_callback = action_callback
		self.default_values = default_values
		#1
		L1 = tk.Label(self, text = u"Контрагент 1", width = -1)
		L1.grid({"column": 0, "row": 0, "sticky": "NSW"})
		self.entry_id1 = tk.Entry(self)
		self.entry_id1.grid({"column": 1, "row": 0, "sticky": "NSW"})
		self.entry_id1["width"] = DEFAULT_WIDTH
		#кнопки
		self.btn_add1 = tk.Button(self, text = u"Добавить", command=partial(self.onClickAdd, self.entry_id1, 1))
		self.btn_add1.grid({"column":2, "row":0, "sticky":"NSEW"})
		self.btn_add1_list = tk.Button(self, text = u"Добавить списком", command=partial(self.onClickAddList, 1))
		self.btn_add1_list.grid({"column":3, "row":0, "sticky":"NSEW"})
		#2
		L1 = tk.Label(self, text = u"Контрагент 2", width=-1)
		L1.grid({"column":0, "row":1, "sticky":"NSW"})
		self.entry_id2 = tk.Entry(self)
		self.entry_id2.grid({"column": 1, "row": 1, "sticky": "NSW"})
		self.entry_id2["width"] = DEFAULT_WIDTH
		#кнопки
		self.btn_add2 = tk.Button(self, text = u"Добавить", command=partial(self.onClickAdd, self.entry_id2, 2))
		self.btn_add2.grid({"column":2, "row":2, "sticky":"NSEW"})
		self.btn_add2_list = tk.Button(self, text = u"Добавить списком", command=partial(self.onClickAddList, 2))
		self.btn_add2_list.grid({"column":3, "row":2, "sticky":"NSEW"})
		#3
		L1 = tk.Label(self, text = u"Контрагент 3", width=-1)
		L1.grid({"column":0, "row":2, "sticky":"NSW"})
		self.entry_id3 = tk.Entry(self)
		self.entry_id3.grid({"column": 2, "row": 1, "sticky": "NSW"})
		self.entry_id3["width"] = DEFAULT_WIDTH
		#кнопки
		self.btn_add3 = tk.Button(self, text = u"Добавить", command=partial(self.onClickAdd,  self.entry_id3, 3))
		self.btn_add3.grid({"column":2, "row":1, "sticky":"NSEW"})
		self.btn_add3_list = tk.Button(self, text = u"Добавить списком", command=partial(self.onClickAddList, 3))
		self.btn_add3_list.grid({"column":3, "row":1, "sticky":"NSEW"})
		###
		L = tk.Label(self, text=u"Формат файла: csv. строки 'идентификатор;кол-во страниц;комментарий'")
		L.grid({"column":0,"row":3, "columnspan":4, "sticky":"W"})
	def onClickAdd(self, srcentry, srctype):
		if self.action_callback:
			letter_info = copy(self.default_values)
			contragent_info = {"srctype":srctype,"srcid":srcentry.get()}
			self.action_callback("ADD", letter_info, contragent_info)
	def onClickAddList(self,srctype):
		""" Добавление писем списком из csv файла
		
		:param srctype:
		:return:
		"""
		#запрашиваем путь к файлу
		fname = tkFileDialog.askopenfilename(filetypes=[("CSV","*.csv")])
		if not fname: return
		#открываем файл в кодировке windows-1251
		infile = codecs.open(fname, "r", encoding="windows-1251")
		while True:
			s = infile.readline()
			if s=="": break
			#читаем строки в виде "число;число;что угодно до конца строки"
			MO = re.match("(\d+);([ \d]+);(.*?)[\r\n]+", s)
			if MO:
				#превращаем группы match object в параметры
				idd = MO.group(1)
				pages_count = 1
				try:
					pages_count = int(MO.group(2))
				except Exception as e:
					logging.error(e)
					pages_count = 1
				comment = MO.group(3)
				logging.error(u"добавление: "+idd)
				if self.action_callback:
					#добавляем письмо
					letter_info = copy(self.default_values)
					letter_info["comment"] = comment
					letter_info["db_mass_pages"] = pages_count
					letter_info["mass"] = pages_to_mass(pages_count)
					contragent_info = {"srctype":srctype,"srcid":idd}
					self.action_callback("ADD", letter_info, contragent_info)
			else:
				logging.error(u"неизвестно: "+s)
		infile.close()
