# -*- coding: utf-8 -*-

from reportlab.graphics.barcode import common
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, TA_LEFT, TA_CENTER
import os
import tmpfile

def render_DL_letters(letters)
	hndl, path = tempfile.mkstemp(suffix='.pdf')
	#close handle
	tmp = os.fdopen(hndl,'w')
	tmp.close()
	#do draw
	c = canvas.Canvas(path, pagesize=(220*mm, 110*mm))
	for li in letters:
		render_DL(c, li)
		c.showPage()
	c.save()

def render_DL(canv, letter_info):
	#TODO: заменить имена полей
	#letter_num, from_name, from_adr, from_index, dst_name, dst_adr, dst_index, fio
	barcode = letter_info["letter_num"]
	TEXT = [
		{"x":20,"y":100,"w":65,"h":15, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":letter_info["from_name"]},
		{"x":20,"y":85,"w":65,"h":15, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":letter_info["from_adr"]},
		{"x":55,"y":80,"w":30,"h":5, "fontsize":10,"font":"TimesNewRoman","alignment":TA_CENTER,"text":letter_info["from_index"]},
		{"x":20,"y":80,"w":30,"h":5, "fontsize":6,"font":"TimesNewRoman","alignment":TA_LEFT,"text":letter_info["fio"]},
		{"x":115,"y":50,"w":85,"h":15, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":letter_info["dst_name"]},
		{"x":115,"y":30,"w":85,"h":20, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":letter_info["dst_adr"]},
		{"x":105,"y":18,"w":30,"h":5, "fontsize":10,"font":"TimesNewRoman","alignment":TA_CENTER,"text":letter_info["dst_index"]},
		{"x":95,"y":84,"w":45,"h":5, "fontsize":10,"font":"TimesNewRoman","alignment":TA_CENTER,
			"text":"%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s" % (barcode[0:6],barcode[6:8], barcode[8:13], barcode[13:14])},
		#TODO: заменить
		{"x":95,"y":75,"w":45,"h":5, "fontsize":10,"font":"TimesNewRoman","alignment":TA_CENTER,"text":u"Заказное"},
	]
	for i in TEXT:
		ps = getSampleStyleSheet()["Normal"]
		ps.fontName = i["font"]
		ps.alignment = i["alignment"]
		ps.fontSize = i["fontsize"]
		P=Paragraph(i["text"], ps)
		w,h = P.wrap(i["w"]*mm, i["h"]*mm)
		P.drawOn(canv,i["x"]*mm,i["y"]*mm)
	for i in xrange(len(letter_info["dst_index"])):
		ii = letter_info["dst_index"][i]
		if ii in ['0','1','2','3','4','5','6','7','8','9']:
			#TODO: перенести bmp в файл ресурсов
			canv.drawImage("index_bmp/Index%s.bmp" % (ii,), (20+9*i)*mm, 10*mm)
	#barcode
	ift = common.I2of5(value = barcode, checksum=False, bearers=0, barWidth=0.35*mm, gap = 1*mm, barHeight=10*mm)
	ift.drawOn(canv, 95*mm, 90*mm)