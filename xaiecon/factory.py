import os

from flask import Flask, render_template, request

from xaiecon.modules.core.cache import cache
from xaiecon.modules.core.hcaptcha import hcaptcha
from xaiecon.modules.core.wrappers import login_wanted

from xaiecon.classes.exception import XaieconDatabaseException, XaieconException
from distutils.util import strtobool

def create_app():
	# Create the global app
	app = Flask(__name__,instance_relative_config=True)
	app.config['DOCKER'] = strtobool(os.environ.get('DOCKER','False'))
	if os.environ.get('FLASK_ENV') == 'production':
		app.config['SECRET_KEY'] = os.urandom(16)
	else:
		app.config['SECRET_KEY'] = 'DefaultDebugKey'
	app.config['MAX_CONTENT_PATH'] = 5*(1000*1000) # 5 MB
	app.config['CACHE_TYPE'] = 'simple'
	app.config['CACHE_DEFAULT_TIMEOUT'] = 300
	app.config['HCAPTCHA_SITE_KEY'] = os.environ.get('HCAPTCHA_SITE_KEY','')
	app.config['HCAPTCHA_SECRET_KEY'] = os.environ.get('HCAPTCHA_SECRET_KEY','')
	app.config['DOMAIN_NAME'] = 'localhost:5000'

	@app.errorhandler(XaieconDatabaseException)
	def handle_database_exception(e=None):
		return render_template("user_error.html",u=None,title='Database Exception',err=e), 500
	
	@app.errorhandler(XaieconException)
	@login_wanted
	def handle_exception(e=None,u=None):
		return render_template("user_error.html",u=None,title='Server Exception',err=e), 500

	@app.errorhandler(404)
	@login_wanted
	def handle_404(e=None,u=None):
		return render_template('404.html',u=u,title='404'),404

	@app.errorhandler(500)
	@login_wanted
	def handle_500(e=None,u=None):
		return render_template('500.html',u=u,title='500'),500

	@app.route('/', methods=['GET'])
	@login_wanted
	def send_index(u=None):
		return render_template('index.html',u=u,title='Homepage')

	@app.after_request
	def after_request_fn(response):
		if os.environ.get('FLASK_ENV') == 'production':
			response.headers.add('X-XSS-Protection','1; mode=block')
			if not request.path.endswith('/thumb') and not request.path.endswith('/image'):
				response.headers.add('Content-Security-Policy','frame-ancestors \'none\';')
				response.headers.add('X-Content-Type-Options','nosniff')
				response.headers.add('Content-Security-Policy','frame-ancestors \'none\';')
		return response

	# Create cache associated with our app
	# And also initialize hcaptcha
	cache.init_app(app)
	hcaptcha.init_app(app)

	# Register modules
	from xaiecon.modules.core.legal import legal
	app.register_blueprint(legal)

	from xaiecon.modules.core.post import post
	app.register_blueprint(post)

	from xaiecon.modules.core.comment import comment
	app.register_blueprint(comment)

	from xaiecon.modules.core.asset import asset
	app.register_blueprint(asset)

	from xaiecon.modules.core.user import user
	app.register_blueprint(user)

	from xaiecon.modules.core.gdpr import gdpr
	app.register_blueprint(gdpr)

	from xaiecon.modules.core.board import board
	app.register_blueprint(board)

	from xaiecon.modules.core.apiapp import apiapp
	app.register_blueprint(apiapp)

	from xaiecon.modules.core.fediverse import fediverse
	app.register_blueprint(fediverse)

	return app