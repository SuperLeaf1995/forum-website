#
# Simple public logging module
#

from os import environ, path, remove
from flask import Blueprint, render_template, request, session, jsonify, redirect
from xaiecon.cache import cache

from xaiecon.classes.base import open_db
from xaiecon.classes.log import *

from xaiecon.modules.core.wrappers import *

logs = Blueprint('logs',__name__,template_folder='templates/logs')

@logs.route('/logs/public', methods = ['GET'])
@login_wanted
def showlogs(u=None):
	try:
		db = open_db()
		
		logs = db.query(Log).all()
		if logs == None:
			raise Exception('No logs :/')
		
		res = render_template('/logs/loglist.html',u=u,title = 'Public logs', logs = logs, len = len(logs))
		db.close()
		
		return res
	except Exception as e:
		return render_template('/logs/loglist.html',u=u,title = 'Public logs')

print('Logging system ... ok')
