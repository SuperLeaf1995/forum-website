#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Serves assets to all pages that uses them, i.e site-logo.png, style.css, etc
#

import time
import os

from flask import Blueprint, send_file, request, jsonify
from werkzeug.utils import secure_filename

asset = Blueprint('asset',__name__,template_folder='templates')

@asset.route('/assets/<asset_name>', methods = ['GET'])
def send_asset(asset_name):
	final_filename = os.path.join('./assets/public',secure_filename(asset_name))
	return send_file(final_filename)

@asset.route('/assets/landscape/<asset_name>', methods = ['GET'])
def send_asset_landscape(asset_name):
	final_filename = os.path.join('./assets/public/landscape',secure_filename(asset_name))
	return send_file(final_filename)

@asset.route('/timeit', methods = ['GET'])
def send_time():
	before = request.values.get('time')
	now = time.time()
	diff = now-before
	if diff <= 0:
		diff_str = f'{"now"}'
	elif diff >= 0 and diff <= 60:
		diff_str = f'{diff} seconds ago'
	elif diff >= 60*2 and diff <= 60*60:
		diff_str = f'{diff/60} minutes ago'
	elif diff >= 60*60:
		diff_str = f'{diff/(60*60)} hours ago'
	
	return jsonify({'time':diff_str})

print('Asset serving ... ok')
