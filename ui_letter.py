# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import Tkinter as tk
from dbstorage import LOCK_STATE_FREE, LOCK_STATE_BACKLOG, LOCK_STATE_BATCH, LOCK_STATE_FINAL
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
	
	def __init__(self, master, bgcolor=0, action_callback=None):
		self.GUI_DEF = [
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
		self.letter_info = {}
		self.action_callback = action_callback
		#create widgets
		tk.Frame.__init__(self, master)
		self["bg"] = COLORS[bgcolor][0]
		#self.pack(fill="both", expand=True)
		self.index_widget = None
		self.mass_widget = None
		self.massp_widget = None
		##########
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
			if c['key']=='index-to': #спец обработка измененеия индекса
				ent.bind("<KeyRelease>", self.onIndexUpdate)
			elif c['key']=='db_mass_pages': #спец обработка измененеия количества листов
				ent.bind("<KeyRelease>", self.onMasspEdit)
			else:
				ent.bind("<KeyRelease>", self.onEntryUpdate)
			ent.bind("<<Cut>>", self.onEntrySpec)
			ent.bind("<<Paste>>", self.onEntrySpec)
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
		#кнопки
		self.btn_save = tk.Button(self, text=u"Сохранить", command=self.onClickSave, bg=COLORS[bgcolor][0])
		self.btn_save.grid({"column":max(gridcol.values())+1, "row":0, "sticky":"NSEW"})
		#
		self.btn_print = tk.Button(self, text=u"Конверт", command=self.onClickPrint, bg=COLORS[bgcolor][0])
		self.btn_print.grid({"column":max(gridcol.values())+2, "row":0, "sticky":"NSEW"})
		#
		self.btn_delete = tk.Button(self, text=u"Удалить", command=self.onClickDelete, bg=COLORS[bgcolor][0])
		self.btn_delete.grid({"column":max(gridcol.values())+1, "row":1, "sticky":"NSEW"})
		#
		self.btn_barcode = tk.Button(self, text=u"Получить номер", command=self.onClickBarcode, bg=COLORS[bgcolor][0])
		self.btn_barcode.grid({"column":max(gridcol.values())+1, "row":2, "sticky":"NSEW", "columnspan":2})
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
				try:
					postindex = int(self.index_widget.get())
				except:
					postindex = 0
				if self.action_callback:
					pinf = self.action_callback("POSTINDEX", {"postindex":postindex})
					self.sync()
					for k,v in pinf.iteritems():
						self.letter_info[k] = v
					self.set_data(self.letter_info)
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
		self.sync()
		if self.action_callback:
			self.action_callback("PRINT", self.letter_info)
	def onClickDelete(self):
		""" Event - клик по кнопке Удалить
		"""
		self.sync()
		if self.action_callback:
			self.action_callback("DELETE", self.letter_info)
	def onClickBarcode(self):
		""" Event - клик по кнопке Получить/удалить код
		"""
		self.sync()
		if self.action_callback:
			if (self.letter_info["db_locked"] == LOCK_STATE_FREE) or (self.letter_info["db_locked"] == LOCK_STATE_BACKLOG):
				self.action_callback("BARCODE_ADD", self.letter_info)
			elif (self.letter_info["db_locked"] == LOCK_STATE_BATCH):
				self.action_callback("BARCODE_DEL", self.letter_info)
	def onMasspEdit(self, event):
		pages_count = 1
		try:
			pages_count = int(self.massp_widget.get())
		except:
			pages_count = 1
		mass = pages_to_mass(pages_count)
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
			if not c["edit"]:
				c["widget"].config(state='readonly')
		self.set_lock(self.letter_info["db_locked"])
	def set_lock(self, lock_state):
		""" Установить доступность элементов согласно статусу блокировки письма
		"""
		self.btn_print["state"] = "disabled"
		self.btn_save["state"] = "disabled"
		self.btn_delete["state"] = "disabled"
		self.btn_barcode["state"] = "disabled"
		self.btn_barcode["text"] = u'Присвоить номер'
		for c in self.GUI_DEF:
			c["widget"].config(state='readonly')
		if lock_state == LOCK_STATE_FREE:
			self.btn_save["state"] = "normal"
			self.btn_delete["state"] = "normal"
			self.btn_barcode["state"] = "normal"
			for c in self.GUI_DEF:
				if c["edit"]:
					c["widget"].config(state='normal')
		if lock_state == LOCK_STATE_BACKLOG:
			pass
		if lock_state == LOCK_STATE_BATCH:
			self.btn_print["state"] = "normal"
			self.btn_barcode["state"] = "normal"
			self.btn_barcode["text"] = u'Удалить номер'
		if lock_state == LOCK_STATE_FINAL:
			pass
	def sync(self):
		""" Перенсит данные из формы в letter_info
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
