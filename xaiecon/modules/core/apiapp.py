#
# Simple post-sharing base module
#

import secrets

from flask import Blueprint, render_template, request, session, jsonify, redirect, send_from_directory, abort, send_file
from werkzeug.utils import secure_filename
from xaiecon.cache import cache

from xaiecon.classes.base import open_db
from xaiecon.classes.user import *
from xaiecon.classes.log import *
from xaiecon.classes.apiapp import *
from xaiecon.classes.exception import *

from xaiecon.modules.core.wrappers import *

from distutils.util import *

from sqlalchemy.orm import joinedload
from sqlalchemy import desc

apiapp = Blueprint('apiapp',__name__,template_folder='templates/apiapp')

@apiapp.route('/apiapp/new', methods = ['GET','POST'])
@login_required
def new(u=None):
	try:
		if request.method == 'POST':
			name = request.values.get('name')
			
			db = open_db()
			
			aapp = APIApp(
				token=secrets.token_urlsafe(64),
				name=name,
				user_id=u.id)
			
			db.add(aapp)
			db.commit()
			
			# db.refresh(oauth)
			
			db.close()
			return redirect('/apiapp/view')
		else:
			return render_template('apiapp/new.html',u=u,title='New OAuth App')
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@apiapp.route('/apiapp/view', methods = ['GET','POST'])
@login_required
def view_all(u=None):
	try:
		db = open_db()
		
		apps = db.query(APIApp).filter_by(user_id=u.id).all()
		
		db.close()
		return render_template('apiapp/view.html',u=u,title='Your apps',apps=apps)
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@apiapp.route('/apiapp/delete', methods = ['GET','POST'])
@login_required
def delete(u=None):
	try:
		# Delete specified app
		id = request.values.get('aid')
		
		db = open_db()
		
		db.query(APIApp).filter_by(user_id=u.id,id=id).delete()
		db.commit()
		
		db.close()
		return redirect('/apiapp/view')
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@apiapp.route('/apiapp/reroll', methods = ['GET','POST'])
@login_required
def reroll(u=None):
	try:
		# Reroll tokens for specified app
		id = request.values.get('aid')
		
		db = open_db()
		
		db.query(APIApp).filter_by(user_id=u.id,id=id).update({
			'token':secrets.token_urlsafe(127)
		})
		db.commit()
		
		db.close()
		return redirect('/apiapp/view')
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

print('Post share ... ok')
