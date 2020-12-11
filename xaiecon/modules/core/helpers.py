#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests

from flask import request, session

from xaiecon.modules.core.markdown import md
from xaiecon.classes.base import open_db
from xaiecon.classes.user import User
from xaiecon.classes.apiapp import APIApp
from xaiecon.classes.notification import Notification
from xaiecon.classes.serverchain import Serverchain

# Sends an event to all instances
# 
def send_event(json):
	db = open_db()
	servers = db.query(Serverchain).all()
	for s in servers:
		headers = { 'User-Agent':'Xaiecon-Fediverse' }
		requests.post(url='https://{s.ip_addr}/fediverse/receive',headers=headers,json=json)
	db.close()

# Obtains current user/bot
def obtain_logged_user():
	db = open_db()
	
	# Set user to none, in case we did not declare it somewhere
	user = None
	
	# Obtain user, in this case it's a bot
	if request.path.startswith('/api/bot/'):
		token = request.headers.get('X-API-Key')
		if token is None:
			return None
		
		# Obtain app with token
		app = db.query(APIApp).filter_by(token=token).first()
		if app is None:
			return None
		
		# Obtain user that is assigned the app
		user = db.query(User).filter_by(id=app.user_id).first()
		if user is None:
			return None
	elif request.path.startswith('/fediverse/end/'):
		if not request.headers.getlist('X-Forwarded-For'):
			ip_addr = request.remote_addr
		else:
			ip_addr = request.headers.getlist('X-Forwarded-For')[0]
		
		server = db.query(Serverchain).filter_by(ip_addr=ip_addr).first()
		if server is None:
			return None
		
		return server
# (don't just copy/paste this -- keep reading)
	# Obtain user, normal user, not a bot hopefuly
	else:
		user = db.query(User).filter_by(id=session.get('id')).first()
		if user is None:
			return None
		
		if user.validate() == False:
			return None
		
		if user.is_banned == True:
			return None
	db.close()
	return user

def send_admin_notification(msg: str):
	db = open_db()
	
	admins = db.query(User).filter_by(is_admin=True).all()
	for a in admins:
		notification = Notification(
			body=msg,
			body_html=md(msg),
			user_id=a.id)
		db.add(notification)
		db.commit()
	
	db.close()

def send_everyone_notification(msg: str):
	db = open_db()
	
	users = db.query(User).all()
	for u in users:
		notification = Notification(
			body=msg,
			body_html=md(msg),
			user_id=u.id)
		db.add(notification)
		db.commit()
	
	db.close()

def send_notification(msg: str, target_id: int):
	db = open_db()
	
	notification = Notification(
		body=msg,
		body_html=md(msg),
		user_id=target_id)
	db.add(notification)
	db.commit()
	
	db.close()