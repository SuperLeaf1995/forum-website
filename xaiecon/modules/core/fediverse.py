#
# Module that allows fediverse with other instances
#

import requests
import os

from flask import Blueprint, render_template, request

from werkzeug.security import check_password_hash, generate_password_hash

from xaiecon.modules.core.cache import cache
from xaiecon.classes.base import open_db
from xaiecon.classes.post import Post
from xaiecon.classes.user import User
from xaiecon.classes.board import Board
from xaiecon.classes.comment import Comment
from xaiecon.classes.serverchain import Serverchain
from xaiecon.classes.exception import XaieconException

from xaiecon.modules.core.wrappers import login_wanted, login_required

fediverse = Blueprint('fediverse',__name__,template_folder='templates/fediverse')

# Connect to the nodes in the fediverse
# This ensures that we are actually not dropped of it
@fediverse.route('/fediverse/connect', methods = ['POST'])
@login_required
def connect(u=None):
	try:
		# Only admins
		if u.is_admin == False:
			abort(401)

		db = open_db()

		json = {
			"last_comment_id":db.query(Comment).order_by(Comment.id.desc()).first().id,
			"last_post_id":db.query(Post).order_by(Post.id.desc()).first().id,
			"last_user_id":db.query(User).order_by(User.id.desc()).first().id,
			"last_board_id":db.query(Board).order_by(Board.id.desc()).first().id
		}

		db.close()
		return '',200
	except XaieconException as e:
		return e,400

print('Fediverse module ... ok')
