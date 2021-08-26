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
from envelope_render_C5 import render_C5_letters
from notification_render import render_notifications
import commands
import os
from copy import copy
import configuration as defconf
import logging

class UIEditWindow(tk.Frame):
    """UI класс главное окно
    """

    def __init__(self, master, postconn, dbstorage, user_ident, reestr_info, use_daemon):
        #
        self.postconn = postconn
        self.dbstorage = dbstorage
        self.user_ident = user_ident
        self.use_daemon = use_daemon
        self.rowcount = 0
        self.reestr_info = reestr_info
        self.render_letters = render_DL_letters
        if self.reestr_info["envelope-type"] == "C5":
            self.render_letters = render_C5_letters
        #
        tk.Frame.__init__(self, master)
        self.ui_ctl = UILetterControl(self, action_callback=self.action_letter)
        self.ui_ctl.config(bd=5, relief=tk.GROOVE)
        self.ui_ctl.pack(side=tk.TOP, fill=tk.X)
        self.ui_add = UILetterAdd(self,
                                  default_values={"db_mass_pages": 1,
                                                  "mass": 20,
                                                  "db_locked": LOCK_STATE_FREE,
                                                  "db_user_id": self.user_ident.get_user_id(),
                                                  "db_reestr_id": self.reestr_info["db_reestr_id"],
                                                  "with-simple-notice": self.reestr_info["with-simple-notice"],
                                                  "no-return": self.reestr_info["no-return"],
                                                  "mail-category": self.reestr_info["mail-category"],
                                                  "envelope-type": self.reestr_info["envelope-type"],
                                                  "payment-method": self.reestr_info["payment-method"],
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
        self.reestr_info, err = self.dbstorage.get_reestr_info(self.reestr_info["db_reestr_id"])
        if err == "":
            self.master.wm_title(u"Реестр №%s (сайт: %s) от %s%s" %
                                 (self.reestr_info["db_reestr_id"],
                                  self.reestr_info["batch-name"],
                                  self.reestr_info["db_create_date"].strftime("%d.%m.%Y"),
                                  " (ЗАБЛОКИРОВАН)" if self.reestr_info["db_locked"] == LOCK_STATE_FINAL else ""))
        else:
            logging.error(err)

    def refresh(self):
        # TODO: оптимизировать обновление списка
        self.update_title()
        self.rowcount = 0
        self.ui_scrollarea.clear()
        for data, err in self.dbstorage.get_letters_list(self.reestr_info["db_reestr_id"]):
            if err == "":
                uu = UILetter(self.ui_scrollarea.frame, self.rowcount % 2, self.action_letter)
                # если реестр заблокирован или это чужое письмо, передаем это письмам,
                # чтобы не возникало ложного ощущения, что можно редактировать
                if (self.reestr_info["db_locked"] == LOCK_STATE_FINAL) or \
                        (self.user_ident.get_user_id() != data["db_user_id"] and self.user_ident.is_admin() == 0):
                    data["db_locked"] = LOCK_STATE_FINAL
                uu.set_data(data)
                uu.pack(side=tk.TOP, fill=tk.X, expand=False)
                self.rowcount += 1
            else:
                logging.error(err)

    def letter_iterator(self, user_id=None):
        """ Итератор по письмам реестра. Используется в выводе печатной формы
        
        :param user_id: string/None значение db_user_id, если требуется
        отфильтровать письма по пользователю. None отключает фильтрацию
        :return:
        """
        for data, err in self.dbstorage.get_letters_list(
                self.reestr_info["db_reestr_id"]):
            if err != "":
                logging.error(err)
                continue
            # FAIL POST
            # if data["db_locked"] != LOCK_STATE_BATCH:
            #    continue
            if (user_id is not None) and (data["db_user_id"] != user_id):
                continue
            from_info = copy(defconf.FROM_INFO)
            uinf, err = self.dbstorage.get_user_info(data["db_user_id"])
            if err > "":
                logging.error(err)
            from_info["fio"] = UserIdentifier(uinf).get_fio()
            data["list-number-date"] = self.reestr_info["list-number-date"]
            yield data, from_info

    def action_letter(self, command, letter_info, contagent_info={}):
        """ Callback функция для обработки действий в форме добавления и в письме
        
        :param command:
        :param letter_info:
        :param contagent_info:
        :return:
        """
        if command == "ADD":
            cinfo, err = self.dbstorage.get_contragent_info(contagent_info["srctype"], contagent_info["srcid"])
            if err > "":
                logging.error(err)
            if cinfo is not None:
                for k, v in cinfo.iteritems():
                    letter_info[k] = v
            res = self.dbstorage.add_letter(letter_info)
            self.refresh()
        if command == "SAVE":
            res, err = self.dbstorage.modify_letter(letter_info)
            if res:
                return True
            else:
                logging.error(err)
                return False
        if command == "PRINT":
            from_info = copy(defconf.FROM_INFO)
            uinf, err = self.dbstorage.get_user_info(letter_info["db_user_id"])
            if err > "":
                logging.error(err)
            from_info["fio"] = UserIdentifier(uinf).get_fio()
            letter_info["list-number-date"] = self.reestr_info["list-number-date"]
            os.startfile(self.render_letters([(letter_info, from_info)].__iter__()))
        if command == "PRINT_ALL":
            os.startfile(self.render_letters(self.letter_iterator()))
        if command == "PRINT_MY":
            os.startfile(self.render_letters(self.letter_iterator(
                self.user_ident.get_user_id())
            )
            )
        if command == "PRINT_NOTIFICATIONS":
            os.startfile(render_notifications(self.letter_iterator()))
        if command == "DELETE":
            res, err = self.dbstorage.delete_letter(letter_info)
            if err > "":
                logging.error(err)
            self.refresh()
        if command == "BARCODE_ADD":
            if self.use_daemon:
                self.dbstorage.add_command({"command": "BARCODE_ADD", "db_reestr_id": letter_info["db_reestr_id"],
                                            "db_letter_id": letter_info["db_letter_id"],
                                            "db_user_id": self.user_ident.get_user_id()})
            else:
                commands.barcode_add(self.dbstorage, self.postconn, self.reestr_info, letter_info)
            self.reestr_info, err = self.dbstorage.get_reestr_info(self.reestr_info["db_reestr_id"])
            if err > "":
                logging.error(err)
            self.refresh()
        if command == "BARCODE_DEL":
            if self.use_daemon:
                self.dbstorage.add_command({"command": "BARCODE_DEL", "db_reestr_id": letter_info["db_reestr_id"],
                                            "db_letter_id": letter_info["db_letter_id"],
                                            "db_user_id": self.user_ident.get_user_id()})
            else:
                commands.barcode_del(self.dbstorage, self.postconn, self.reestr_info, letter_info)
            self.reestr_info, err = self.dbstorage.get_reestr_info(self.reestr_info["db_reestr_id"])
            if err > "":
                logging.error(err)
            self.refresh()
        if command == "BARCODE_ADD_ALL":
            if self.use_daemon:
                self.dbstorage.add_command({"command": "BARCODE_ADD_ALL", "db_reestr_id": letter_info["db_reestr_id"],
                                            "db_user_id": self.user_ident.get_user_id()})
            else:
                commands.barcode_add_all(self.dbstorage, self.postconn, self.reestr_info, self.user_ident)
            self.reestr_info, err = self.dbstorage.get_reestr_info(self.reestr_info["db_reestr_id"])
            if err > "":
                logging.error(err)
            self.refresh()
        if command == "BARCODE_DEL_ALL":
            if self.use_daemon:
                self.dbstorage.add_command({"command": "BARCODE_DEL_ALL", "db_reestr_id": letter_info["db_reestr_id"],
                                            "db_user_id": self.user_ident.get_user_id()})
            else:
                commands.barcode_del_all(self.dbstorage, self.postconn, self.reestr_info, self.user_ident)
            self.reestr_info, err = self.dbstorage.get_reestr_info(self.reestr_info["db_reestr_id"])
            if err > "":
                logging.error(err)
            self.refresh()
        if command == "POSTINDEX":
            pinf, err = self.dbstorage.get_postindex_info(letter_info["postindex"])
            if err > "":
                logging.error(err)
            else:
                return pinf
        if command == "REFRESH":
            self.refresh()
