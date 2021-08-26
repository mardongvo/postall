# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import Tkinter as tk
from ui_scrollframe import UIScrollFrame
from ui_letter_view import UILetterView
from ui_find_control import UIFindControl
import configuration as defconf
import logging


class UIFindWindow(tk.Frame):
    """UI класс главное окно
    """

    def __init__(self, master, dbstorage):
        #
        self.dbstorage = dbstorage
        self.rowcount = 0
        #
        tk.Frame.__init__(self, master)
        self.ui_ctl = UIFindControl(self, action_callback=self.action_find)
        self.ui_ctl.config(bd=5, relief=tk.GROOVE)
        self.ui_ctl.pack(side=tk.TOP, fill=tk.X)
        self.ui_scrollarea = UIScrollFrame(self)
        self.ui_scrollarea.config(bd=5, relief=tk.GROOVE)
        self.ui_scrollarea.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def action_find(self, command, recipient_info):
        """ Callback функция для обработки действий в форме
        
        :param command:
        :param recipient_info:
        :return:
        """
        if command == "FIND":
            self.ui_scrollarea.clear()
            lvinfo = self.dbstorage.find_letters(recipient_info)
            for data, err in lvinfo:
                if err != "":
                    logging.error(err)
                    continue
                uu = UILetterView(self.ui_scrollarea.frame, self.rowcount % 2, None)
                uu.set_data(data)
                uu.pack(side=tk.TOP, fill=tk.X, expand=False)
                self.rowcount += 1
