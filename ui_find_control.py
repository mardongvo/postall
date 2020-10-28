# -*- coding: utf-8 -*-
import Tkinter as tk

DEFAULT_WIDTH = 20

class UIFindControl(tk.Frame):
    """UI класс для разных операций в UIFindWindow
    """
    def __init__(self, master, action_callback=None):
        """
        
        :param master:
        :param action_callback:
        """
        tk.Frame.__init__(self, master)
        self.action_callback = action_callback
        #
        L1 = tk.Label(self, text = u"Получатель", width = -1)
        L1.grid({"column": 0, "row": 0, "sticky": "NSW"})
        self.entry_recipient = tk.Entry(self)
        self.entry_recipient.grid({"column": 1, "row": 0, "sticky": "NSW"})
        self.entry_recipient["width"] = DEFAULT_WIDTH        
        #кнопки
        self.btn_find = tk.Button(self, text=u"найти", command=self.onClickFind)
        self.btn_find.grid({"column": 2, "row": 0, "sticky": "NSEW"})
    def onClickFind(self):
        if self.action_callback:
            self.action_callback("FIND", self.entry_recipient.get())
