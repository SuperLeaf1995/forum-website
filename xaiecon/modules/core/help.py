#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Guidebook and stuff
#

from flask import Blueprint, render_template
from flask_babel import gettext

from xaiecon.modules.core.cache import cache

from xaiecon.modules.core.wrappers import login_wanted

help = Blueprint('help',__name__,template_folder='templates/help')

@help.route('/help/guide', methods = ['GET'])
@login_wanted
#@cache.memoize(timeout=86400)
def display_guide(u=None):
	return render_template('help/guide.html',u=u,title='Guidebook')

print('Help pages ... ok')
