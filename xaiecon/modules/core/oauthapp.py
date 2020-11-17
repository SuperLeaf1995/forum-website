#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 23:29:08 2020

@author: superleaf1995
"""

# TODO: Finish this

import secrets

from flask import Blueprint, render_template, request, redirect

from xaiecon.classes.base import open_db
from xaiecon.classes.oauthapp import OAuthApp
from xaiecon.classes.exception import XaieconException

from xaiecon.modules.core.wrappers import login_required

oauthapp = Blueprint('apiapp',__name__,template_folder='templates/apiapp')

@oauthapp.route('/oauth/new', methods = ['GET','POST'])
@login_required
def new(u=None):
	try:
		if request.method == 'POST':
			name = request.values.get('name')
			redirect_uri = request.values.get('redirect_uri')
			
			if name is None:
				name = 'Untitled oauth app'
			if redirect_uri == '':
				raise XaieconException('Please provide a redirect url')
			
			db = open_db()
			
			# Create app, with tokens and client id and stuff
			app = OAuthApp(
				client_id=secrets.token_urlsafe(128)[0:128],
				client_secret=secrets.token_urlsafe(128)[0:128],
				redirect_uri=redirect_uri,
				name=name,
				user_id=u.id)
			
			db.add(app)
			db.commit()
			
			db.close()
			return redirect('/oauth/view')
		else:
			return render_template('oauth/new.html',u=u,title='New OAuth App')
	except XaieconException as e:
		return render_template('user_error.html',u=u,title='Whoops!',err=e)

print('OAuthApp routes ... ok')
