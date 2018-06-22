# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import Tkinter as tk

class UIScrollFrame(tk.Frame):
	""" Элемент с горизонтальными и вертикальными полосами прокрутки
	В качестве родителя для всяких элементов необходимо указывать .frame
	"""
	def __init__(self, master):
		tk.Frame.__init__(self, master)
		self.grid_rowconfigure(0, weight=1)
		self.grid_columnconfigure(0, weight=1)
		self.canvas = tk.Canvas(self)
		#вертикальный
		self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
		self.vsb.grid(row=0, column=1, sticky="NS")
		#горизонтальный
		self.hsb = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
		self.hsb.grid(row=1, column=0, sticky="EW")
		#
		self.canvas.configure(yscrollcommand=self.vsb.set)
		self.canvas.configure(xscrollcommand=self.hsb.set)
		self.canvas.grid(row=0, column=0, sticky="NSWE")
		self.frame = self.canvas
		self.frame = tk.Frame(self.canvas)
		self.frame.grid(row=0, column=0, sticky="NSWE")
		self.canvas.create_window(1, 1, window=self.frame, anchor="nw")
		self.frame.bind("<Configure>", self.onFrameConfigure)
	def onFrameConfigure(self, event):
		self.canvas.configure(scrollregion=(0,0,event.width,event.height))
	def clear(self):
		""" Очистка содержимого
		
		:return:
		"""
		for w in self.frame.winfo_children():
			w.destroy()

