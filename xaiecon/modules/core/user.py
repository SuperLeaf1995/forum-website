#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Simple user log-in and sign-up module if you want to remove this
# module, make sure to also remove the posts module
#

from PIL import Image

import os
import threading
import requests
import secrets
import time
import random

from flask import Blueprint, render_template, session, request, redirect, abort, send_from_directory
from flask_babel import gettext

from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from xaiecon.classes.base import open_db
from xaiecon.classes.user import User
from xaiecon.classes.notification import Notification

from xaiecon.classes.exception import XaieconException

from xaiecon.modules.core.hcaptcha import hcaptcha
from xaiecon.modules.core.helpers import send_notification
from xaiecon.modules.core.wrappers import login_wanted, login_required

from sqlalchemy import desc

from distutils.util import strtobool

user = Blueprint('user',__name__,template_folder='templates/user')

@user.route('/user/login', methods = ['GET','POST'])
@login_wanted
def login(u=None):
	try:
		if request.method == 'POST':
			if len(request.form.get('password')) == 0:
				raise XaieconException(gettext('Please input a password'))
			if len(request.form.get('username')) == 0:
				raise XaieconException(gettext('Please input a username'))
			
			username = request.form.get('username')
			
			# Select data of SQL database
			db = open_db()
			users = db.query(User).filter_by(username=username).all()
			if users == None:
				raise XaieconException(gettext('Invalid username or password'))
			
			for data in users:
				rbool = check_password_hash(data.password,request.form.get('password'))
				if rbool == True:
					# Update auth token, and put it in our session cookie
					string = f'{data.password}:{data.id}'
					auth_token = generate_password_hash(string)
					
					db.query(User).filter_by(id=data.id).update({'auth_token':auth_token})
					
					db.commit()
					
					session['auth_token'] = auth_token
					session['username'] = username
					session['id'] = data.id
					
					db.close()
					
					# We now have everything in the session!
					return redirect('/')
			
			db.rollback()
			db.close()
			raise XaieconException(gettext('Invalid username or password'))
		else:
			return render_template('user/login.html',u=u,login_error='',title='Login')
	except XaieconException as e:
		return render_template('user/login.html',u=u,login_error=e,title='Login')

@user.route('/user/signup', methods = ['GET','POST'])
@login_wanted
def signup(u=None):
	try:
		if request.method == 'POST':
			# Validate form data
			if len(request.form.get('password','')) < 6:
				raise XaieconException('Please input a password atleast of 6 characters')
			if len(request.form.get('username','')) < 4:
				raise XaieconException('Please input a username atleast of 4 characters')
			
			if len(request.form.get('agree_tos','')) == 0:
				raise XaieconException('Agree to the terms, privacy policy and content policy')
			
			# Hash the password
			password = generate_password_hash(request.form.get('password'))
			
			# Create the auth_token of form {username}:{password}
			string = f'{password}:{id}'
			auth_token = generate_password_hash(string)
			
			# Open the database
			db = open_db()
			
			pics = ['golden.png','blue.png','jelly.png','crab.png']
			
			# Create new user and add it to database
			new_user = User(username=request.form.get('username'),
							password=password,
							auth_token=auth_token,
							fallback_thumb=random.choice(pics))
			db.add(new_user)
			db.commit()
			
			db.refresh(new_user)
			
			# Set session
			session['auth_token'] = auth_token
			session['username'] = request.form.get('username')
			session['id'] = new_user.id
			
			send_notification(gettext(f'Thanks for registering, feel free to [create your first post](/post/create) or [explore the frontpage](/post/list?sort=new)'),new_user.id)
			
			# Finally, end ;)
			db.close()
			
			return redirect(f'/user/view?uid={new_user.id}')
		else:
			return render_template('user/signup.html',u=u,signup_error='',title='Signup')
	except XaieconException as e:
		return render_template('user/signup.html',u=u,signup_error=e,title='Signup')

@user.route('/user/logout', methods = ['GET'])
def logout():
	session.pop('auth_token', None)
	session.pop('username', None)
	session.pop('id', None)
	return redirect('/')

@user.route('/user/notifications', methods = ['GET'])
@login_required
def notifications(u=None):
	db = open_db()
	
	# Mark all notifications as read
	notifications = db.query(Notification).filter_by(user_id=u.id,is_read=False).all()
	
	db.close()
	return render_template('user/notification.html',u=u,title='Your notifications',notifications=notifications)

@user.route('/user/mark_all', methods = ['GET'])
@login_required
def mark_all_as_read(u=None):
	db = open_db()
	db.query(Notification).filter_by(user_id=u.id).update({'is_read':True})
	db.commit()
	db.close()
	return redirect('/user/notifications')

