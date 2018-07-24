# -*- coding: utf-8 -*-

from user_identifier import UserIdentifier
import commands
import logging
from time import sleep

from multiprocessing.dummy import Pool

def dowork(dbstorage, postconn, command):
	if command["command"]=="BARCODE_ADD":
		reestr_info, err = dbstorage.get_reestr_info(command["db_reestr_id"])
		if err > "":
			logging.error("Daemon::dowork::BARCODE_ADD::get_reestr_info>>" + err)
			return
		letter_info, err = dbstorage.get_letter_info(command["db_letter_id"])
		if err > "":
			logging.error("Daemon::dowork::BARCODE_ADD::get_letter_info>>" + err)
			return
		commands.barcode_add(dbstorage, postconn, reestr_info, letter_info)
		res, err = dbstorage.delete_command(command)
		if err > "":
			logging.error("Daemon::dowork::BARCODE_ADD::delete_command>>" + err)
	if command["command"]=="BARCODE_ADD_ALL":
		reestr_info, err = dbstorage.get_reestr_info(command["db_reestr_id"])
		if err > "":
			logging.error("Daemon::dowork::BARCODE_ADD_ALL::get_reestr_info>>" + err)
			return
		uinf, err = dbstorage.get_user_info(command["db_user_id"])
		if err > "":
			logging.error("Daemon::dowork::BARCODE_ADD_ALL::get_user_info>>" + err)
			return
		user_ident = UserIdentifier(uinf)
		commands.barcode_add_all(dbstorage, postconn, reestr_info, user_ident)
		res, err = dbstorage.delete_command(command)
		if err > "":
			logging.error("Daemon::dowork::BARCODE_ADD::delete_command>>" + err)
	if command["command"] == "BARCODE_DEL":
		reestr_info, err = dbstorage.get_reestr_info(command["db_reestr_id"])
		if err > "":
			logging.error("Daemon::dowork::BARCODE_DEL::get_reestr_info>>" + err)
			return
		letter_info, err = dbstorage.get_letter_info(command["db_letter_id"])
		if err > "":
			logging.error("Daemon::dowork::BARCODE_DEL::get_letter_info>>" + err)
			return
		commands.barcode_del(dbstorage, postconn, reestr_info, letter_info)
		res, err = dbstorage.delete_command(command)
		if err > "":
			logging.error("Daemon::dowork::BARCODE_DEL::delete_command>>" + err)
	if command["command"] == "BARCODE_DEL_ALL":
		reestr_info, err = dbstorage.get_reestr_info(command["db_reestr_id"])
		if err > "":
			logging.error("Daemon::dowork::BARCODE_DEL_ALL::get_reestr_info>>" + err)
			return
		uinf, err = dbstorage.get_user_info(command["db_user_id"])
		if err > "":
			logging.error("Daemon::dowork::BARCODE_DEL_ALL::get_user_info>>" + err)
			return
		user_ident = UserIdentifier(uinf)
		commands.barcode_del_all(dbstorage, postconn, reestr_info, user_ident)
		res, err = dbstorage.delete_command(command)
		if err > "":
			logging.error("Daemon::dowork::BARCODE_DEL_ALL::delete_command>>" + err)
	if command["command"] == "DATE":
		reestr_info, err = dbstorage.get_reestr_info(command["db_reestr_id"])
		if err > "":
			logging.error("Daemon::dowork::DATE::get_reestr_info>>" + err)
			return
		commands.set_date(dbstorage, postconn, reestr_info, command["reestr_date"])
		res, err = dbstorage.delete_command(command)
		if err > "":
			logging.error("Daemon::dowork::DATE::delete_command>>" + err)

def daemon_mainloop(dbstorage, postconn, poolsize=10):
	work_pool = Pool(poolsize)
	commands_in_process = set()
	do_main_loop = True
	#main cycle
	while do_main_loop:
		try:
			curr_commands = set()
			for cmd, err in dbstorage.get_command_list():
				if err == "":
					curr_commands.add(cmd["uid"])
					if cmd["uid"] not in commands_in_process: #предотвращаем повторную обработку команды
						work_pool.apply_async(dowork, (dbstorage, postconn, cmd))
						commands_in_process.add(cmd["uid"])
				else:
					logging.error("Daemon::main_loop::get_command_list>>"+err)
			commands_in_process = curr_commands
		except Exception:
			pass
		sleep(1)