# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import Tkinter as tk
from dbstorage import LOCK_STATE_FREE, LOCK_STATE_BACKLOG, LOCK_STATE_BATCH
import copy

BG_COLOR = "FFFFFF"
DEFAULT_WIDTH = 20
ERROR_BG = "#d271ff"

#цвета фона для различия позиций в списке
COLORS = (
	("#cccdff", "#7e80c9"),
	("#ffc9c9", "#c97e7e")
)

def pages_to_mass(pages_count):
	mass = int(round(4.945*pages_count+4.2, 3))
	if mass<20: mass = 20
	return mass

class UILetter(tk.Frame):
	"""UI класс представления письма в виде горизонтальной области в несколько строк
	"""
	
	GUI_DEF = [
		{'key': 'barcode', 'title': u'Номер', 'type': 'text', 'edit': False, 'maxsize': 14, 'row': 0},
		{'key': 'index-to', 'title': u'Индекс', 'type': 'integer', 'edit': True, 'maxsize': 6, 'row': 0},
		{'key': 'region-to', 'title': u'Обл.', 'type': 'text', 'edit': True, 'maxsize': 20, 'row': 0},
		{'key': 'place-to', 'title': u'Город', 'type': 'text', 'edit': True, 'maxsize': 15, 'row': 0},
		{'key': 'street-to', 'title': u'Улица', 'type': 'text', 'edit': True, 'maxsize': 20, 'row': 0},
		{'key': 'house-to', 'title': u'Дом', 'type': 'text', 'edit': True, 'maxsize': 6, 'row': 0},
		{'key': 'room-to', 'title': u'Кв./офис', 'type': 'text', 'edit': True, 'maxsize': 6, 'row': 0},
		{'key': 'recipient-name', 'title': u'Адресат', 'type': 'text', 'edit': True, 'maxsize': 20, 'row': 1},
		{'key': 'mass', 'title': u'Масса', 'type': 'integer', 'edit': True, 'maxsize': 6, 'row': 1},
		{'key': 'db_mass_pages', 'title': u'Листов', 'type': 'integer', 'edit': True, 'maxsize': 6, 'row': 1},
		{'key': 'comment', 'title': u'Содерж.', 'type': 'text', 'edit': True, 'maxsize': 20, 'row': 1},
		{'key': 'db_last_error', 'title': u'Ошибка', 'type': 'text', 'edit': False, 'maxsize': 30, 'row': 2},
		{'key': 'db_user_id', 'title': u'Польз.', 'type': 'text', 'edit': False, 'maxsize': 10, 'row': 2},
	]
	
	def __init__(self, master, bgcolor=0, action_callback=None):
		self.letter_info = {}
		self.action_callback = action_callback
		#create widgets
		tk.Frame.__init__(self, master)
		self["bg"] = COLORS[bgcolor][0]
		#self.pack(fill="both", expand=True)
		#виджеты Tk Entry по-умолчанию не имеют контекстного меню
		self.ctx_menu = tk.Menu(self, tearoff=0)
		self.ctx_menu.add_command(label=u"Вырезать")
		self.ctx_menu.add_command(label=u"Копировать")
		self.ctx_menu.add_command(label=u"Вставить")		
		self.bind_class("Entry", "<Button-3><ButtonRelease-3>", self.onShowMenu)
		#специально запомненные виджеты для обработки событий
		self.index_widget = None
		self.mass_widget = None
		self.massp_widget = None
		##########
		gridcol = {}
		for i in map(lambda a: a['row'], self.GUI_DEF):
			gridcol[i] = 2
		for c in self.GUI_DEF:
			col = gridcol[c['row']]
			if c['key'] == 'barcode':
				col = 0
			L1 = tk.Label(self, text = c['title'])
			L1.grid({"column":col, "row":c['row'], "sticky":"NSW"})
			L1["width"] = -1
			L1["bg"] = COLORS[bgcolor][0]
			ent = tk.Entry(self)
			#ent.insert("end", data[c['name']])
			ent["background"] = COLORS[bgcolor][0]
			ent["readonlybackground"] = COLORS[bgcolor][1]
			if not c['edit']:
				ent.config(state='readonly')
			ent.grid({"column":col+1, "row":c['row'], "sticky":"NSW"})
			if 'maxsize' in c:
				ent["width"] = c['maxsize']
			else:
				ent["width"] = DEFAULT_WIDTH
			if c['key']=='index-to':
				ent.bind("<KeyRelease>", self.onIndexUpdate)
			elif c['key']=='db_mass_pages':
				ent.bind("<KeyRelease>", self.onMasspEdit)
			else:
				ent.bind("<KeyRelease>", self.onEntryUpdate)
			ent.bind("<<Cut>>", self.onEntrySpec)
			ent.bind("<<Paste>>", self.onEntrySpec)
			ent.bind("<Control-KeyPress>", self.onCCPrus)
			c['widget'] = ent
			if c['key'] != 'barcode':
				gridcol[c['row']] += 2
			#специальные виджеты
			if c['key']=='index-to':
				self.index_widget = ent
			if c['key'] == 'db_mass_pages':
				self.massp_widget = ent
			if c['key'] == 'mass':
				self.mass_widget = ent
		self.btn_save = tk.Button(self)
		self.btn_save["text"] = u"Сохранить"
		self.btn_save["command"] = self.onClickSave
		self.btn_save.grid({"column":max(gridcol.values())+1, "row":0, "sticky":"NSEW"})
		self.btn_print = tk.Button(self)
		self.btn_print["text"] = u"Конверт"
		self.btn_print["command"] = self.onClickPrint
		self.btn_print.grid({"column":max(gridcol.values())+2, "row":0, "sticky":"NSEW"})
		self.btn_delete = tk.Button(self)
		self.btn_delete["text"] = u"Удалить"
		self.btn_delete["command"] = self.onClickDelete
		self.btn_delete.grid({"column":max(gridcol.values())+1, "row":1, "sticky":"NSEW"})
		self.btn_barcode = tk.Button(self)
		self.btn_barcode["text"] = u"Получить номер"
		self.btn_barcode["command"] = self.onClickBarcode
		self.btn_barcode.grid({"column":max(gridcol.values())+1, "row":2, "sticky":"NSEW", "columnspan":2})
	def onShowMenu(self, e):
		""" Event - отображение меню для entry
		"""
		w = e.widget
		self.ctx_menu.entryconfigure(0, command=lambda: w.event_generate("<<Cut>>"))
		self.ctx_menu.entryconfigure(1, command=lambda: w.event_generate("<<Copy>>"))
		self.ctx_menu.entryconfigure(2, command=lambda: w.event_generate("<<Paste>>"))
		self.ctx_menu.tk.call("tk_popup", self.ctx_menu, e.x_root, e.y_root)
	def onEntryUpdate(self, event):
		""" Event - при изменении entry изменить цвет кнопки Сохранить
		"""
		if (event.char>'') or (event.keysym=="Delete") or (event.keysym=="BackSpace") or \
			( ((event.keycode==88) or (event.keycode==86)) and (event.state & 0x0004 > 0)):
			self.btn_save["foreground"] = "#FF0000"
	def onEntrySpec(self, event):
		""" Event - при событиях Cut/Paste изменить цвет кнопки Сохранить
		"""
		self.btn_save["foreground"] = "#FF0000"
	def onIndexUpdate(self, event):
		""" Event - при изменении entry индекса, найти область/регион/город
		"""
		if (event.char>'') or (event.keysym=="Delete") or (event.keysym=="BackSpace"):
			self.onEntryUpdate(event)
			if self.index_widget:
				index = self.index_widget.get()
				#TODO: get region, area, city
				#print("find index "+index)
				#cur = self.connection.cursor()
				#cur.execute("select region, city from POSTINDEX where postindex=%s",(index,))
				#for i in cur:
				#	self.mlist_widgets[idd]['region'].delete(0,"end")
				#	self.mlist_widgets[idd]['region'].insert("end", i[0])
				#	#self.mlist_widgets[idd]['area'].delete(0,"end")
				#	#self.mlist_widgets[idd]['area'].insert("end", i[1])
				#	self.mlist_widgets[idd]['city'].delete(0,"end")
				#	self.mlist_widgets[idd]['city'].insert("end", i[1])
				#cur.close()
	def onCCPrus(self, event):
		""" Event - шорткаты Ctrl-C,V,X при русской раскладке
		"""
		# C - 67
		# V - 86
		# X - 88
		if event.keycode==88:
			event.widget.event_generate("<<Cut>>")
		if event.keycode==67:
			event.widget.event_generate("<<Copy>>")
		if event.keycode==86:
			event.widget.event_generate("<<Paste>>")
	def onClickSave(self):
		""" Event - клик по кнопке Сохранить
		"""
		self.sync()
		if self.action_callback:
			if self.action_callback("SAVE", self.letter_info):
				self.btn_save["foreground"] = "#000000"
	def onClickPrint(self):
		""" Event - клик по кнопке Конверт
		"""
		if self.action_callback:
			self.action_callback("PRINT", self.letter_info)
	def onClickDelete(self):
		""" Event - клик по кнопке Удалить
		"""
		if self.action_callback:
			self.action_callback("DELETE", self.letter_info)
	def onClickBarcode(self):
		""" Event - клик по кнопке Получить/удалить код
		"""
		if self.action_callback:
			self.action_callback("BARCODE", self.letter_info)
	def onMasspEdit(self, event):
		pages_count = 1
		try:
			pages_count = int(self.massp_widget.get())
		except:
			pages_count = 1
		mass = pages_to_mass(pages_count)
		print((event.keycode,event.state))
		print(self.mass_widget)
		self.mass_widget.delete(0,"end")
		self.mass_widget.insert("end", "%d" % (mass,))
		self.btn_save["foreground"] = "#FF0000"
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
		self.set_lock(self.letter_info["db_locked"])
	def set_lock(self, lock_state):
		""" Установить доступность кнопок согласно блокировке письма
		"""
		self.btn_print["state"] = "disabled"
		self.btn_save["state"] = "disabled"
		self.btn_delete["state"] = "disabled"
		self.btn_barcode["text"] = u'Присвоить номер'
		for c in self.GUI_DEF:
			c["widget"].config(state='readonly')
		if lock_state == LOCK_STATE_FREE:
			self.btn_save["state"] = "enabled"
			self.btn_delete["state"] = "enabled"
			for c in self.GUI_DEF:
				if c["edit"]:
					c["widget"].config(state='normal')
		if lock_state == LOCK_STATE_BACKLOG:
			pass
		if lock_state == LOCK_STATE_BATCH:
			self.btn_print["state"] = "enabled"
			self.btn_barcode["text"] = u'Удалить номер'
	def sync(self):
		""" Перенести данные из формы в letter_info
		"""
		for c in self.GUI_DEF:
			if c["key"] in self.letter_info:
				v = c["widget"].get()
				if c["type"]=="integer":
					try:
						v = int(v)
					except:
						v = 0
				self.letter_info[c["key"]] = v