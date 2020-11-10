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
	for file in os.listdir('./assets/private')
		name, ext = os.path.splittext(file)
		filename = os.path.join('./assets/public','{name}.min.{ext}')
		outfile = open(filename,'w')
		infile = open(file,'r')
		
		# minify css
		if ext == 'css':
			outfile.write(rcssmin.cssmin(infile.read()))
		# minify css
		elif ext == 'js':
			outfile.write(rjsmin.jsmin(infile.read()))

@asset.route('/assets/<asset_name>', methods = ['GET'])
@cache.memoize(0)
def send_asset(asset_name):
	final_filename = os.path.join('./assets/public',secure_filename(asset_name))
	return send_file(final_filename)

print('Asset serving ... ok')
