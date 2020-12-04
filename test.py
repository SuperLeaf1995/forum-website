import requests
import time
import sys
import os
import unittest

from xaiecon.classes.base import open_db
from xaiecon.__init__ import app

os.environ['SQLALCHEMY_URL'] = 'postgresql://postgres:postgres@postgres:5432/xaiecon_test'

class TestFlaskApp(unittest.TestCase):
	def test_database(self):
		db = open_db()
		db.close()
	
	# TODO: Add even more tests

if __name__ == '__main__':
	unittest.main()
