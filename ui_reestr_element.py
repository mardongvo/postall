# -*- coding: utf-8 -*-

import Tkinter as tk
import copy
from dbstorage import LOCK_STATE_FREE, LOCK_STATE_BACKLOG, LOCK_STATE_BATCH, LOCK_STATE_FINAL
from datetime import datetime, date
import logging

DEFAULT_WIDTH = 20

# цвета фона для различия позиций в списке
COLORS = (
    ("#cccdff", "#7e80c9"),
    ("#ffc9c9", "#c97e7e")
)


class UIReestrElement(tk.Frame):
    """UI класс представления реестра
    """

    def __init__(self, master, user_ident, bgcolor=0, action_callback=None):
        self.GUI_DEF = [
            {'key': 'db_reestr_id', 'title': u'Номер', 'type': 'text', 'edit': False, 'maxsize': 10, 'row': 0},
            {'key': 'db_create_date', 'title': u'Дата создания', 'type': 'date', 'edit': False, 'maxsize': 12,
             'row': 0},
            {'key': 'batch-name', 'title': u'Номер(сайт)', 'type': 'text', 'edit': False, 'maxsize': 10, 'row': 1},
            {'key': 'list-number-date', 'title': u'Дата отправки', 'type': 'date', 'edit': True, 'maxsize': 12,
             'row': 1},
            {'key': 'db_letter_count', 'title': u'Кол-во', 'type': 'integer', 'edit': False, 'maxsize': 10, 'row': 0},
            {'key': 'with-simple-notice', 'title': u'С уведомл.', 'type': 'bool', 'edit': False, 'maxsize': 10,
             'row': 1},
            {'key': 'mail-category', 'title': u'Катег.', 'type': 'text', 'edit': False, 'maxsize': 10, 'row': 0},
            {'key': 'no-return', 'title': u'Без возврата', 'type': 'bool', 'edit': False, 'maxsize': 10,
             'row': 1},
            {'key': 'envelope-type', 'title': u'Конверт', 'type': 'text', 'edit': False, 'maxsize': 10, 'row': 0},
            {'key': 'payment-method', 'title': u'Оплата', 'type': 'text', 'edit': False, 'maxsize': 10, 'row': 1},
            {'key': 'db_comment', 'title': u'Комм.', 'type': 'text', 'edit': False, 'maxsize': 20, 'row': 0},
            {'key': 'fio', 'title': u'ФИО', 'type': 'text', 'edit': False, 'maxsize': 20, 'row': 1},
        ]
        self.reestr_info = {}
        self.action_callback = action_callback
        self.user_ident = user_ident
        # create widgets
        tk.Frame.__init__(self, master)
        self["bg"] = COLORS[bgcolor][0]
        ##########
        gridcol = {}
        for i in map(lambda a: a['row'], self.GUI_DEF):
            gridcol[i] = 0
        for c in self.GUI_DEF:
            col = gridcol[c['row']]
            L1 = tk.Label(self, text=c['title'])
            L1.grid({"column": col, "row": c['row'], "sticky": "NSW"})
            L1["width"] = -1
            L1["bg"] = COLORS[bgcolor][0]
            ent = tk.Entry(self)
            # ent["background"] = COLORS[bgcolor][1]
            ent["readonlybackground"] = COLORS[bgcolor][0]
            if not c['edit']:
                ent.config(state='readonly')
            ent.grid({"column": col + 1, "row": c['row'], "sticky": "NSW"})
            if 'maxsize' in c:
                ent["width"] = c['maxsize']
            else:
                ent["width"] = DEFAULT_WIDTH
            c['widget'] = ent
            gridcol[c['row']] += 2
        # кнопки
        # редактирование
        self.btn_edit = tk.Button(self, text=u"Редактировать", command=self.onClickEdit, bg=COLORS[bgcolor][0])
        self.btn_edit.grid({"column": max(gridcol.values()) + 1, "row": 0, "sticky": "NSEW"})
        # удаление
        self.btn_delete = tk.Button(self, text=u"Удалить", command=self.onClickDelete, bg=COLORS[bgcolor][0])
        self.btn_delete.grid({"column": max(gridcol.values()) + 2, "row": 0, "sticky": "NSEW"})
        # дата отправки
        self.btn_date = tk.Button(self, text=u"Изменить дату отправки", command=self.onClickDate, bg=COLORS[bgcolor][0])
        self.btn_date.grid({"column": max(gridcol.values()) + 1, "row": 1, "sticky": "NSEW"})
        # заблокиировать
        self.btn_lock = tk.Button(self, text=u"Заблокировать окончательно", command=self.onClickLock,
                                  bg=COLORS[bgcolor][0])
        self.btn_lock.grid({"column": max(gridcol.values()) + 2, "row": 1, "sticky": "NSEW"})

    def set_data(self, reestr_info):
        """ Скопировать данные реестра, заполнить entry
        """
        self.reestr_info = copy.copy(reestr_info)
        for c in self.GUI_DEF:
            c["widget"].config(state='normal')  # необходимо для редактирования
            c["widget"].delete(0, "end")
            if c["key"] in self.reestr_info:
                v = self.reestr_info[c["key"]]
                if isinstance(v, bool):
                    v = u'Да' if v else u'Нет'
                if isinstance(v, int):
                    v = str(v)
                if isinstance(v, datetime) or isinstance(v, date):
                    v = v.strftime("%d.%m.%Y")
                c["widget"].insert("end", v)
                # для реестра с уведомлением особое выделение
                if (c["key"] == 'with-simple-notice') and self.reestr_info[c["key"]]:
                    c["widget"]["readonlybackground"] = "#FF0000"
                # для реестра без галки "без возврата"
                if (c["key"] == 'no-return') and not self.reestr_info[c["key"]]:
                    c["widget"]["readonlybackground"] = "#FF0000"
                if (c["key"] == 'envelope-type') and (self.reestr_info[c["key"]] != 'DL'):
                    c["widget"]["readonlybackground"] = "#00FF00"
                if (c["key"] == 'payment-method') and (self.reestr_info[c["key"]] != 'STAMP'):
                    c["widget"]["readonlybackground"] = "#00FF00"
            if not c["edit"]:
                c["widget"].config(state='readonly')
        self.set_lock(self.reestr_info["db_locked"])

    def set_lock(self, lock_state):
        """ Установить доступность элементов согласно статусу блокировки
        """
        self.btn_edit["state"] = "disabled"
        self.btn_date["state"] = "disabled"
        self.btn_lock["state"] = "disabled"
        self.btn_delete["state"] = "disabled"
        if self.user_ident.is_admin() == 1:
            self.btn_lock["state"] = "normal"
        for c in self.GUI_DEF:
            c["widget"].config(state='readonly')
        if lock_state == LOCK_STATE_FREE:
            self.btn_edit["state"] = "normal"
            self.btn_date["state"] = "normal"
            self.btn_delete["state"] = "normal"
            for c in self.GUI_DEF:
                if c["edit"]:
                    c["widget"].config(state='normal')
        if lock_state == LOCK_STATE_BATCH:
            self.btn_edit["state"] = "normal"
            # при оплате знаками онлайн оплаты дата прописывается в QR коде,
            # поэтому оставляем изменение даты, если это марки
            if self.reestr_info['payment-method'] == 'STAMP':
                self.btn_date["state"] = "normal"
            for c in self.GUI_DEF:
                if c["edit"]:
                    c["widget"].config(state='normal')
        if lock_state == LOCK_STATE_FINAL:
            self.btn_edit["state"] = "normal"
            self.btn_edit["text"] = u'Просмотр'
            self.btn_lock["state"] = "disabled"

    def sync(self):
        """ Перенсит данные из формы в reestr_info
        Пока только дата отправки
        """
        for c in self.GUI_DEF:
            if c["key"] == 'list-number-date':
                try:
                    v = datetime.strptime(c["widget"].get(), "%d.%m.%Y")
                    self.reestr_info[c["key"]] = v
                except ValueError:
                    logging.error(u"Невозможно установить дату %s", c["widget"].get())

    def onClickDate(self):
        self.sync()
        if self.action_callback:
            self.action_callback("DATE", self.reestr_info)

    def onClickLock(self):
        if self.action_callback:
            self.action_callback("LOCK", self.reestr_info)

    def onClickDelete(self):
        if self.action_callback:
            self.action_callback("DELETE", self.reestr_info)

    def onClickEdit(self):
        if self.action_callback:
            self.action_callback("EDIT", self.reestr_info)
