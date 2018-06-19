# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import Tkinter as tk

class UIScrollFrame(tk.Frame):
	""" Элемент с горизонтальными и вертикальными полосами прокрутки
	В качестве родителя для всяких элементов необходимо указывать .frame
	"""
	def __init__(self, master):
		tk.Frame.__init__(self, master)
		self.canvas = tk.Canvas(self)
		#вертикальный
		vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
		self.canvas.configure(yscrollcommand=vsb.set)
		vsb.pack(side="right", fill="y", expand=False)
		#горизонтальный
		hsb = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
		self.canvas.configure(xscrollcommand=hsb.set)
		hsb.pack(side="bottom", fill="x", expand=False)
		#
		self.canvas.pack(side="left", fill="both", expand=True)
		self.frame = tk.Frame(self.canvas)
		self.frame.pack(side="left", fill="both", expand=True)
		self.frame.bind("<Configure>", self.onFrameConfigure)
	def onFrameConfigure(self, event):
		self.canvas.configure(scrollregion=self.canvas.bbox('all'))
