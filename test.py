import requests
import time
import sys
import os

from xaiecon.classes.base import open_db

os.environ['SQLALCHEMY_URL'] = 'postgresql://postgres@localhost/test'
os.environ['DOMAIN_NAME'] = 'localhost:5000'

#from xaiecon.__init__ import app

from xaiecon.factory import create_app
app = create_app()
if __name__ == '__main__':
	app.run(host='0.0.0.0',port=5000)

# Wait 3 seconds for server to start
time.sleep(3)

# Do tests to assure quality!
def test():
	if app is None:
		sys.exit('App not created')
	
	headers = {'User-Agent':'python-webtester'}
	
	# Test 1: Database connection
	db = open_db()
	db.create_all()
	db.close()
	
	# Test 2: Test most visited and relevant endpoints
	endpoints = [
		'',
		'user/leaderboard',
		'post/list/new']
	for e in endpoints:
		x = requests.get(f'http://{app.config["DOMAIN_NAME"]}/{e}',headers=headers)
		if x.status_code not in [200]:
			sys.exit('Invalid answer for {e}, expected 200 got {x.status_code} instead')
	
	# TODO: Add even more tests

test()