from flask import redirect
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