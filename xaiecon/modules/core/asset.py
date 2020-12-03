#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Serves assets to all pages that uses them, i.e site-logo.png, style.css, etc
#

import time
import os

from flask import Blueprint, send_file, request, jsonify
from werkzeug.utils import secure_filename

from xaiecon.modules.core.limiter import limiter
from xaiecon.modules.core.cache import cache

asset = Blueprint('asset',__name__,template_folder='templates')

@asset.route('/assets/<asset_name>', methods = ['GET'])
@limiter.exempt
def send_asset(asset_name):
	final_filename = os.path.join('./assets/public',secure_filename(asset_name))
	return send_file(final_filename)

@asset.route('/assets/landscape/<asset_name>', methods = ['GET'])
@limiter.exempt
def send_asset_landscape(asset_name):
	final_filename = os.path.join('./assets/public/landscape',secure_filename(asset_name))
	return send_file(final_filename)

print('Asset serving ... ok')
