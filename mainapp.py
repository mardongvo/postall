# -*- coding: utf-8 -*-
from Tkinter import Tk
import sys
import psycopg2
import requests

from ui_main_window import UIMainWindow
from user_identifier import UserIdentifier
from dbstorage import DBStorage
from postconnector import PostConnector
import configuration as defconf
import logging
import os
from copy import copy

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)

conn = psycopg2.connect("host=127.0.0.1 user=postgres dbname=postall")
db = DBStorage(conn)
# инициализация информации о таблицах
db.add_field_map("REESTR_INFO", defconf.REESTR_DB_FIELDS)
db.add_field_map("LETTER_INFO", defconf.LETTER_DEFAULT)
db.add_field_map("LETTER_INFO", defconf.LETTER_DB_FIELDS)
db.add_field_map("USER_DICT", defconf.USER_DB_FIELDS)
contragent_struct = copy(defconf.CONTRAGENT_DB_FIELDS)
for k,v in defconf.LETTER_DEFAULT.iteritems():
	if k.endswith("-to"):
		contragent_struct[k] = v
db.add_field_map("CONTRAGENT_DICT", contragent_struct)

pc = PostConnector(requests.Session())
pc.set_parameters(token=defconf.ACCESS_TOKEN, login_password=defconf.LOGIN_PASSWORD, proxyurl=None)

root = Tk()
uinf, err = db.get_user_info(os.environ['USERNAME'])
if err > "":
	logging.error(err)
	uinf = {}
uid = UserIdentifier(uinf)

app = UIMainWindow(root, pc, db, uid)
app.pack(fill="both", expand=True)
app.refresh()
root.wm_title(u"ПОЧТА")
app.mainloop()

conn.close()