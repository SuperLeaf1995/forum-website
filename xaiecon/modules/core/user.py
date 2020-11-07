#
# Simple user log-in and sign-up module if you want to remove this
# module, make sure to also remove the posts module
#

from flask import Blueprint, render_template, session, request, redirect, abort

from werkzeug.security import check_password_hash, generate_password_hash
from xaiecon.modules.core.cache import cache

from xaiecon.classes.base import open_db
from xaiecon.classes.user import User
from xaiecon.classes.exception import XaieconException

from xaiecon.modules.core.hcaptcha import hcaptcha
from xaiecon.modules.core.wrappers import login_wanted, login_required

from distutils.util import *

import random

user = Blueprint('user',__name__,template_folder='templates/user')

def create_unique_identifier(n=250):
	string = str(''.join(random.choices('abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ',k=n)))
	return string

@user.route('/user/login', methods = ['GET','POST'])
@login_wanted
def user_login(u=None):
	try:
		if request.method == 'POST':
			if session.get('agreed_gdpr') is None:
				raise XaieconException('To login, we require to set cookies on your browser, please be kind and allow us to store cookies.')

			if len(request.form.get('password')) <= 0:
				raise XaieconException('Please input a password')
			if len(request.form.get('username')) <= 0:
				raise XaieconException('Please input a username')
			
			username = request.form.get('username')
			
			# Select data of SQL database
			db = open_db()
			users = db.query(User).filter_by(username=username).all()
			if users == None:
				raise XaieconException('Invalid username or password')
			
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
			raise XaieconException('Invalid username or password')
		else:
			return render_template('user/login.html',u=u,login_error='',title='Login')
	except XaieconException as e:
		return render_template('user/login.html',u=u,login_error=e,title='Login')

@user.route('/user/signup', methods = ['GET','POST'])
@login_wanted
def user_signup(u=None):
	try:
		if request.method == 'POST':
			#if not hcaptcha.verify():
			#	raise XaieconException('Please complete hcaptcha')
			
			if session.get('agreed_gdpr') is None:
				raise XaieconException('To signup, we require to set cookies on your browser, please be kind and allow us to store cookies.')

			# Validate form data
			if len(request.form.get('password')) < 6:
				raise XaieconException('Please input a password atleast of 6 characters')
			if len(request.form.get('name')) == 0:
				raise XaieconException('Please input a name')
			if len(request.form.get('username')) < 4:
				raise XaieconException('Please input a username atleast of 4 characters')
			
			# Hash the password
			password = generate_password_hash(request.form.get('password'))
			
			# Create the auth_token of form {username}:{password}
			string = f'{password}:{id}'
			auth_token = generate_password_hash(string)
			
			# Open the database
			db = open_db()
			
			# Create new user and add it to database
			new_user = User(name=request.form.get('name'),
							username=request.form.get('username'),
							password=password,
							auth_token=auth_token)
			db.add(new_user)
			db.commit()
			
			db.refresh(new_user)
			
			# Set session
			session['auth_token'] = auth_token
			session['username'] = request.form.get('username')
			session['id'] = new_user.id
			
			# Finally, end ;)
			db.close()
			
			return redirect(f'/user/view?id={new_user.id}')
		else:
			return render_template('user/signup.html',u=u,signup_error='',title='Signup')
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user/signup.html',u=u,signup_error=e,title='Signup')

@user.route('/user/logout', methods = ['GET'])
def user_logout():
	session.pop('auth_token', None)
	session.pop('username', None)
	session.pop('id', None)
	return redirect('/')

@user.route('/u/<username>', methods = ['GET'])
@login_wanted
def user_view_by_username(u=None,username=None):
	db = open_db()
	user = db.query(User).filter_by(username=username).all()
	if user is None:
		abort(404)
	db.close()
	
	if len(user) == 1:
		return redirect(f'/user/view/{user.id}')
	return render_template('user/pick.html',u=u,title=username,username=username,user=user,len=len(user))

@user.route('/user/view', methods = ['GET'])
@login_wanted
def user_view_by_id(u=None):
	id = request.values.get('uid')
	
	db = open_db()
	user = db.query(User).filter_by(id=id).first()
	if user is None:
		abort(404)
	
	db.close()
	
	return render_template('user/info.html',u=u,title=user.username,user=user)

@user.route('/user/edit', methods = ['GET','POST'])
@login_required
def user_edit(u=None):
	try:
		id = request.values.get('uid')
		
		db = open_db()
		user = db.query(User).filter_by(id=id).first()
		if u.id != id and u.is_admin == False:
			raise XaieconException('Not authorized')
		
		if request.method == 'POST':
			# Get stuff
			email = request.form.get('email')
			fax = request.form.get('fax')
			phone = request.form.get('phone')
			
			# Update our user information
			if request.form.get('is_show_email'):
				is_show_email = True
			else:
				is_show_email = False
			
			if request.form.get('is_show_fax'):
				is_show_fax = True
			else:
				is_show_fax = False
			
			if request.form.get('is_show_phone'):
				is_show_phone = True
			else:
				is_show_phone = False
			
			if request.form.get('is_nsfw'):
				is_nsfw = True
			else:
				is_nsfw = False
			
			biography = request.form.get('biography')
			
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
			db.close()
			return redirect(f'/user/view?uid={id}')
		else:
			db.close()
			return render_template('user/edit.html',u=u,title=f'Editing {user.username}',user=user)
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

print('User system ... ok')
