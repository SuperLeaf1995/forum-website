#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Module that allows fediverse with other instances
#

# TODO: implement activitypub

import os
import requests
import json

from flask import Blueprint, render_template, request, jsonify, make_response, abort
from flask_babel import gettext

from werkzeug.security import generate_password_hash

from xaiecon.classes.base import open_db
from xaiecon.classes.comment import Comment
from xaiecon.classes.post import Post
from xaiecon.classes.user import User
from xaiecon.classes.vote import Vote
from xaiecon.classes.category import Category
from xaiecon.classes.board import Board
from xaiecon.classes.view import View
from xaiecon.classes.oauthapp import OAuthApp
from xaiecon.classes.apiapp import APIApp
from xaiecon.classes.notification import Notification
from xaiecon.classes.serverchain import Serverchain
from xaiecon.modules.core.wrappers import login_required

from sqlalchemy.orm import joinedload

fediverse = Blueprint('fediverse',__name__,template_folder='templates/fediverse')

# Return object for other instances to fetch
@fediverse.route('/fediverse/end/<_type>/<id>')
def return_object(_type='Post',id=0):
	db = open_db()
	
	types = [
		'Post','User','Comment',
		'Vote','Category','Board',
		'View','OAuthApp','APIApp',
		'Notification'
	]
	
	if _type not in types:
		return jsonify({'error':'Unknown type'})
	
	if _type == 'Post':
		obj = Post
	elif _type == 'User':
		obj = User
	elif _type == 'Comment':
		obj = Comment
	elif _type == 'Vote':
		obj = Vote
	elif _type == 'Category':
		obj = Category
	elif _type == 'Board':
		obj = Board
	elif _type == 'View':
		obj = View
	elif _type == 'OAuthApp':
		obj = OAuthApp
	elif _type == 'APIApp':
		obj = APIApp
	elif _type == 'Notification':
		obj = Notification
	else:
		return jsonify({'error':'Unknown type'})
	
	data = db.query(_type).filter_by(id=id).first()
	if data is None:
		return jsonify({'error':f'{type(data).__name__} with id {id} does not exist here'}),404
	
	data = data.json
	
	if _type == 'User':
		string = f'{data["password"]}:{data["id"]}'
		auth_token = generate_password_hash(string)
		data['auth_token'] = auth_token
	
	db.close()
	return jsonify(data),200

# After this, our server will gladly receive AP stuff from this IP
# And that IP will also be sent some of our info.
#
# The only step left is to contact the IP owner and tell them that
# we are linked
@fediverse.route('/fediverse/chain', methods = ['GET','POST'])
@login_required
def add_instance(u=None):
	if u.is_admin == False:
		abort(403)
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