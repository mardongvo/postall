# -*- coding: utf-8 -*-

import argparse
import copy
import configuration as defconf
from dbstorage import fix_json_field_name

def datatype_to_sqltype(field_name, field_value, dbtype="postgres"):
	if isinstance(field_value, str) and (field_value=="sequence"):
		return "serial"
	if isinstance(field_value, str) and (field_value=="date"):
		return "date default CURRENT_DATE"
	if isinstance(field_value, bool):
		return "boolean default false"
	if isinstance(field_value, int):
		return "integer default 0"
	if isinstance(field_value, str):
		return "text default ''"
	raise Exception("datatype_to_sqltype: unknown type field_name=%s, field_value=%s" % (field_name, field_value))

def dict_to_fields(inp_dict):
	return map(lambda k: fix_json_field_name(k)+" "+datatype_to_sqltype(k, inp_dict[k]), inp_dict.keys() )

def sql_table(tablename, fields):
	return "create table if not exists %s(\n" % (tablename,) + ", \n".join( fields ) + ");\n"

def dump_sql(sql, out, db):
	if out:
		out.write(sql)
	if db:
		cur = db.cursor()
		cur.execute(sql)
		db.commit()

#TODO: параметры для верификации базы, alter table, выбор типа субд
parser = argparse.ArgumentParser(description='postall SQL database initializer')
parser.add_argument("-o","--out", type=unicode, default="-", help="output file for sql code" )
parser.add_argument("-db","--database", type=unicode, default=argparse.SUPPRESS, help="database connection string")
parser.add_argument("-a","--alter", action="store_true", help="alter columns of tables")
parser.add_argument("-v","--verify", action="store_true", help="verify tables")
args = vars(parser.parse_args())

out = None
db = None
if "out" in args:
	if args["out"]=="-":
		import sys
		out = sys.stdout
	else:
		out = open(args["out"],"w")
if "database" in args:
	import psycopg2
	db = psycopg2.connect(args["database"])

###
sql = sql_table("LETTER_INFO", dict_to_fields(defconf.LETTER_DB_FIELDS)+dict_to_fields(defconf.LETTER_DEFAULT) )
dump_sql(sql, out, db)
###
sql = sql_table("REESTR_INFO", dict_to_fields(defconf.REESTR_DB_FIELDS) )
dump_sql(sql, out, db)
###
contragent_struct = copy.copy(defconf.CONTRAGENT_DB_FIELDS)
for k,v in defconf.LETTER_DEFAULT.iteritems():
	if k.endswith("-to"):
		contragent_struct[k] = v
sql = sql_table("CONTRAGENT_DICT", dict_to_fields(contragent_struct) )
dump_sql(sql, out, db)
###
sql = sql_table("USER_DICT", dict_to_fields(defconf.USER_DB_FIELDS) )
dump_sql(sql, out, db)
###
sql = sql_table("POSTINDEX", dict_to_fields(defconf.POSTINDEX_DB_FIELDS) )
dump_sql(sql, out, db)
###
if defconf.USE_DAEMON:
	sql = sql_table("COMMAND_QUEUE", ["uid serial", "command varchar(20)","db_reestr_id integer unique","db_letter_id integer","reestr_date date", "db_user_id text"])
	dump_sql(sql, out, db)
###
if out:
	out.close()
if db:
	db.close()