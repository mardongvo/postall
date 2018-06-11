import unittest

import sys
sys.path.append('..')

from datetime import datetime
from postconnector import PostConnector

class MockResponse:
	def __init__(self, text, status_code):
		self.text = text
		self.status_code = status_code

class MockSession:
	def __init__(self):
		self.put_callback = None
		self.get_callback = None
		self.post_callback = None
		self.delete_callback = None
	def put(self, url, headers={}, data="", proxies={}):
		return self.put_callback(url, data)
	def get(self, url, headers={}, data="", proxies={}):
		return self.get_callback(url, data)
	def post(self, url, headers={}, data="", proxies={}):
		return self.post_callback(url, data)
	def delete(self, url, headers={}, data="", proxies={}):
		return self.delete_callback(url, data)
		
def raise_exception(url, data):
	raise Exception('common exception')
	return MockResponse('', 200)

def http_error_500(url, data):
	return MockResponse('', 500)

def invalid_json(url, data):
	return MockResponse('{}', 500)
	
class test_errors(unittest.TestCase):
	def setUp(self):
		self.connobj = MockSession()
		self.PC = PostConnector(self.connobj)
		self.PC.set_parameters()
	def test_exception(self):
		self.connobj.put_callback = raise_exception
		self.connobj.get_callback = raise_exception
		self.connobj.post_callback = raise_exception
		self.connobj.delete_callback = raise_exception
		#
		res = self.PC.add_backlog({})
		print("add_backlog")
		print(res)
		#
		print("add_backlogs")
		for i in self.PC.add_backlogs([{},{}]):
			print(i)
		#
		res = self.PC.add_batch(datetime.now(), [0,0])
		print("add_batch")
		print(res)
		#
		print("remove_backlogs")
		for i in self.PC.remove_backlogs([0,0]):
			print(i)
	def test_httperror(self):
		self.connobj.put_callback = http_error_500
		self.connobj.get_callback = http_error_500
		self.connobj.post_callback = http_error_500
		self.connobj.delete_callback = http_error_500
		#
		res = self.PC.add_backlog({})
		print("add_backlog")
		print(res)
		#
		print("add_backlogs")
		for i in self.PC.add_backlogs([{},{}]):
			print(i)
		#
		res = self.PC.add_batch(datetime.now(), [0,0])
		print("add_batch")
		print(res)
		#
		print("remove_backlogs")
		for i in self.PC.remove_backlogs([0,0]):
			print(i)
	
if __name__=='__main__':
	unittest.main()
