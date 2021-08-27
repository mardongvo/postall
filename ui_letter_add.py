# -*- coding: utf-8 -*-

import Tkinter as tk
from copy import copy

DEFAULT_WIDTH = 20


class UILetterAdd(tk.Frame):
    """UI класс для добавления письма
    """

    def __init__(self, master, default_values={}, action_callback=None):
        """
        
        :param master:
        :param default_values: dict() - какие-либо значения для письма по-умолчанию
        :param action_callback:
        """
        tk.Frame.__init__(self, master)
        self.action_callback = action_callback
        self.default_values = default_values
        #
        L1 = tk.Label(self, text=u"Контрагент", width=-1)
        L1.grid({"column": 0, "row": 0, "sticky": "NSW"})
        self.entry_id = tk.Entry(self)
        self.entry_id.grid({"column": 1, "row": 0, "sticky": "NSW"})
        self.entry_id["width"] = DEFAULT_WIDTH
        # кнопки
        self.btn_add = tk.Button(self, text=u"Добавить", command=self.onClickAdd)
        self.btn_add.grid({"column": 2, "row": 0, "sticky": "NSEW"})

    def onClickAdd(self):
        if self.action_callback:
            letter_info = copy(self.default_values)
            contragent_info = {"srctype": 0, "srcid": self.entry_id.get()}
            self.action_callback("ADD", letter_info, contragent_info)
            self.action_callback("REFRESH", {}, {})
