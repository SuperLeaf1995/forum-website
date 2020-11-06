#
# Simple user log-in and sign-up module if you want to remove this
# module, make sure to also remove the posts module
#

from flask import Blueprint, render_template, session, request, redirect, abort
from werkzeug.security import check_password_hash, generate_password_hash
from xaiecon.cache import cache

from xaiecon.classes.base import open_db
from xaiecon.classes.user import *
from xaiecon.classes.exception import *

from xaiecon.modules.core.wrappers import *

from distutils.util import *

import random
import re

user = Blueprint('user',__name__,template_folder='templates/user')

def create_unique_identifier(n=250):
	string = str(''.join(random.choices('abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ',k=n)))
	return string

@user.route('/user/login', methods = ['GET','POST'])
@login_wanted
def user_login(u=None):
	try:
		if request.method == 'POST':
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
					string = '{}:{}'.format(data.unique_identifier,data.password)
					auth_token = generate_password_hash(string)
					
					db.query(User).filter_by(unique_identifier=data.unique_identifier).update({'auth_token':auth_token})
					
					db.commit()
					
					session['auth_token'] = auth_token
					session['username'] = username
					session['id'] = data.id
					session['uid'] = data.unique_identifier
					
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
			# Validate form data
			if len(request.form.get('password')) < 6:
				raise XaieconException('Please input a password atleast of 6 characters')
			if len(request.form.get('name')) == 0:
				raise XaieconException('Please input a name')
			if len(request.form.get('username')) < 4:
				raise XaieconException('Please input a username atleast of 4 characters')
			
			# Hash the password
			password = generate_password_hash(request.form.get('password'))
			
			# Generate unique identifier
			unique_identifier = create_unique_identifier()
			
			# Create the auth_token of form {username}:{password}
			string = '{}:{}'.format(unique_identifier,password)
			auth_token = generate_password_hash(string)
			
			# Open the database
			db = open_db()
			
			# Create new user and add it to database
			new_user = User(name=request.form.get('name'),
							username=request.form.get('username'),
							password=password,
							auth_token=auth_token,
							unique_identifier=unique_identifier)
			db.add(new_user)
			db.commit()
			
			# Set session
			session['auth_token'] = auth_token
			session['username'] = request.form.get('username')
			session['uid'] = unique_identifier
			
			# Get user id and add it to the session
			get_id = db.query(User).filter_by(username = request.form.get('username'), auth_token = auth_token).first()
			session['id'] = get_id.id
			
			# Finally, end ;)
			db.close()
			
			return redirect(f'/user/view/{unique_identifier}')
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

@user.route('/u/<username>#<id>', methods = ['GET'])
@login_wanted
def user_view_by_username(u=None,username=None,id=None):
	db = open_db()
	user = db.query(User).filter_by(username=username).all()
	if user == None:
		abort(404)
	db.close()
	
	if len(user) == 1:
		return redirect(f'/user/view/{user.unique_identifier}')
	return redirect(f'/user/view/{user[id].unique_identifier}')

@user.route('/u/<username>', methods = ['GET'])
@login_wanted
def user_view_by_username(u=None,username=None):
	db = open_db()
	user = db.query(User).filter_by(username=username).all()
	if user == None:
		abort(404)
	db.close()
	
	if len(user) == 1:
		return redirect(f'/user/view/{user.unique_identifier}')
	return render_template('user/pick.html',u=u,title=username,username=username,user=user,len=len(user))

@user.route('/user/view/<unique_identifier>', methods = ['GET'])
@login_wanted
def user_view_by_unique_identifier(u=None,unique_identifier=None):
	db = open_db()
	user = db.query(User).filter_by(unique_identifier=unique_identifier).first()
	if user == None:
		abort(404)
	
	db.close()
	return render_template('user/info.html',u=u,title=user.username,user=user)

@user.route('/user/edit/<uid>', methods = ['GET','POST'])
@login_required
def user_edit(u=None,uid=None):
	try:
		if request.method == 'POST':
			db = open_db()
			
			if u.unique_identifier != uid and u.is_admin == False:
				raise XaieconException('Not authorized')
			
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
			
			db.query(User).filter_by(unique_identifier=uid).update({
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
			return redirect(f'/user/view/{uid}')
		else:
			db = open_db()
			user = db.query(User).filter_by(unique_identifier=uid).first()
			if u.unique_identifier != uid and u.is_admin == False:
				raise XaieconException('Not authorized')
			db.close()
			return render_template('user/edit.html',u=u,title=f'Editing {user.username}',user=user)
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

print('User system ... ok')
