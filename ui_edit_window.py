# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import Tkinter as tk
from ui_scrollframe import UIScrollFrame
from ui_letter_add import UILetterAdd
from ui_letter import UILetter
from dbstorage import LOCK_STATE_FINAL, LOCK_STATE_FREE
from envelope_render import render_DL_letters
import os

class UIEditWindow(tk.Frame):
	"""UI класс главное окно
	"""
	def __init__(self, master, postconn, dbstorage, user_ident, reestr_info):
		#
		self.postconn = postconn
		self.dbstorage = dbstorage
		self.user_ident = user_ident
		self.rowcount = 0
		self.reestr_info = reestr_info
		#
		tk.Frame.__init__(self, master)
		self.ui_add = UILetterAdd(self,
			default_values={"db_mass_pages":1,
							"mass":20,
							"db_locked":LOCK_STATE_FREE,
							"db_user_id": self.user_ident.get_user_id(),
							"db_reestr_id": self.reestr_info["db_reestr_id"],
							"with-simple-notice": self.reestr_info["with-simple-notice"]
							},
			action_callback=self.action_letter)
		self.ui_add.config(bd=5, relief=tk.GROOVE)
		self.ui_add.pack(side=tk.TOP, fill=tk.X)
		self.ui_scrollarea = UIScrollFrame(self)
		self.ui_scrollarea.config(bd=5, relief=tk.GROOVE)
		self.ui_scrollarea.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
	def refresh(self):
		#TODO: добавить обновление информации реестра, disable для LOCK_STATE_FINAL
		self.rowcount = 0
		self.ui_scrollarea.clear()
		for data, err in self.dbstorage.get_letters_list(self.reestr_info["db_reestr_id"]):
			uu = UILetter(self.ui_scrollarea.frame, self.rowcount % 2, self.action_letter)
			uu.set_data(data)
			uu.pack(side=tk.TOP, fill=tk.X, expand=False)
			self.rowcount += 1
	def action_letter(self, command, letter_info, contagent_info={ }):
		""" Callback функция для обработки действий в форме добавления и в письме
		
		:param command:
		:param letter_info:
		:param contagent_info:
		:return:
		"""
		if command == "ADD":
			cinfo,err = self.dbstorage.get_contragent_info(contagent_info["srctype"],contagent_info["srcid"])
			if cinfo != None:
				for k,v in cinfo.iteritems():
					letter_info[k] = v
			self.dbstorage.add_letter(letter_info)
			self.refresh()
		if command == "SAVE":
			res = self.dbstorage.modify_letter(letter_info)
			if res[0]:
				return True
		if command == "PRINT":
			os.startfile(render_DL_letters([letter_info]))
		if command == "DELETE":
			self.dbstorage.delete_letter(letter_info)
			self.refresh()
		if command == "BARCODE":
			pass
