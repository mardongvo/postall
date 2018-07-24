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
from os.path import join

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)

conn = psycopg2.connect(defconf.DB_CONNECTION)
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
db.add_field_map("POSTINDEX", defconf.POSTINDEX_DB_FIELDS)
if defconf.USE_DAEMON:
	db.add_field_map("COMMAND_QUEUE", defconf.COMMAND_DB_FIELDS)

sess = requests.session()
#в случае bundled приложения (py2exe,pyInstaller) есть атрибут frozen в sys
#и требуется указать хранилище сертификатов для правильной работы HTTPS
#при установленном requests хранилище находится в папке бибилиотеки
if getattr(sys, "frozen", False):
	sess.verify = join(os.getcwd(),"cacert.pem") #необходимо для проверок сертификатов https

pc = PostConnector(sess)
pc.set_parameters(token=defconf.ACCESS_TOKEN, login_password=defconf.LOGIN_PASSWORD, proxyurl=defconf.PROXY_URL)

root = Tk()
uinf, err = db.get_user_info(os.environ['USERNAME'])
if err > "":
	logging.error(err)
if (err > "") or len(uinf)==0:
	uinf = {"db_user_id":os.environ['USERNAME'], "fio":"", "is_admin":0}
uid = UserIdentifier(uinf)

app = UIMainWindow(root, pc, db, uid, defconf.USE_DAEMON)
app.pack(fill="both", expand=True)
app.refresh()
root.wm_title(u"ПОЧТА")
app.mainloop()

conn.close()