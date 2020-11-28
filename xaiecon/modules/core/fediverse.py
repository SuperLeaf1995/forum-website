#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Module that allows fediverse with other instances
#

# In short
# Our ActivityPub implementation uses E2E to communicate to other servers
# We need to have many privacy, because we do not want any eavesdropper
# To see a big list of posts without our consent. Business will love this.

# TODO: implement activitypub

from flask import Blueprint, render_template, request, jsonify
from flask_babel import gettext

from xaiecon.classes.base import open_db
from xaiecon.classes.serverchain import Serverchain

from xaiecon.modules.core.wrappers import login_required

fediverse = Blueprint('fediverse',__name__,template_folder='templates/fediverse')

# After this, our server will gladly receive AP stuff from this IP
# And that IP will also be sent some of our info.
#
# The only step left is to contact the IP owner and tell them that
# we are linked
@fediverse.route('/fediverse/chain', methods = ['GET','POST'])
@login_required
def add_instance(u=None):
	if request.method == 'POST':
		db = open_db()
		
		serv = Serverchain(
			name=request.values.get('name',request.values.get('ip_addr')),
			ip_addr=request.values.get('ip_addr'))
		
		db.add(serv)
		db.commit()
		db.close()
		return 'Server added!',200
	else:
		return render_template('fediverse/add.html',u=u,title='Add instance')

print('Fediverse module ... ok')