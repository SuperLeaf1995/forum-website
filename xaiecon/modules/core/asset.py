#
# Serves assets to all pages that uses them, i.e site-logo.png, style.css, etc
#

from os import path
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, send_file

asset = Blueprint('asset',__name__,template_folder='templates')

@asset.route('/assets/<asset_name>', methods = ['GET'])
def send_asset(asset_name):
	final_filename = path.join('./assets/public',secure_filename(asset_name))
	return send_file(final_filename)

@asset.route('/icons/<ico_name>', methods = ['GET'])
def send_icon(ico_name):
	final_filename = path.join('./assets/public/icons',secure_filename(ico_name))
	return send_file(final_filename)

print('Asset serving ... ok')
