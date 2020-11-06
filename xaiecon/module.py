from flask import Blueprint

from xaiecon.modules.core.legal import legal
from xaiecon.modules.core.posts import posts
from xaiecon.modules.core.comment import comment
from xaiecon.modules.core.asset import asset
from xaiecon.modules.core.user import user
from xaiecon.modules.core.gdpr import gdpr
from xaiecon.modules.core.logs import logs
from xaiecon.modules.core.board import board
from xaiecon.modules.core.apiapp import apiapp
from xaiecon.modules.core.fediverse import fediverse

# Register modules
def register_all_modules(app=None):
	app.register_blueprint(legal)
	app.register_blueprint(posts)
	app.register_blueprint(comment)
	app.register_blueprint(asset)
	app.register_blueprint(user)
	app.register_blueprint(gdpr)
	app.register_blueprint(logs)
	app.register_blueprint(board)
	app.register_blueprint(apiapp)
	app.register_blueprint(fediverse)

print('Adding modules ... ok')
