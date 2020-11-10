#
# Serves assets to all pages that uses them, i.e site-logo.png, style.css, etc
#

import os
import rjsmin
import rcssmin

from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, send_file
from xaiecon.modules.core.cache import cache

asset = Blueprint('asset',__name__,template_folder='templates')

# optimize assets to save space and time
def optimize_all():
	for file in os.listdir('./xaiecon/assets/private'):
		# minify css
		if file.endswith('css'):
			infile = open(os.path.join('./xaiecon/assets/private',file),'r')
			outfile = open(os.path.join('./xaiecon/assets/public',file),'w')
			outfile.write(rcssmin.cssmin(infile.read()))
		# minify css
		elif file.endswith('js'):
			infile = open(os.path.join('./xaiecon/assets/private',file),'r')
			outfile = open(os.path.join('./xaiecon/assets/public',file),'w')
			outfile.write(rjsmin.jsmin(infile.read()))
		else:
			infile = open(os.path.join('./xaiecon/assets/private',file),'rb')
			outfile = open(os.path.join('./xaiecon/assets/public',file),'wb')
			outfile.write(infile.read())

@asset.route('/assets/<asset_name>', methods = ['GET'])
def send_asset(asset_name):
	final_filename = os.path.join('./assets/public',secure_filename(asset_name))
	return send_file(final_filename)

print('Asset serving ... ok')
