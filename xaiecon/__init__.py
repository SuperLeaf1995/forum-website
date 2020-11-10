import os
import traceback
import urllib

from flask import Blueprint, Flask, render_template, request, redirect, session
from flask_caching import Cache
from xaiecon.modules.core.cache import cache
from xaiecon.modules.core.hcaptcha import hcaptcha
from xaiecon.modules.core.wrappers import login_wanted

from xaiecon.modules.core.legal import legal
from xaiecon.modules.core.post import post
from xaiecon.modules.core.comment import comment
from xaiecon.modules.core.asset import asset, optimize_all
from xaiecon.modules.core.user import user
from xaiecon.modules.core.gdpr import gdpr
from xaiecon.modules.core.board import board
from xaiecon.modules.core.apiapp import apiapp
from xaiecon.modules.core.fediverse import fediverse

from xaiecon.classes.exception import XaieconDatabaseException

from distutils.util import *

# Create the global app
app = Flask(__name__,instance_relative_config=True)

def main_init():
	app.config['DOCKER'] = strtobool(os.environ.get('DOCKER','False'))
	app.config['SECRET_KEY'] = 'os.urandom(16)'
	app.config['MAX_CONTENT_PATH'] = 5*(1000*1000) # 5 MB
	app.config['CACHE_TYPE'] = 'simple'
	app.config['CACHE_DEFAULT_TIMEOUT'] = 300
	app.config['HCAPTCHA_SITE_KEY'] = os.environ.get('HCAPTCHA_SITE_KEY','')
	app.config['HCAPTCHA_SECRET_KEY'] = os.environ.get('HCAPTCHA_SECRET_KEY','')

	# Developement-only stuff
	if os.environ.get('FLASK_ENV') == 'developement':
		@app.errorhandler(Exception)
		def handle_exception(e):
			return render_template("templates/dev_error.html",u=None,title='Uh oh!',error=e,trace=traceback.format_exc()),503
	else:
		print('Running on production mode')

	@app.errorhandler(XaieconDatabaseException)
	def handle_database_exception(e):
		return render_template("user_error.html",u=None,title='Database error',err=e), 500

	@app.before_first_request
	def app_setup():
		pass

	@app.after_request
	def after_request_fn(response):
		if os.environ.get('FLASK_ENV') == 'production':
			# Send headers
			response.headers.add('X-XSS-Protection','1; mode=block')
			
			# Disallow framing except on media or thumbnails
			if not request.path.endswith('/as_media') and not request.path.endswith('/thumb'):
				response.headers.add('Content-Security-Policy','frame-ancestors \'none\';')
				response.headers.add('X-Content-Type-Options','nosniff')
				response.headers.add('Content-Security-Policy','frame-ancestors \'none\';')

		return response

	@app.route('/', methods=['GET'])
	@login_wanted
	def send_index(u=None):
		return render_template('index.html',u=u,title='Homepage')

	@app.errorhandler(404)
	@login_wanted
	def handle_404(e=None,u=None):
		return render_template('404.html',u=u,title='404'),404

	@app.errorhandler(500)
	@login_wanted
	def handle_500(e=None,u=None):
		return render_template('500.html',u=u,title='500'),500

	# Create cache associated with our app
	# And also initialize hcaptcha
	cache.init_app(app)
	hcaptcha.init_app(app)
	optimize_all()

	# Register modules
	app.register_blueprint(legal)
	app.register_blueprint(post)
	app.register_blueprint(comment)
	app.register_blueprint(asset)
	app.register_blueprint(user)
	app.register_blueprint(gdpr)
	app.register_blueprint(board)
	app.register_blueprint(apiapp)
	app.register_blueprint(fediverse)

	if __name__ == "__main__":
		print('Xaiecon node is up and running. Good luck.')

		if app.config['DOCKER'] == True:
			# Listen to 0.0.0.0 for all addresses on system only on Docker
			app.run(host='0.0.0.0')
		else:
			app.run()

main_init()