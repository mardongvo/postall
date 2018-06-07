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

#TODO: параметры для верификации базы, для подключения к БД и выполнения DDL, alter table
#parser = argparse.ArgumentParser(description='postall SQL database init')

out = open("db.sql","w")
out.write( "create table if not exists LETTER_INFO(\n"  +
	", \n".join( dict_to_fields(defconf.LETTER_DB_FIELDS)+dict_to_fields(defconf.LETTER_DEFAULT)  ) +
	");\n" )
out.write("\n")
out.write( "create table if not exists REESTR_INFO(\n"  +
	", \n".join( dict_to_fields(defconf.REESTR_DB_FIELDS)  ) +
	");\n" )
out.write("\n")
contragent_struct = copy.copy(defconf.CONTRAGENT_DB_FIELDS)
for k,v in defconf.LETTER_DEFAULT.iteritems():
	if k.endswith("-to"):
		contragent_struct[k] = v
out.write( "create table if not exists CONTRAGENT_DICT(\n"  +
	", \n".join( dict_to_fields(contragent_struct)  ) +
	");\n" )
out.write("\n")
out.write( "create table if not exists USER_DICT(\n"  +
	", \n".join( dict_to_fields(defconf.USER_DB_FIELDS)  ) +
	");\n" )
out.close()
