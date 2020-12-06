#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import redirect, request
from functools import wraps
from xaiecon.modules.core.helpers import obtain_logged_user

# Wants user to be logged in, otherwise just gives him "guest"
def login_wanted(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		u = obtain_logged_user()
		return f(u=u, *args, **kwargs)
	return wrapper

# Requires user to be logged in
def login_required(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		u = obtain_logged_user()
		if u is None:
			redirect('/user/login')
		return f(u=u, *args, **kwargs)
	return wrapper

# Administers response
def api(*scopes):
	def decorator(f):
		@wraps(f)
		def wrapper(*args, **kwargs):
			response = f(*args, **kwargs)
			if isinstance(response,dict):
				if request.path.startswith('/api/bot'):
					return response['html']
				else:
					return response['html']
			else:
				return response
		return wrapper
	return decorator