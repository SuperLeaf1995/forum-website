from flask import session, redirect
from xaiecon.classes.base import open_db
from xaiecon.classes.user import User
from functools import wraps

# Wants user to be logged in, otherwise just gives him "guest"
def login_wanted(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		db = open_db()
		user = db.query(User).filter_by(id=session.get('id')).first()
		if user is None or user.validate() == False:
			u = None
		u = user
		db.close()
		return f(u=u, *args, **kwargs)
	return wrapper

# Requires user to be logged in
def login_required(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		db = open_db()
		user = db.query(User).filter_by(id=session.get('id')).first()
		if user is None or user.validate() == False:
			return redirect('/user/login')
		if user.is_banned == True:
			abort(403)
		u = user
		db.close()
		return f(u=u, *args, **kwargs)
	return wrapper