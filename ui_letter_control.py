# -*- coding: utf-8 -*-

import Tkinter as tk

class UILetterControl(tk.Frame):
	"""UI класс для разных операций в UIEditWindow
	"""
	def __init__(self, master, action_callback=None):
		"""
		
		:param master:
		:param action_callback:
		"""
		tk.Frame.__init__(self, master)
		self.action_callback = action_callback
		#кнопки
		self.btn_refresh = tk.Button(self, text=u"Обновить", command=self.onClickRefresh)
		self.btn_refresh.grid({"column": 1, "row": 0, "sticky": "NSEW"})
		self.btn_add_barcodes = tk.Button(self, text = u"Присвоить номера всем", command=self.onClickAdd)
		self.btn_add_barcodes.grid({"column": 2, "row":0, "sticky":"NSEW"})
		self.btn_del_barcodes = tk.Button(self, text=u"Удалить номера у всех", command=self.onClickDel)
		self.btn_del_barcodes.grid({"column": 3, "row": 0, "sticky": "NSEW"})
		self.btn_print_all = tk.Button(self, text=u"Печать всех", command=self.onClickPrint)
		self.btn_print_all.grid({"column": 4, "row": 0, "sticky": "NSEW"})
		self.btn_print_my = tk.Button(self, text=u"Печать моих",
								   command=self.onClickPrintMy)
		self.btn_print_my.grid({"column": 5, "row": 0, "sticky": "NSEW"})
		self.btn_print_notif = tk.Button(self, text=u"Печать уведомлений", command=self.onClickPrintNotif)
		self.btn_print_notif.grid({"column": 7, "row": 0, "sticky": "NSEW"})
	def onClickAdd(self):
		if self.action_callback:
			self.action_callback("BARCODE_ADD_ALL", None)
	def onClickDel(self):
		if self.action_callback:
			self.action_callback("BARCODE_DEL_ALL", None)
	def onClickRefresh(self):
		if self.action_callback:
			self.action_callback("REFRESH", None)
	def onClickPrint(self):
		if self.action_callback:
			self.action_callback("PRINT_ALL", None)
	def onClickPrintMy(self):
		if self.action_callback:
			self.action_callback("PRINT_MY", None)
	def onClickPrintNotif(self):
		if self.action_callback:
			self.action_callback("PRINT_NOTIFICATIONS", None)
	def disable(self):
		self.btn_add_barcodes["state"] = "disabled"
		self.btn_del_barcodes["state"] = "disabled"
