# -*- coding: utf-8 -*-

import Tkinter as tk
from datetime import datetime

DEFAULT_WIDTH = 20

class UIReestrAdd(tk.Frame):
    """UI класс для добавления реестра
    """
    def __init__(self, master, user_ident, action_callback=None):
        """
        
        :param master:
        :param user_ident: объект типа UserIdentifier
        :param action_callback:
        """
        self.GUI_DEF = [
            {'key': 'list-number-date', 'title': u'Дата отправки', 'type': 'date', 'edit': True, 'maxsize': 12,
             'row': 0},
            {'key': 'with-simple-notice', 'title': u'С уведомл.', 'type': 'bool', 'edit': True, 'maxsize': 10,
             'row': 0},
            {'key': 'no-return', 'title': u'Без возврата', 'type': 'bool', 'edit': True, 'maxsize': 10,
             'row': 0},
            {'key': 'db_comment', 'title': u'Комм.', 'type': 'text', 'edit': True, 'maxsize': 20, 'row': 0},
            {'key': 'fio', 'title': u'ФИО', 'type': 'text', 'edit': False, 'maxsize': 20, 'row': 0},
        ]
        tk.Frame.__init__(self, master)
        self.user_ident = user_ident
        self.action_callback = action_callback
        col = 0
        for c in self.GUI_DEF:
            if c['type']=='bool':
                c['var'] = tk.IntVar()
                wgt = tk.Checkbutton(self, text=c['title'], variable=c['var'])
                c['widget'] = wgt
                wgt.grid({"column": col, "row": 0, "sticky": "NSW"})
                col += 1
            else:
                L1 = tk.Label(self, text = c['title'], width=-1)
                L1.grid({"column":col, "row":0, "sticky":"NSW"})
                ent = tk.Entry(self)
                ent.grid({"column": col + 1, "row": 0, "sticky": "NSW"})
                if 'maxsize' in c:
                    ent["width"] = c['maxsize']
                else:
                    ent["width"] = DEFAULT_WIDTH
                #обработка особых случаев
                if c['type']=='date':
                    ent.insert("end", datetime.now().strftime("%d.%m.%Y"))
                if c['key']=='fio':
                    ent.insert("end", self.user_ident.get_fio())
                if not c['edit']:
                    ent.config(state='readonly')
                c['widget'] = ent
                col += 2
        #кнопки
        self.btn_add = tk.Button(self, text = u"Добавить", command=self.onClickAdd)
        self.btn_add.grid({"column":col+1, "row":0, "sticky":"NSEW"})
        self.btn_refresh = tk.Button(self, text=u"Обновить", command=self.onClickRefresh)
        self.btn_refresh.grid({"column": col + 2, "row": 0, "sticky": "NSEW"})
        self.btn_find = tk.Button(self, text=u"Найти письмо", command=self.onClickFind)
        self.btn_find.grid({"column": col + 3, "row": 0, "sticky": "NSEW"})
    def onClickAdd(self):
        if self.action_callback:
            reestr = {}
            for c in self.GUI_DEF:
                v = None
                if c['type']=='bool':
                    try:
                        v = c['var'].get()
                        v = True if v==1 else False
                    except Exception as e:
                        v = False
                        #TODO: log
                elif c['type']=='date':
                    try:
                        v = datetime.strptime(c['widget'].get(), "%d.%m.%Y")
                    except Exception as e:
                        v = datetime.now()
                        # TODO: log
                else:
                    v = c['widget'].get()
                reestr[c['key']] = v
            self.action_callback("ADD", reestr)
    def onClickRefresh(self):
        if self.action_callback:
            self.action_callback("REFRESH", None)
    def onClickFind(self):
        if self.action_callback:
            self.action_callback("FIND", None)
