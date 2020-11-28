#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Module that allows fediverse with other instances
#

# In short
# Our ActivityPub implementation uses E2E to communicate to other servers
# We need to have many privacy, because we do not want any eavesdropper
# To see a big list of posts without our consent. Business will love this.

# TODO: implement activitypub

import os

from flask import Blueprint, render_template, request, jsonify
from flask_babel import gettext

from xaiecon.classes.base import open_db
from xaiecon.classes.user import User
from xaiecon.classes.serverchain import Serverchain

from xaiecon.modules.core.wrappers import login_required

fediverse = Blueprint('fediverse',__name__,template_folder='templates/fediverse')

# Inbox for user
@fediverse.route('/acpub/user/<user_id>/inbox', methods = ['POST'])
def inbox(user_id=0):
	data = request.json
	
	if data['@context'] != 'https://www.w3.org/ns/activitystreams':
		return '',400
	
	atype = data.get('type')
	
	# Upvote
	if atype == 'Like':
		actor = data.get('actor')
		object = data.get('object')
		published = data.get('published')
		
		
	
	return '',201

# Return user object
@fediverse.route('/acpub/user/<user_id>/object', methods = ['GET'])
def user_object(user_id=0):
	db = open_db()
	user = db.query(User).filter_by(id=user_id).first()
	if user is None:
		return '',404
	
	data = {
		'@context':'https://www.w3.org/ns/activitystreams',
		'type':'Person',
		'id':f'https://{os.environ.get("DOMAIN_NAME")}/acpub/user/{user_id}/object',
		'following':f'https://{os.environ.get("DOMAIN_NAME")}/acpub/user/{user_id}/follwing',
		'followers':f'https://{os.environ.get("DOMAIN_NAME")}/acpub/user/{user_id}/follwers',
		'liked':f'https://{os.environ.get("DOMAIN_NAME")}/acpub/user/{user_id}/liked',
		'inbox':f'https://{os.environ.get("DOMAIN_NAME")}/acpub/user/{user_id}/inbox',
		'outbox':f'https://{os.environ.get("DOMAIN_NAME")}/acpub/user/{user_id}/outbox',
		'preferredUsername':f'{user.username}',
		'name':f'{user.name}',
		'summary':f'{user.biography}',
		'icon':[f'https://{os.environ.get("DOMAIN_NAME")}/user/thumb?uid={user_id}']
	}
	
	return jsonify(data),200

# After this, our server will gladly receive AP stuff from this IP
# And that IP will also be sent some of our info.
#
# The only step left is to contact the IP owner and tell them that
# we are linked
@fediverse.route('/fediverse/chain', methods = ['GET','POST'])
@login_required
def add_instance(u=None):
	if request.method == 'POST':
		db = open_db()
		
		serv = Serverchain(
			name=request.values.get('name',request.values.get('ip_addr')),
			ip_addr=request.values.get('ip_addr'))
		
		db.add(serv)
		db.commit()
		db.close()
		return 'Server added!',200
	else:
		return render_template('fediverse/add.html',u=u,title='Add instance')

print('Fediverse module ... ok')