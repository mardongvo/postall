# -*- coding: utf-8 -*-

from reportlab.graphics.barcode import common
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Rect

from reportlab.graphics.barcode.qr import QrCode

import os
import tempfile

def render_C5_letters(letter_iterator):
	""" Создает pdf файл во временной папке со страницами в виде конвертов C5

	:param letter_iterator: итератор, возвращающий кортеж (letter_info,
	from_info)
	:return: путь к файлу pdf
	"""
	# грязно, но обычно этот шрифт есть
	pdfmetrics.registerFont(TTFont('TimesNewRoman', 'times.ttf'))
	pdfmetrics.registerFont(TTFont('TimesNewRomanBold', 'timesbd.ttf'))
	# do draw
	hndl, path = tempfile.mkstemp(suffix='.pdf')
	#закрываем хэндл, иначе получим ошибку при открытии pdf файла
	tmp = os.fdopen(hndl, 'w')
	tmp.close()
	c = canvas.Canvas(path, pagesize=(229 * mm, 162 * mm))
	for letter_info, from_info  in letter_iterator:
		render_C5(c, letter_info, from_info)
		c.showPage()
	c.save()
	return path

def render_C5(canv, letter_info, from_info):
	barcode = letter_info["barcode"]
	from_name = from_info["name"]
	from_addr = from_info["addr"]
	from_index = from_info["index"]
	from_fio = from_info["fio"]
	no_return = u"Возврату не подлежит" if letter_info["no-return"] else ""
	dst_name = letter_info["recipient-name"]
	dst_addr = ", ".join(map(lambda k: letter_info[k],
		filter(lambda a: a in letter_info,["region-to", "area-to", "place-to", "location-to", "street-to", "hotel-to", "house-to", "slash-to", "letter-to", "building-to", "corpus-to", "room-to"])
	))
	dst_index = "%06d" % letter_info["index-to"]
	mass = letter_info["mass"]
	total_rate = letter_info["total_rate_wo_vat"]+letter_info["total_vat"]
	rate_print = u"%d руб %02d коп" % (total_rate//100, total_rate-(total_rate//100)*100)
	
	TEXT = [
		#from
		{"x":10,"y":110,"w":15,"h":15, "fontsize":10,"font":"TimesNewRomanBold","alignment":TA_LEFT,"text": u"От кого:"},
		{"x":25,"y":110,"w":70,"h":15, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":from_name},
		{"x":10,"y":98,"w":15,"h":15, "fontsize":10,"font":"TimesNewRomanBold","alignment":TA_LEFT,"text": u"Откуда:"},
		{"x":25,"y":98,"w":70,"h":15, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":from_addr},
		{"x":10,"y":86,"w":65,"h":15, "fontsize":14,"font":"TimesNewRomanBold","alignment":TA_LEFT,"text":from_index},
		{"x":10,"y":35,"w":30,"h":15, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":from_fio},
		{"x":10,"y":45,"w":55,"h":25, "fontsize":14,"font":"TimesNewRomanBold","alignment":TA_CENTER,"text":no_return, "border":True},
		#to
		{"x":115,"y":50,"w":15,"h":15, "fontsize":10,"font":"TimesNewRomanBold","alignment":TA_LEFT,"text": u"Кому:"},
		{"x":130,"y":50,"w":85,"h":15, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":dst_name},
		{"x":115,"y":35,"w":15,"h":15, "fontsize":10,"font":"TimesNewRomanBold","alignment":TA_LEFT,"text": u"Куда:"},
		{"x":130,"y":35,"w":85,"h":20, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":dst_addr},
		{"x":185,"y":20,"w":25,"h":5, "fontsize":16,"font":"TimesNewRomanBold","alignment":TA_LEFT,"text":dst_index},
		#barcode
		{"x":10,"y":128,"w":45,"h":15, "fontsize":12,"font":"TimesNewRoman","alignment":TA_CENTER,
			"text":"%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s" % (barcode[0:6],barcode[6:8], barcode[8:13], barcode[13:14])},
		#letter category etc
		{"x":115,"y":112,"w":45,"h":15, "fontsize":10,"font":"TimesNewRomanBold","alignment":TA_LEFT,"text": u"Без разряда"},
		{"x":115,"y":105,"w":85,"h":15, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text": u"Вес: %dг" % (mass,)},
		{"x":115,"y":100,"w":85,"h":15, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text": u"Плата за пересылку: %s" % (rate_print,)},
	]
	if "mail-category" in letter_info:
		cat = u"Письмо простое"
		if letter_info["mail-category"] == "ORDERED":
			cat = u"Письмо заказное"
		TEXT.append({"x": 115, "y": 116, "w": 45, "h": 15, "fontsize": 10, "font": "TimesNewRomanBold",
					 "alignment": TA_LEFT, "text": cat})
	for i in TEXT:
		ps = getSampleStyleSheet()["Normal"]
		ps.fontName = i["font"]
		ps.alignment = i["alignment"]
		ps.fontSize = i["fontsize"]
		P = Paragraph(i["text"], ps)
		w,h = P.wrap(i["w"]*mm, i["h"]*mm)
		P.drawOn(canv,i["x"]*mm,i["y"]*mm-h)
		if ("border" in i) and h>0:
			canv.setStrokeColorRGB(0,0,0)
			canv.rect(i["x"]*mm,i["y"]*mm-2*h,w,2*h)
	if letter_info["opm_id"] > "":
		render_QR(canv, letter_info, from_info, 115*mm, 130*mm)
	if barcode > "":
		ift = common.I2of5(value = barcode, checksum=False, bearers=0, barWidth=0.35*mm, gap = 1*mm, barHeight=10*mm)
		ift.drawOn(canv, 10*mm, 128*mm)

def render_QR(canv, letter_info, from_info, x, y):
	barcode = letter_info["barcode"]
	opm_index_oper = letter_info["opm_index_oper"]
	opm_id = letter_info["opm_id"]
	opm_value = letter_info["opm_value"]
	opm_value_print = "%d.%02d" % (opm_value//100, opm_value-(opm_value//100)*100)
	inn = from_info["inn"]
	kpp = from_info["kpp"]
	weight = letter_info["mass"]
	date_oper = letter_info["list-number-date"]
	postcode = letter_info["index-to"]
	qr_text="ID OPM: %s\r\nBarcode: %s\r\nTIN: %s\r\nTRRC: %s\r\nCost: %s\r\nWeight: %s\r\nDate: %s\r\nDispatch postcode: %s\r\nDelivery postcode: %s" % (
		opm_id,
		barcode,
		inn,
		kpp,
		opm_value_print,
		"%d" % (weight,),
		date_oper.strftime("%d/%m/%Y"),
		opm_index_oper,
		"%06d" % (postcode,)
	)
	qrw = QrCode(qr_text, width=30*mm, height=30*mm, qrLevel='L')
	qrw.drawOn(canv, x, y-5*mm)
	TEXT = [
		{"x":33,"y":20,"w":35,"h":15, "fontsize":11,"font":"TimesNewRoman","alignment":TA_CENTER,"text":"РОССИЯ•RUSSIA"},
		{"x":33,"y":16,"w":35,"h":15, "fontsize":11,"font":"TimesNewRoman","alignment":TA_CENTER,"text":"ПОЧТА"},
		{"x":33,"y":13,"w":35,"h":20, "fontsize":20,"font":"TimesNewRoman","alignment":TA_LEFT,"text":"₽"},
		{"x":33,"y":11,"w":35,"h":15, "fontsize":14,"font":"TimesNewRoman","alignment":TA_CENTER,"text":opm_value_print},
		{"x":33,"y":6,"w":35,"h":15, "fontsize":9,"font":"TimesNewRoman","alignment":TA_LEFT,"text":date_oper.strftime("%d/%m/%Y")},
		{"x":33,"y":6,"w":35,"h":15, "fontsize":9,"font":"TimesNewRoman","alignment":TA_RIGHT,"text":opm_index_oper},
		{"x":33,"y":2,"w":35,"h":15, "fontsize":9,"font":"TimesNewRoman","alignment":TA_LEFT,"text": opm_id},
	]
	for i in TEXT:
		ps = getSampleStyleSheet()["Normal"]
		ps.fontName = i["font"]
		ps.alignment = i["alignment"]
		ps.fontSize = i["fontsize"]
		P = Paragraph(i["text"], ps)
		w,h = P.wrap(i["w"]*mm, i["h"]*mm)
		P.drawOn(canv, x + i["x"]*mm, y + i["y"]*mm)
