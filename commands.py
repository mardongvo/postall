# -*- coding: utf-8 -*-

import configuration as defconf
import logging
from dbstorage import LOCK_STATE_FINAL, LOCK_STATE_FREE, LOCK_STATE_BACKLOG, LOCK_STATE_BATCH
from user_identifier import UserIdentifier

def barcode_add(dbstorage, postconn, reestr_info, letter_info):
	""" Добавление письма в кабинете сначала в новые, а потом в пакет
	
	:param reestr_info:
	:param letter_info:
	:return:
	"""
	reestr_info, err = dbstorage.get_reestr_info(reestr_info["db_reestr_id"])
	if err > "":
		logging.error("Commands:barcode_add::get_reestr_info>>"+err)
		return
	#если реестр заблокирован, ничего не делаем
	if reestr_info["db_locked"] == LOCK_STATE_FINAL: return
	#1. необходимо добавить письмо в новые
	if letter_info["db_locked"] == LOCK_STATE_FREE:
		#копируем постоянные поля
		for k, v in defconf.LETTER_CONSTANT_FIELDS.iteritems():
			letter_info[k] = v
		#!!!
		#комментарий к отправлению должен быть - <ФИО>, <комментарий из письма>
		uinf, err = dbstorage.get_user_info(letter_info["db_user_id"])
		if err > "":
			logging.error("Commands:barcode_add::get_user_info>>"+err)
		letter_info["order-num"] = UserIdentifier(uinf).get_fio() + u", " + letter_info["comment"]
		#добавление в "новые" в кабинете
		idd, err = postconn.add_backlog(letter_info)
		if err > "":
			logging.error("Commands:barcode_add::add_backlog>>"+err)
		letter_info["db_last_error"] = err
		letter_info["id"] = idd
		if idd > 0: #если добавление в новые прошло успешно
			letter_info["db_locked"] = LOCK_STATE_BACKLOG
		res, err = dbstorage.modify_letter(letter_info)
		if err > "":
			logging.error("Commands:barcode_add::modify_letter>>" + err)
	#2. перенести из новых в пакет; создать пакет, если его нет
	if letter_info["db_locked"] == LOCK_STATE_BACKLOG:
		# если пакета нет - пытаемся создать новый
		if reestr_info["batch-name"] == "":
			batch_info, err = postconn.add_batch(reestr_info["list-number-date"], [letter_info["id"]])
			if err > "":
				logging.error("Commands:barcode_add::add_batch>>" + err)
			letter_info["db_last_error"] = err[letter_info["id"]]
			if letter_info["db_last_error"] > "":
				res, err = dbstorage.modify_letter(letter_info) #сохраняем ошибку
				if err > "":
					logging.error("Commands:barcode_add::modify_letter>>" + err)
			#если добавление пакета прошло успешно
			if "batch-name" in batch_info:
				if letter_info["db_last_error"] == "":
					inf, err = postconn.get_backlog(letter_info["id"]) #получаем информацию о заказе
					if err > "":
						logging.error("Commands:barcode_add::get_backlog>>" + err)
					letter_info["db_last_error"] = err
					if letter_info["db_last_error"] == "":
						letter_info["db_locked"] = LOCK_STATE_BATCH
						letter_info["barcode"] = inf["barcode"]
				res, err = dbstorage.modify_letter(letter_info)
				if err > "":
					logging.error("Commands:barcode_add::modify_letter>>" + err)
				#сохраняем реестр
				reestr_info["batch-name"] = batch_info["batch-name"]
				reestr_info["db_locked"] = LOCK_STATE_BATCH
				res, err = dbstorage.modify_reestr(reestr_info)
				if err > "":
					logging.error("Commands:barcode_add::modify_reestr>>" + err)
		else: #если пакет уже есть
			#добавляем в пакет
			err = postconn.add_backlog_to_batch(reestr_info["batch-name"], letter_info["id"])
			if err > "":
				letter_info["db_last_error"] = err
				logging.error("Commands:barcode_add::add_backlog_to_batch>>" + err)
			else:
				# получаем информацию о заказе, чтобы сохранить штрих-код
				inf, err = postconn.get_backlog(letter_info["id"])
				letter_info["db_last_error"] = err
				if err > "":
					logging.error("Commands:barcode_add::get_backlog>>" + err)
				else:
					letter_info["db_locked"] = LOCK_STATE_BATCH
					letter_info["barcode"] = inf["barcode"]
			res, err = dbstorage.modify_letter(letter_info)
			if err > "":
				logging.error("Commands:barcode_add::modify_reestr>>" + err)

