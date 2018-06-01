# -*- coding: utf-8 -*-

import base64

def to_base64(str):
	return base64.b64encode(str.encode()).decode("utf-8")

POSTGRES_DB="host=ip port=5432 dbname=postall user=... password=..." #database path/auth
PROXY_URL="..." #http proxy, set None for no-proxy
#see https://otpravka.pochta.ru/specification#/authorization-token
ACESS_TOKEN	= "....."
LOGIN_PASSWORD	= to_base64("login:pass")
POST_SERVER = "https://otpravka-api.pochta.ru"
POSTOFFICE_CODE = "000000"