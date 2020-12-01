import requests
import os
import sys

from xaiecon.classes.base import open_db
from xaiecon.__init__ import app

# Wait 3 seconds for server to start
os.sleep(3)

# Do tests to assure quality!
def test():
	if app is None:
		sys.exit('App not created')
	
	headers = {'User-Agent':'python-webtester'}
	
	# Test 1: Test most visited and relevant endpoints
	endpoints = [
		'',
		'user/leaderboard',
		'post/list/new']
	for e in endpoints:
		x = requests.get(f'http://{app.config["DOMAIN_NAME"]}/{e}',headers=headers)
		if x.status_code not in [200]:
			sys.exit('Invalid answer for {e}, expected 200 got {x.status_code} instead')
	
	# Test 2: Database connection
	db = open_db()
	db.close()
	
	# TODO: Add even more tests

test()