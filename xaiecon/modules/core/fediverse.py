#
# Module that allows fediverse with other instances
#

import requests

from flask import Blueprint, render_template, request
from xaiecon.modules.core.cache import cache

from xaiecon.classes.base import open_db
from xaiecon.classes.post import Post
from xaiecon.classes.user import User
from xaiecon.classes.board import Board
from xaiecon.classes.serverchain import Serverchain
from xaiecon.classes.exception import XaieconException

from xaiecon.modules.core.wrappers import login_wanted, login_required

fediverse = Blueprint('fediverse',__name__,template_folder='templates/fediverse')
#
# Tells the other instance that we want to be chained
#
@fediverse.route('/fediverse/chain', methods = ['GET','POST'])
@login_required
def chaining_request(u=None):
	try:
		if u.is_admin == False:
			raise XaieconException('Not authorized')
		
		if request.method == 'POST':
			ip_addr = request.values.get('ip_addr','').rstrip('/')
			if ip_addr == '':
				return '',400
			
			data = {'requester':request.url_root}
			url = f'{ip_addr}/fediverse/counter_chain'
			response = requests.post(url,data)
			
			if not response.ok:
				raise XaieconException('Server that you tried to chain with is down, or has weird endpoint')
			return '',200
		else:
			return render_template('fediverse/chain.html',u=u,title = 'Add instance')
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

#
# Entry point for instances requesting chaining
#
@fediverse.route('/fediverse/counter_chain', methods = ['POST'])
@login_required
def chaining_entry(u=None):
	try:
		ip_addr = request.values.get('requester','').rstrip('/')
		if ip_addr == '':
			return '',400
		db = open_db()
		
		server = Serverchain(ip_addr=ip_addr,name='Chaining')
		db.add(server)
		db.commit()
		
		db.close()
		return '',200
	except XaieconException as e:
		return e,400

print('Fediverse module ... ok')
