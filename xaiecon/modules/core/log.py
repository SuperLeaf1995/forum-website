#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Simple public logging module
#

from flask import Blueprint, render_template
from flask_babel import gettext

from xaiecon.classes.base import open_db
from xaiecon.classes.log import Log

from xaiecon.modules.core.wrappers import login_wanted

log = Blueprint('log',__name__,template_folder='templates/log')

@log.route('/log/public', methods = ['GET'])
@login_wanted
def showlogs(u=None):
	db = open_db()
	
	logs = db.query(Log).all()
	
	res = render_template('/logs/loglist.html',u=u,title = 'Public logs', logs = logs, len = len(logs))
	db.close()
	return res

print('Logging system ... ok')
