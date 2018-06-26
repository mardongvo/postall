# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import Tkinter as tk
from ui_reestr_add import UIReestrAdd
from ui_reestr_element import UIReestrElement
from ui_scrollframe import UIScrollFrame
from datetime import datetime, timedelta
from dbstorage import LOCK_STATE_FINAL, LOCK_STATE_BATCH, LOCK_STATE_FREE
from ui_edit_window import UIEditWindow
import logging

class UIMainWindow(tk.Frame):
	"""UI класс главное окно
	"""
	def __init__(self, master, postconn, dbstorage, user_ident):
		#
		self.postconn = postconn
		self.dbstorage = dbstorage
		self.user_ident = user_ident
		self.rowcount = 0
		#self.reestr_list = []
		#
		tk.Frame.__init__(self, master)
		self.ui_add = UIReestrAdd(self, self.user_ident, self.action_reestr)
		self.ui_add.config(bd=5, relief=tk.GROOVE)
		self.ui_add.pack(side=tk.TOP, fill=tk.X)
		self.ui_scrollarea = UIScrollFrame(self)
		self.ui_scrollarea.config(bd=5, relief=tk.GROOVE)
		self.ui_scrollarea.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
	def refresh(self):
		self.rowcount = 0
		todate = datetime.now()+timedelta(1)
		fromdate = todate - timedelta(15)
		self.ui_scrollarea.clear()
		for data, err in self.dbstorage.get_reestr_list(fromdate, todate):
			uu = UIReestrElement(self.ui_scrollarea.frame, self.user_ident, self.rowcount % 2, self.action_reestr)
			uu.set_data(data)
			uu.pack(side=tk.TOP, fill=tk.X, expand=False)
			self.rowcount += 1
	def action_reestr(self, command, reestr_info):
		if command == "ADD":
			reestr_info["db_user_id"] = self.user_ident.get_user_id()
			self.dbstorage.add_reestr(reestr_info)
			self.refresh()
		if command == "EDIT":
			w = UIEditWindow(tk.Toplevel(self.master), self.postconn, self.dbstorage, self.user_ident, reestr_info)
			w.pack(fill="both", expand=True)
		if command == "DELETE":
			res = self.dbstorage.delete_reestr(reestr_info)
			if res[1]>"":
				logging.error(res[1])
			self.refresh()
		if command == "DATE":
			if reestr_info["db_locked"] == LOCK_STATE_BATCH:
				err = self.postconn.modify_batch(reestr_info["batch-name"], reestr_info["list-number-date"])
				if err == "":
					self.dbstorage.modify_reestr(reestr_info)
				else:
					logging.error(err)
			if reestr_info["db_locked"] == LOCK_STATE_FREE:
				self.dbstorage.modify_reestr(reestr_info)
			self.refresh()
		if command == "LOCK":
			self.dbstorage.lock_reestr(reestr_info["db_reestr_id"], LOCK_STATE_FINAL)
			self.refresh()
		if command == "REFRESH":
			self.refresh()
