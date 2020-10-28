# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import Tkinter as tk
import copy

BG_COLOR = "FFFFFF"
DEFAULT_WIDTH = 20
ERROR_BG = "#d271ff"

#цвета фона для различия позиций в списке
COLORS = (
    ("#cccdff", "#7e80c9"),
    ("#ffc9c9", "#c97e7e")
)

class UILetterView(tk.Frame):
    """UI класс представления письма в виде горизонтальной области в несколько строк
    """
    
    def __init__(self, master, bgcolor=0, action_callback=None):
        self.GUI_DEF = [
            {'key': 'barcode', 'title': u'Номер', 'type': 'text', 'edit': False, 'maxsize': 14, 'row': 0},
            {'key': 'index-to', 'title': u'Индекс', 'type': 'integer', 'edit': False, 'maxsize': 6, 'row': 0},
            {'key': 'region-to', 'title': u'Обл.', 'type': 'text', 'edit': False, 'maxsize': 20, 'row': 0},
            {'key': 'place-to', 'title': u'Город', 'type': 'text', 'edit': False, 'maxsize': 15, 'row': 0},
            {'key': 'street-to', 'title': u'Улица', 'type': 'text', 'edit': False, 'maxsize': 20, 'row': 0},
            {'key': 'house-to', 'title': u'Дом', 'type': 'text', 'edit': False, 'maxsize': 6, 'row': 0},
            {'key': 'room-to', 'title': u'Кв./офис', 'type': 'text', 'edit': False, 'maxsize': 6, 'row': 0},
            {'key': 'recipient-name', 'title': u'Адресат', 'type': 'text', 'edit': False, 'maxsize': 20, 'row': 1},
            {'key': 'mass', 'title': u'Масса', 'type': 'integer', 'edit': False, 'maxsize': 6, 'row': 1},
            {'key': 'db_mass_pages', 'title': u'Листов', 'type': 'integer', 'edit': False, 'maxsize': 6, 'row': 1},
            {'key': 'comment', 'title': u'Содерж.', 'type': 'text', 'edit': False, 'maxsize': 20, 'row': 1},
            {'key': 'db_last_error', 'title': u'Ошибка', 'type': 'text', 'edit': False, 'maxsize': 30, 'row': 2},
            {'key': 'db_user_id', 'title': u'Польз.', 'type': 'text', 'edit': False, 'maxsize': 10, 'row': 2},
            {'key': 'db_create_date', 'title': u'Дата', 'type': 'text', 'edit': False, 'maxsize': 10, 'row': 2},
        ]
        self.letter_info = {}
        self.action_callback = action_callback
        #create widgets
        tk.Frame.__init__(self, master)
        self["bg"] = COLORS[bgcolor][0]
        #self.pack(fill="both", expand=True)
        gridcol = {}
        for i in map(lambda a: a['row'], self.GUI_DEF):
            gridcol[i] = 2
        for c in self.GUI_DEF:
            col = gridcol[c['row']]
            if c['key'] == 'barcode': #исключение для номера отправления
                col = 0
            L1 = tk.Label(self, text = c['title'])
            L1.grid({"column":col, "row":c['row'], "sticky":"NSW"})
            L1["width"] = -1
            L1["bg"] = COLORS[bgcolor][0]
            ent = tk.Entry(self)
            ent["background"] = COLORS[bgcolor][0]
            ent["readonlybackground"] = COLORS[bgcolor][1]
            if not c['edit']:
                ent.config(state='readonly')
            ent.grid({"column":col+1, "row":c['row'], "sticky":"NSW"})
            if 'maxsize' in c:
                ent["width"] = c['maxsize']
            else:
                ent["width"] = DEFAULT_WIDTH
            c['widget'] = ent
            if c['key'] != 'barcode':
                gridcol[c['row']] += 2
    def set_data(self, letter_info):
        """ Скопировать данные письма, заполнить entry
        """
        self.letter_info = copy.copy(letter_info)
        for c in self.GUI_DEF:
            c["widget"].config(state='normal') #необходимо для редактирования
            c["widget"].delete(0,"end")
            if c["key"] in self.letter_info:
                v = self.letter_info[c["key"]]
                if isinstance(v, int):
                    v = str(v)
                c["widget"].insert("end", v)
            if not c["edit"]:
                c["widget"].config(state='readonly')
