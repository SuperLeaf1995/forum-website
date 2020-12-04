import requests
import os
import unittest
import threading
import sys
import time

from bs4 import BeautifulSoup

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
		
		time.sleep(1)
		
		headers = {'User-Agent':'webapp-tester'}
		endpoints = [
			{
				'endpoint':'',
				'method':'GET',
				'params':None,
				'accept_status':[200]
			},{
				'endpoint':'post/list',
				'method':'GET',
				'params':None,
				'accept_status':[200]
			},{
				'endpoint':'user/leaderboard',
				'method':'GET',
				'params':None,
				'accept_status':[200]
			},{
				'endpoint':'user/login',
				'method':'GET',
				'params':None,
				'accept_status':[200]
			},{
				'endpoint':'user/signup',
				'method':'GET',
				'params':None,
				'accept_status':[200]
			},{
				'endpoint':'user/logout',
				'method':'GET',
				'params':None,
				'accept_status':[200,302]
			},{
				'endpoint':'post/list/All/new/1',
				'method':'GET',
				'params':None,
				'accept_status':[200]
			},{
				'endpoint':'post/list/All/new/not_a_number',
				'method':'GET',
				'params':None,
				'accept_status':[404]
			},{
				'endpoint':'favicon.ico',
				'method':'GET',
				'params':None,
				'accept_status':[200]
			}
		]
		
		for e in endpoints:
			if e['method'].startswith('GET'):
				method = requests.get
			elif e['method'].startswith('POST'):
				method = requests.post
			
			data = None
			if e['params'] is not None:
				data = e['params']
			
			resp = method(f'http://localhost:5000/{e["endpoint"]}',headers=headers,data=data)
			self.assertTrue(resp.status_code in e['accept_status'])
			
			if e['method'] == 'GET':
				# Check that given webpages are valid HTML5
				soup = BeautifulSoup(resp.text,"html.parser")
				
				# Check that soup has all semantically correct html
				self.assertNotEqual(soup.find('html'),None)
				self.assertNotEqual(soup.find('body'),None)
				
				# Check OpenGraph
				self.assertNotEqual(soup.find('meta',property='og:description'),None)
				self.assertNotEqual(soup.find('meta',property='og:url'),None)
				
				# Check that there aren't any broken links on any page
				links = soup.find_all('a')
				for a in links:
					if a.get('href') == '' or a.get('href') is None or a.get('href').startswith('/') or a.get('href').startswith('#'):
						continue
					
					x = requests.get(a['href'],headers=headers)
					self.assertTrue(x.status_code in [200,302,303,304])
	
	# TODO: Add even more tests

def app_start():
	os.environ['FLASK_APP'] = 'xaiecon'
	os.environ['FLASK_ENV'] = 'developement'
	os.environ['DOMAIN_NAME'] = 'localhost:5000'
	app.run()

if __name__ == '__main__':
	unittest.main()
	sys.exit()