def barcode_del(dbstorage, postconn, reestr_info, letter_info):
	""" Удаление письма с сайта
	
	:param reestr_info:
	:param letter_info:
	:return:
	"""
	reestr_info, err = dbstorage.get_reestr_info(reestr_info["db_reestr_id"])
	if err > "":
		logging.error("Commands:barcode_del::get_reestr_info>>" + err)
		return
	if reestr_info["db_locked"] == LOCK_STATE_FINAL: return
	# удаляем письмо из новых
	#TODO: сделать надежное удаление
	for idd, err in postconn.remove_backlogs([letter_info["id"]]):
		#TODO: возможны ли ситуации, в которых письмо с сайта не удаляется?
		linf = {"db_letter_id": letter_info["db_letter_id"], "db_locked": LOCK_STATE_FREE, "id": 0,
				"db_last_error": err, "barcode": "", "db_reestr_id": letter_info["db_reestr_id"]}
		if err > "":
			logging.error("Commands:barcode_del::remove_backlogs>>" + err)
		res, err = dbstorage.modify_letter(linf)
		if err > "":
			logging.error("Commands:barcode_del::modify_letter>>" + err)
	# удаляем письмо из пакетов
	for idd, err in postconn.remove_backlogs_from_shipment([letter_info["id"]]):
		# TODO: возможны ли ситуации, в которых письмо с сайта не удаляется?
		linf = {"db_letter_id": letter_info["db_letter_id"], "db_locked": LOCK_STATE_FREE, "id": 0,
				"db_last_error": err, "barcode": "", "db_reestr_id": letter_info["db_reestr_id"]}
		if err > "":
			logging.error("Commands:barcode_del::remove_backlogs_from_shipment>>" + err)
		res, err = dbstorage.modify_letter(linf)
		if err > "":
			logging.error("Commands:barcode_del::modify_letter>>" + err)

def set_date(dbstorage, postconn, reestr_info, batch_date):
	""" Установить дату реестра. Если реестр уже есть на сайте, то и на сайте
	
	:param reestr_info:
	:param batch_date: дата в виде datetime/date
	:return:
	"""
	reestr_info["list-number-date"] = batch_date
	if reestr_info["db_locked"] == LOCK_STATE_BATCH: #если реестр выгружен
		err = postconn.modify_batch(reestr_info["batch-name"], reestr_info["list-number-date"])
		if err > "":
			logging.error("Commands:set_date::modify_batch>>" + err)
		else:
			res, err = dbstorage.modify_reestr(reestr_info)
			if err > "":
				logging.error("Commands:set_date::modify_reestr>>" + err)
	if reestr_info["db_locked"] == LOCK_STATE_FREE:
		err = dbstorage.modify_reestr(reestr_info)
		if err > "":
			logging.error("Commands:set_date::modify_reestr>>" + err)

def barcode_add_all(dbstorage, postconn, reestr_info, user_ident):
	for data, err in dbstorage.get_letters_list(reestr_info["db_reestr_id"]):
		if err == "":
			if (reestr_info["db_locked"] == LOCK_STATE_FINAL) or \
					(user_ident.get_user_id() != data["db_user_id"] and user_ident.is_admin() == 0):
				data["db_locked"] = LOCK_STATE_FINAL
			barcode_add(dbstorage, postconn, reestr_info, data)
		else:
			logging.error("Commands:barcode_add_all::get_letters_list>>" + err)

def barcode_del_all(dbstorage, postconn, reestr_info, user_ident):
	for data, err in dbstorage.get_letters_list(reestr_info["db_reestr_id"]):
		if err == "":
			if (reestr_info["db_locked"] == LOCK_STATE_FINAL) or \
					(user_ident.get_user_id() != data["db_user_id"] and user_ident.is_admin() == 0):
				data["db_locked"] = LOCK_STATE_FINAL
			barcode_del(dbstorage, postconn, reestr_info, data)
		else:
			logging.error("Commands:barcode_add_all::get_letters_list>>" + err)