@user.route('/user/leaderboard', methods = ['GET'])
@login_wanted
def netpoint_leaderboard(u=None,username=None):
	db = open_db()
	user = db.query(User).order_by(desc(User.net_points)).limit(50).all()
	if user is None:
		abort(404)
	db.close()
	
	return render_template('user/leaderboard.html',u=u,title='Network Points Leaderboard',users=user)

@user.route('/u/<username>', methods = ['GET'])
@login_wanted
def view_by_username(u=None,username=None):
	db = open_db()
	user = db.query(User).filter(User.username.ilike(username)).all()
	if user is None:
		abort(404)
	db.close()
	
	if len(user) > 1:
		random.shuffle(user)
		return render_template('user/pick.html',u=u,title=username,username=username,user=user,len=len(user))
	return redirect(f'/user/view?uid={user[0].id}')

@user.route('/user/view', methods = ['GET'])
@login_wanted
def view_by_id(u=None):
	id = request.values.get('uid')
	
	db = open_db()
	user = db.query(User).filter_by(id=id).first()
	if user is None:
		abort(404)
	
	db.close()
	
	return render_template('user/info.html',u=u,title=user.username,user=user)

@user.route('/user/thumb', methods = ['GET','POST'])
@login_wanted
def thumb(u=None):
	uid = int(request.values.get('uid','0'))
	db = open_db()
	user = db.query(User).filter_by(id=uid).first()
	if user is None:
		abort(404)
	
	db.close()
	
	if user.image_file is None:
		return send_from_directory('assets/public/pics',user.fallback_thumb)
	if os.path.isfile(os.path.join('user_data',user.image_file)) == False:
		return send_from_directory('assets/public/pics',user.fallback_thumb)
	return send_from_directory('../user_data',user.image_file)

@user.route('/user/edit', methods = ['GET','POST'])
@login_required
def edit(u=None):
	try:
		id = int(request.values.get('uid',''))

		db = open_db()
		user = db.query(User).filter_by(id=id).first()
		if user is None:
			abort(404)

		if u.id != id and u.is_admin == False:
			raise XaieconException(gettext('Not authorized'))

		if request.method == 'POST':
			# Get stuff
			email = request.form.get('email')
			fax = request.form.get('fax')
			phone = request.form.get('phone')
			biography = request.form.get('biography')
			
			# Update our user information
			is_show_email = strtobool(request.form.get('is_show_email','False'))
			is_show_fax = strtobool(request.form.get('is_show_fax','False'))
			is_show_phone = strtobool(request.form.get('is_show_phone','False'))
			is_nsfw = strtobool(request.form.get('is_nsfw','False'))
			
			db.query(User).filter_by(id=id).update({
						'biography':biography,
						'email':email,
						'is_show_email':is_show_email,
						'fax':fax,
						'is_show_fax':is_show_fax,
						'phone':phone,
						'is_show_phone':is_show_phone,
						'is_nsfw':is_nsfw})
			db.commit()
			db.refresh(user)

			file = request.files['profile']
			if file:
				# Remove old image
				if user.image_file is not None:
					try:
						os.remove(os.path.join('user_data',user.image_file))
					except FileNotFoundError:
						pass
				
				# Create thumbnail
				filename = f'{secrets.token_hex(32)}.jpeg'
				filename = secure_filename(filename)

				final_filename = os.path.join('user_data',filename)

				file.save(final_filename)

				image = Image.open(final_filename)
				image = image.convert('RGB')
				image.thumbnail((120,120))
				os.remove(final_filename)
				image.save(final_filename)

				db.query(User).filter_by(id=id).update({'image_file':filename})
				db.commit()

				csam_thread = threading.Thread(target=csam_check_profile, args=(id,))
				csam_thread.start()

			db.close()
			return redirect(f'/user/view?uid={id}')
		else:
			db.close()
			return render_template('user/edit.html',u=u,title=f'Editing {user.username}',user=user)
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

# Check user for csam, if so ban the user
def csam_check_profile(uid: int):
	db = open_db()

	# Let's see if this is csam
	user = db.query(User).filter_by(id=uid).first()

	headers = {'User-Agent':'xaiecon-csam-check'}

	for i in range(10):
		x = requests.get(f'https://{os.environ.get("DOMAIN_NAME")}/user/thumb?uid={uid}',headers=headers)
		if x.status_code in [200, 451]:
			break
		else:
			time.sleep(10)
	
	if x.status_code != 451:
		return

	# Ban user
	db.query(User).filter_by(id=id).update({
		'ban_reason':gettext('CSAM Automatic Removal'),
		'is_banned':True})
	db.commit()
	db.refresh(user)

	os.remove(os.path.join('user_data',user.image_file))
	
	db.close()
	return

print('User system ... ok')
