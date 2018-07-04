# -*- coding: utf-8 -*-
import psycopg2
import dbf
import requests
import zipfile
import re
import argparse
import os

def download_file(url, proxy):
	local_filename = url.split('/')[-1]
	r = requests.get(url, stream=True, proxies=proxy)
	with open(local_filename, 'wb') as f:
		for chunk in r.iter_content(chunk_size=1024):
			if chunk:
				f.write(chunk)
	return local_filename

def extract(fname):
	zf = zipfile.ZipFile(fname)
	for i in zf.infolist():
		if re.match("PIndx.*dbf", i.filename, re.I):
			zf.extract(i)
			return i.filename

"""
POSTINDEX_DB_FIELDS = {
	"index-to": 0,  # Почтовый индекс Целое число (INDEX)
	"region-to": "",  # Область, регион (REGION, AUTONOM)
	"area-to": "", #Район (AREA)
	"place-to": "",  # Населенный пункт (CITY, CITY_1)
}
"""

def str_coalesce(*strs):
	for i in strs:
		if i>"": return i

def postindex_import(dbconn, fname):
	cur = dbconn.cursor()
	spr = dbf.Db3Table(filename=fname)
	spr.open()
	cur.execute("delete from POSTINDEX;")
	n = 1
	for rec in spr:
		n+=1
		cur.execute("insert into POSTINDEX(index_to, region_to, area_to, place_to) values(%s,%s,%s,%s)",
					(int(rec['index']),
					 str_coalesce(rec['region'].strip(),rec['autonom'].strip()),
					 rec['area'].strip(),
					 str_coalesce(rec['city'].strip(),rec['region'].strip())  )
					)
	dbconn.commit()
	spr.close()

parser = argparse.ArgumentParser(description='postall postindex loader')
parser.add_argument("-db","--database", type=unicode, help="database connection string")
parser.add_argument("-c","--clear", action="store_true", help="clear downloaded files")
parser.add_argument("-p","--proxy", type=unicode, default="", help="http proxy <ip:port>")
args = vars(parser.parse_args())

proxy = None
if args["proxy"]>"":
	proxy={"http":args["proxy"]}
fname = download_file('http://vinfo.russianpost.ru/database/PIndx.zip', proxy)
dbfname = extract(fname)
conn = psycopg2.connect(args["database"])
postindex_import(conn, dbfname)
if args["clear"]:
	os.remove(dbfname)
	os.remove(fname)