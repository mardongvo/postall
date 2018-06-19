# -*- coding: utf-8 -*-

from reportlab.graphics.barcode import common
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, TA_LEFT, TA_CENTER
import os
import tempfile
import configuration as defconf
from base64 import standard_b64decode
from io import BytesIO

def render_DL_letters(letters, from_info=defconf.FROM_INFO):
	""" Создает pdf файл во временной папке со страницами в виде конвертов DL
	
	:param letters: массив словарей
	:param from_info: информация об отправителе configuration.FROM_INFO
	:return: путь к файлу pdf
	"""
	#грязно, но обычно этот шрифт есть
	pdfmetrics.registerFont(TTFont('TimesNewRoman', 'times.ttf'))
	#
	hndl, path = tempfile.mkstemp(suffix='.pdf')
	#close handle
	tmp = os.fdopen(hndl,'w')
	tmp.close()
	#do draw
	c = canvas.Canvas(path, pagesize=(220*mm, 110*mm))
	for li in letters:
		render_DL(c, li, from_info)
		c.showPage()
	c.save()
	return path

def render_DL(canv, letter_info, from_info):
	barcode = letter_info["barcode"]
	from_name = from_info["name"]
	from_addr = from_info["addr"]
	from_index = from_info["index"]
	from_fio = from_info["fio"]
	dst_name = letter_info["recipient-name"]
	dst_addr = ", ".join(map(lambda k: letter_info[k] if k in letter_info else "",
		["region-to", "area-to", "place-to", "location-to", "street-to", "hotel-to", "house-to", "slash-to", "letter-to", "building-to", "corpus-to", "room-to"]
	))
	dst_index = "%06d" % letter_info["index-to"]
	
	TEXT = [
		{"x":20,"y":100,"w":65,"h":15, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":from_name},
		{"x":20,"y":85,"w":65,"h":15, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":from_addr},
		{"x":55,"y":80,"w":30,"h":5, "fontsize":10,"font":"TimesNewRoman","alignment":TA_CENTER,"text":from_index},
		{"x":20,"y":80,"w":30,"h":5, "fontsize":6,"font":"TimesNewRoman","alignment":TA_LEFT,"text":from_fio},
		{"x":115,"y":50,"w":85,"h":15, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":dst_name},
		{"x":115,"y":30,"w":85,"h":20, "fontsize":10,"font":"TimesNewRoman","alignment":TA_LEFT,"text":dst_addr},
		{"x":105,"y":18,"w":30,"h":5, "fontsize":10,"font":"TimesNewRoman","alignment":TA_CENTER,"text":dst_index},
		{"x":95,"y":84,"w":45,"h":5, "fontsize":10,"font":"TimesNewRoman","alignment":TA_CENTER,
			"text":"%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s" % (barcode[0:6],barcode[6:8], barcode[8:13], barcode[13:14])},
	]
	if "mail-category" in letter_info and letter_info["mail-category"] == "ORDERED":
		TEXT.append({"x": 95, "y": 75, "w": 45, "h": 5, "fontsize": 10, "font": "TimesNewRoman",
					 "alignment": TA_CENTER, "text": u"Заказное"})
	for i in TEXT:
		ps = getSampleStyleSheet()["Normal"]
		ps.fontName = i["font"]
		ps.alignment = i["alignment"]
		ps.fontSize = i["fontsize"]
		P = Paragraph(i["text"], ps)
		w,h = P.wrap(i["w"]*mm, i["h"]*mm)
		P.drawOn(canv,i["x"]*mm,i["y"]*mm)
	for i in range(len(dst_index)):
		ii = dst_index[i]
		if ii in ['0','1','2','3','4','5','6','7','8','9']:
			canv.drawImage(ImageReader(BytesIO(standard_b64decode(_INDEX_IMAGES[ii]))), (20+9*i)*mm, 10*mm)
	#barcode
	ift = common.I2of5(value = barcode, checksum=False, bearers=0, barWidth=0.35*mm, gap = 1*mm, barHeight=10*mm)
	ift.drawOn(canv, 95*mm, 90*mm)

#изображения цифр индекса в формате bmp (base64)
_INDEX_IMAGES = {
'0':'Qk3yAAAAAAAAAD4AAAAoAAAAGAAAAC0AAAABAAEAAAAAALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wD///8A8AAPAPAADwDz/88A8v/PAPP/zwDz/88A89/PAPP/zwDz/88A8/vPAPP/zwDz/88A8/9PAPP/zwDz/88A8ttPAPP/zwDz/88A8v/PAPP/zwDz/88A89/PAPP/zwDz/88A8/vPAPP/zwDz/88A8/9PAPP/zwDwAA8A8AAPAP///wD///8A////AP///wD///8A////AIAAAQCAAAEAgAABAIAAAQCAAAEAgAABAP///wA=',
'1':'Qk3yAAAAAAAAAD4AAAAoAAAAGAAAAC0AAAABAAEAAAAAALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wD///8A9ttPAP//zwD//88A9v/PAP//zwD//88A99/PAP//zwD//88A9/vPAP//zwD//88A9/9PAP//zwD//88A8ttPAPH/zwD4/88A9H/PAP4/zwD/H88A94/PAP/HzwD/488A9/HPAP/4zwD//E8A9/4PAP//DwD//48A9ttPAP///wD///8A////AP///wD///8A////AIAAAQCAAAEAgAABAIAAAQCAAAEAgAABAP///wA=',
'2':'Qk3yAAAAAAAAAD4AAAAoAAAAGAAAAC0AAAABAAEAAAAAALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wD///8A8AAPAPAADwD4//8A9H/vAP4//wD/H/8A94/vAP/H/wD/4/8A9/HvAP/4/wD//H8A9/4vAP//HwD//48A9ttPAP//zwD//88A9v/PAP//zwD//88A99/PAP//zwD//88A9/vPAP//zwD//88A9/9PAP//zwDwAA8A8AAPAP///wD///8A////AP///wD///8A////AIAAAQCAAAEAgAABAIAAAQCAAAEAgAABAP///wA=',
'3':'Qk3yAAAAAAAAAD4AAAAoAAAAGAAAAC0AAAABAAEAAAAAALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wD///8A8ttvAPH//wD4//8A9H/vAP4//wD/H/8A94/vAP/H/wD/4/8A9/HvAP/4/wD//H8A9/4vAP//HwD//48A8AAPAPAADwD4//8A9H/vAP4//wD/H/8A94/vAP/H/wD/4/8A9/HvAP/4/wD//H8A9/4vAP//HwDwAA8A8AAPAP///wD///8A////AP///wD///8A////AIAAAQCAAAEAgAABAIAAAQCAAAEAgAABAP///wA=',
'4':'Qk3yAAAAAAAAAD4AAAAoAAAAGAAAAC0AAAABAAEAAAAAALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wD///8A9ttPAP//zwD//88A9v/PAP//zwD//88A99/PAP//zwD//88A9/vPAP//zwD//88A9/9PAP//zwDwAA8A8AAPAPP/zwDz/88A8v/PAPP/zwDz/88A89/PAPP/zwDz/88A8/vPAPP/zwDz/88A8/9PAPP/zwDz/88A8ttPAP///wD///8A////AP///wD///8A////AIAAAQCAAAEAgAABAIAAAQCAAAEAgAABAP///wA=',
'5':'Qk3yAAAAAAAAAD4AAAAoAAAAGAAAAC0AAAABAAEAAAAAALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wD///8A8AAPAPAADwD//88A9v/PAP//zwD//88A99/PAP//zwD//88A9/vPAP//zwD//88A9/9PAP//zwD//88A8AAPAPAADwDz//8A8v/vAPP//wDz//8A89/vAPP//wDz//8A8/vvAPP//wDz//8A8/9vAPP//wDwAA8A8AAPAP///wD///8A////AP///wD///8A////AIAAAQCAAAEAgAABAIAAAQCAAAEAgAABAP///wA=',
'6':'Qk3yAAAAAAAAAD4AAAAoAAAAGAAAAC0AAAABAAEAAAAAALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wD///8A8AAPAPAADwDz/88A8v/PAPP/zwDz/88A89/PAPP/zwDz/88A8/vPAPP/zwDz/88A8/9PAPP/zwDz/88A8AAPAPAADwDx//8A8P/vAPx//wD+P/8A9x/vAP+P/wD/x/8A9+PvAP/x/wD/+P8A9/xvAP/+PwD//x8A9tsPAP///wD///8A////AP///wD///8A////AIAAAQCAAAEAgAABAIAAAQCAAAEAgAABAP///wA=',
'7':'Qk3yAAAAAAAAAD4AAAAoAAAAGAAAAC0AAAABAAEAAAAAALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wD///8A8ttvAPP//wDz//8A8v/vAPP//wDz//8A89/vAPP//wDz//8A8/vvAPP//wDz//8A8/9vAPP//wDz//8A8ttvAPH//wD4//8A9H/vAP4//wD/H/8A94/vAP/H/wD/4/8A9/HvAP/4/wD//H8A9/4vAP//HwDwAA8A8AAPAP///wD///8A////AP///wD///8A////AIAAAQCAAAEAgAABAIAAAQCAAAEAgAABAP///wA=',
'8':'Qk3yAAAAAAAAAD4AAAAoAAAAGAAAAC0AAAABAAEAAAAAALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wD///8A8AAPAPAADwDz/88A8v/PAPP/zwDz/88A89/PAPP/zwDz/88A8/vPAPP/zwDz/88A8/9PAPP/zwDz/88A8AAPAPAADwDz/88A8v/PAPP/zwDz/88A89/PAPP/zwDz/88A8/vPAPP/zwDz/88A8/9PAPP/zwDwAA8A8AAPAP///wD///8A////AP///wD///8A////AIAAAQCAAAEAgAABAIAAAQCAAAEAgAABAP///wA=',
'9':'Qk3yAAAAAAAAAD4AAAAoAAAAGAAAAC0AAAABAAEAAAAAALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wD///8A8ttvAPH//wD4//8A9H/vAP4//wD/H/8A94/vAP/H/wD/4/8A9/HvAP/4/wD//H8A9/4vAP//HwDwAA8A8AAPAPP/zwDz/88A8v/PAPP/zwDz/88A89/PAPP/zwDz/88A8/vPAPP/zwDz/88A8/9PAPP/zwDwAA8A8AAPAP///wD///8A////AP///wD///8A////AIAAAQCAAAEAgAABAIAAAQCAAAEAgAABAP///wA=',
}
