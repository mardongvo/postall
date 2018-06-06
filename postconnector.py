# -*- coding: utf-8 -*-

import requests
import json
import configuration as defconf

class PostConnector:
	def __init__(self):
		self.session = requests.Session()
	def set_proxy(self, proxyurl=""):
		pass
	def set_auth(self, token=defconf.ACESS_TOKEN, login_password=defconf.LOGIN_PASSWORD):
		pass
	def add_backlog(self, letter_info):
		return (id, error)
	def add_shipment(self, send_date, backlog_ids):
		return (id, error)
	def add_backlogs(self, letter_info_array):
		yield (id, error)
	def modify_shipment(self, send_date):
		return err
	def remove_backlog(self, ext_id):
		return err
