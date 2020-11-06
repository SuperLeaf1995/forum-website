#
# Board module, place where posts can be put and yanked off
#

from flask import Blueprint, render_template, session, redirect, request, abort
from xaiecon.cache import cache

from xaiecon.classes.board import *
from xaiecon.classes.post import *
from xaiecon.classes.exception import *
from xaiecon.classes.category import *

from xaiecon.modules.core.wrappers import *

from sqlalchemy.orm import joinedload

board = Blueprint('board',__name__,template_folder='templates')

import random
def create_unique_identifier(n=250):
	string = str(''.join(random.choices('abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ',k=n)))
	return string

@board.route('/board/view/<uid>', methods = ['GET'])
@login_wanted
def view(u=None,uid=None):
	sort = request.values.get('sort','new')
	
	db = open_db()
	board = db.query(Board).filter_by(unique_identifier=uid).options(joinedload('*')).first()
	if board == None:
		abort(404)
	posts = db.query(Post).filter_by(board_id=board.id).options(joinedload('*'))
	
	if sort == 'new':
		posts = posts.order_by(desc(Post.id))
	elif sort == 'old':
		posts = posts.order_by(asc(Post.id))
	else:
		abort(401)
	
	posts = posts.all()
	
	db.close()
	return render_template('board/view.html',u=u,title=board.name,board=board,posts=posts)

@board.route('/b/<name>', methods = ['GET'])
@login_wanted
def view_by_name(u=None,name=None):
	db = open_db()
	board = db.query(Board).filter_by(name=name).options(joinedload('*')).all()
	if board is None or len(board) == 0:
		abort(404)
	db.close()
	
	# Multiple boards
	if len(board) > 1:
		return render_template('board/pick.html',u=u,title=name,boards=board)
	
	# Only 1 board exists with that name
	return redirect(f'/board/view/{board[0].unique_identifier}')

@board.route('/board/new', methods = ['GET','POST'])
@login_required
def new(u=None):
	try:
		db = open_db()
		if request.method == 'POST':
			
			name = request.values.get('name')
			descr = request.values.get('descr')
			category = request.values.get('category')
			keywords = request.values.get('keywords')
			
			category = db.query(Category).filter_by(name=category).first()
			if category is None:
				raise XaieconException('Not a valid category')
			
			unique_identifier = create_unique_identifier()
			
			board = Board(
				name=name,
				descr=descr,
				user_id=u.id,
				unique_identifier=unique_identifier,
				category_id=category.id,
				keywords=keywords)
			
			db.add(board)
			db.commit()
			
			db.close()
			return redirect(f'/board/view/{unique_identifier}')
		else:
			category = db.query(Category).all()
			db.close()
			return render_template('board/new.html',u=u,title = 'New board',categories=category)
	except XaieconException as e:
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

print('Board pages ... ok')
