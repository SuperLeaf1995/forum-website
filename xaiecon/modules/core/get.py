from flask import session
from xaiecon.classes.base import open_db
from xaiecon.classes.user import User

def fediverse_user(user=None):
	if user is None:
		return None
