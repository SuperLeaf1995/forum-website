import requests
import time
import sys
import os

from xaiecon.classes.base import open_db

os.environ['SQLALCHEMY_URL'] = 'postgresql://postgres:postgres@localhost/test'
os.environ['DOMAIN_NAME'] = 'localhost:5000'

from xaiecon.__init__ import app

# Wait lots of seconds for server to start
# see issue https://gitlab.com/gitlab-org/gitlab-runner/-/issues/1552
print('Waiting for database to start')
time.sleep(20)

# Do tests to assure quality!
def test():
	if app is None:
		sys.exit('App not created')
	
	headers = {'User-Agent':'python-webtester'}
	
	# Test 1: Database connection
	print('Testing database connection')
	db = open_db()
	db.create_all()
	db.close()
	
	# Test 2: Test most visited and relevant endpoints
	print('Testing most visited endpoinsts')
	endpoints = [
		'',
		'user/leaderboard',
		'post/list/new']
	for e in endpoints:
		print(f'Testing /{e}')
		x = requests.get(f'http://{app.config["DOMAIN_NAME"]}/{e}',headers=headers)
		if x.status_code not in [200]:
			sys.exit('Invalid answer for {e}, expected 200 got {x.status_code} instead')
	
	# TODO: Add even more tests

test()