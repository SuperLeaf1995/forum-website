#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import request, session
from flask_misaka import markdown

from xaiecon.classes.base import open_db
from xaiecon.classes.user import User
from xaiecon.classes.apiapp import APIApp
from xaiecon.classes.notification import Notification

# Obtains current user/bot
def obtain_logged_user():
	db = open_db()
	
	# Set user to none, in case we did not declare it somewhere
	user = None
	
	# Obtain user, in this case it's a bot
	if request.path.startswith('/api/v1/'):
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
		
	# Obtain user, normal user, not a bot hopefuly
	else:
		user = db.query(User).filter_by(id=session.get('id')).first()
		if user is None or user.validate() == False:
			return None
		if user.is_banned == True:
			return None
	db.close()
	return user

def send_notification(msg: str, target_id: int):
	db = open_db()
	
	notification = Notification(
		body=msg,
		body_html=markdown(msg),
		user_id=target_id)
	db.add(notification)
	db.commit()
	
	db.close()