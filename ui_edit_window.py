# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import Tkinter as tk
from ui_scrollframe import UIScrollFrame
from ui_letter_add import UILetterAdd
from ui_letter import UILetter
from ui_letter_control import UILetterControl
from dbstorage import LOCK_STATE_FINAL, LOCK_STATE_FREE, LOCK_STATE_BACKLOG, LOCK_STATE_BATCH
from user_identifier import UserIdentifier
from envelope_render import render_DL_letters
import os
from copy import copy
import configuration as defconf
import logging

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
		self.ui_ctl = UILetterControl(self, action_callback=self.action_letter)
		self.ui_ctl.config(bd=5, relief=tk.GROOVE)
		self.ui_ctl.pack(side=tk.TOP, fill=tk.X)
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
		self.refresh()
	def update_title(self):
		""" Обновление информации о реестре
		
		:return:
		"""
		self.reestr_info,err = self.dbstorage.get_reestr_info(self.reestr_info["db_reestr_id"])
		if err == "":
			self.master.wm_title(u"Реестр №%s (сайт: %s) от %s%s" %
				(self.reestr_info["db_reestr_id"],
				 self.reestr_info["batch-name"],
				 self.reestr_info["db_create_date"].strftime("%d.%m.%Y"),
				 " (ЗАБЛОКИРОВАН)" if self.reestr_info["db_locked"]==LOCK_STATE_FINAL else ""))
	def refresh(self):
		#TODO: оптимизировать обновление списка
		self.update_title()
		self.rowcount = 0
		self.ui_scrollarea.clear()
		for data, err in self.dbstorage.get_letters_list(self.reestr_info["db_reestr_id"]):
			uu = UILetter(self.ui_scrollarea.frame, self.rowcount % 2, self.action_letter)
			#если реестр заблокирован, передаем это письмам, чтобы не возникало ложного ощущения, что можно редактировать
			if self.reestr_info["db_locked"]==LOCK_STATE_FINAL:
				data["db_locked"]=LOCK_STATE_FINAL
			uu.set_data(data)
			uu.pack(side=tk.TOP, fill=tk.X, expand=False)
			self.rowcount += 1
	def barcode_add(self, letter_info):
		self.reestr_info, err = self.dbstorage.get_reestr_info(self.reestr_info["db_reestr_id"])
		if self.reestr_info["db_locked"] == LOCK_STATE_FINAL: return
		#1. необходимо добавить в новые
		if letter_info["db_locked"] == LOCK_STATE_FREE:
			#копируем постоянные поля
			for k, v in defconf.LETTER_CONSTANT_FIELDS.iteritems():
				letter_info[k] = v
			#комментарий к отправлению - <ФИО>, <комментарий из письма>
			letter_info["order-num"] = UserIdentifier(
				self.dbstorage.get_user_info(letter_info["db_user_id"])).get_fio() + u", " + letter_info["comment"]
			#добавлени в "новые" в кабинете
			idd, err = self.postconn.add_backlog(letter_info)
			letter_info["db_last_error"] = err
			letter_info["id"] = idd
			if idd > 0: #если прошло успешно
				letter_info["db_locked"] = LOCK_STATE_BACKLOG
			self.dbstorage.modify_letter(letter_info)
		#2. перенести из новых в пакет; создать пакет, если его нет
		if letter_info["db_locked"] == LOCK_STATE_BACKLOG:
			# если пакета нет
			if self.reestr_info["batch-name"] == "":
				batch_info, err = self.postconn.add_batch(self.reestr_info["list-number-date"], [letter_info["id"]])
				letter_info["db_last_error"] = err[letter_info["id"]]
				if letter_info["db_last_error"] > "":
					self.dbstorage.modify_letter(letter_info) #сохраняем ошибку
				#если добавление пакета прошло успешно
				if "batch-name" in batch_info:
					if letter_info["db_last_error"] == "":
						inf, err = self.postconn.get_backlog(letter_info["id"]) #получаем информацию о заказе
						letter_info["db_last_error"] = err
						if letter_info["db_last_error"] == "":
							letter_info["db_locked"] = LOCK_STATE_BATCH
							letter_info["barcode"] = inf["barcode"]
					self.dbstorage.modify_letter(letter_info)
					#сохраняем реестр
					self.reestr_info["batch-name"] = batch_info["batch-name"]
					self.reestr_info["db_locked"] = LOCK_STATE_BATCH
					self.dbstorage.modify_reestr(self.reestr_info)
			else: #если пакет есть
				#добавляем в пакет
				err = self.postconn.add_backlog_to_batch(self.reestr_info["batch-name"], letter_info["id"])
				if err > "":
					letter_info["db_last_error"] = err
				else:
					inf, err = self.postconn.get_backlog(letter_info["id"]) #получаем информацию о заказе
					letter_info["db_last_error"] = err
					if letter_info["db_last_error"] == "":
						letter_info["db_locked"] = LOCK_STATE_BATCH
						letter_info["barcode"] = inf["barcode"]
				self.dbstorage.modify_letter(letter_info)
	def barcode_del(self, letter_info):
		self.reestr_info, err = self.dbstorage.get_reestr_info(self.reestr_info["db_reestr_id"])
		if self.reestr_info["db_locked"] == LOCK_STATE_FINAL: return
		# удаляем письмо из новых
		for idd, err in self.postconn.remove_backlogs([letter_info["id"]]):
			linf = {"db_letter_id": letter_info["db_letter_id"], "db_locked": LOCK_STATE_FREE, "id": 0,
					"db_last_error": err, "barcode": "", "db_reestr_id": letter_info["db_reestr_id"]}
			self.dbstorage.modify_letter(linf)
		# удаляем письмо из пакетов
		for idd, err in self.postconn.remove_backlogs_from_shipment([letter_info["id"]]):
			linf = {"db_letter_id": letter_info["db_letter_id"], "db_locked": LOCK_STATE_FREE, "id": 0,
					"db_last_error": err, "barcode": "", "db_reestr_id": letter_info["db_reestr_id"]}
			self.dbstorage.modify_letter(linf)
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
			res = self.dbstorage.add_letter(letter_info)
			self.refresh()
		if command == "SAVE":
			res = self.dbstorage.modify_letter(letter_info)
			print(res)
			if res[0]:
				return True
			else:
				logging.error(res[1])
				return False
		if command == "PRINT":
			from_info = copy(defconf.FROM_INFO)
			from_info["fio"] = UserIdentifier(self.dbstorage.get_user_info(letter_info["db_user_id"])[0]).get_fio()
			os.startfile(render_DL_letters([letter_info], from_info))
		if command == "PRINT_ALL":
			lts = []
			for data, err in self.dbstorage.get_letters_list(self.reestr_info["db_reestr_id"]):
				if err == "":
					lts.append(data)
			from_info = copy(defconf.FROM_INFO)
			from_info["fio"] = UserIdentifier(self.dbstorage.get_user_info(self.reestr_info["db_user_id"])[0]).get_fio()
			os.startfile(render_DL_letters(lts, from_info))
		if command == "DELETE":
			self.dbstorage.delete_letter(letter_info)
			self.refresh()
		if command == "BARCODE_ADD":
			self.barcode_add(letter_info)
			self.reestr_info, err = self.dbstorage.get_reestr_info(self.reestr_info["db_reestr_id"])
			self.refresh()
		if command == "BARCODE_DEL":
			self.barcode_del(letter_info)
			self.reestr_info, err = self.dbstorage.get_reestr_info(self.reestr_info["db_reestr_id"])
			self.refresh()
		if command == "BARCODE_ADD_ALL":
			for data, err in self.dbstorage.get_letters_list(self.reestr_info["db_reestr_id"]):
				if err == "":
					if self.reestr_info["db_locked"] == LOCK_STATE_FINAL:
						data["db_locked"] = LOCK_STATE_FINAL
					self.barcode_add(data)
			self.reestr_info, err = self.dbstorage.get_reestr_info(self.reestr_info["db_reestr_id"])
			self.refresh()
		if command == "BARCODE_DEL_ALL":
			for data, err in self.dbstorage.get_letters_list(self.reestr_info["db_reestr_id"]):
				if err == "":
					if self.reestr_info["db_locked"] == LOCK_STATE_FINAL:
						data["db_locked"] = LOCK_STATE_FINAL
					self.barcode_del(data)
			self.reestr_info, err = self.dbstorage.get_reestr_info(self.reestr_info["db_reestr_id"])
			self.refresh()
		if command == "REFRESH":
			self.refresh()
