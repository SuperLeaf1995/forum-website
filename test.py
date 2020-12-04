import requests
import os
import unittest
import threading

from xaiecon.classes.base import open_db
from xaiecon.__init__ import app

os.environ['SQLALCHEMY_URL'] = 'postgresql://postgres:postgres@postgres:5432/xaiecon_test'

class TestFlaskApp(unittest.TestCase):
	def test_database(self):
		db = open_db()
		db.close()
	
	def test_app(self):
		x = threading.Thread(target=app_start)
		x.daemon = True
		x.start()
		
		headers = {'User-Agent':'webapp-tester'}
		resp = requests.get('http://localhost:5000/',headers=headers)
		print(resp)
	
	# TODO: Add even more tests

def app_start():
	os.environ['FLASK_APP'] = 'xaiecon'
	os.environ['FLASK_ENV'] = 'developement'
	os.environ['DOMAIN_NAME'] = 'localhost:5000'
	app.run()

if __name__ == '__main__':
	unittest.main()
	sys.exit()