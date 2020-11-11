#
# Board module, place where posts can be put and yanked off
#

from flask import Blueprint, render_template, session, redirect, request, abort
from xaiecon.modules.core.cache import cache

from xaiecon.classes.base import open_db
from xaiecon.classes.board import Board, BoardBan, BoardSub
from xaiecon.classes.post import Post
from xaiecon.classes.category import Category
from xaiecon.classes.exception import XaieconException

from xaiecon.modules.core.wrappers import login_wanted, login_required

from sqlalchemy.orm import joinedload
from sqlalchemy import desc, asc

board = Blueprint('board',__name__,template_folder='templates')

@board.route('/board/view', methods = ['GET'])
@login_wanted
def view(u=None):
	sort = request.values.get('sort','new')
	bid = request.values.get('bid','new')
	
	db = open_db()
	board = db.query(Board).filter_by(id=bid).options(joinedload('*')).first()
	if board is None:
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

@board.route('/board/edit', methods = ['GET','POST'])
@login_required
def edit(u=None):
	try:
		db = open_db()
		
		bid = request.values.get('bid')
		
		board = db.query(Board).filter_by(id=bid).first()
		if board is None:
			abort(404)
		
		if request.method == 'POST':
			name = request.values.get('name')
			descr = request.values.get('descr')
			category = request.values.get('category')
			keywords = request.values.get('keywords')
			
			if u.mods(board.id) == False:
				raise XaieconException('Not authorized')
			
			category = db.query(Category).filter_by(name=category).first()
			if category is None:
				raise XaieconException('Not a valid category')
			
			board = Board(
				name=name,
				descr=descr,
				category_id=category.id,
				keywords=keywords)
			
			db.add(board)
			db.commit()
			
			db.refresh(board)
			
			db.close()
			return redirect(f'/board/view/{board.id}')
		else:
			category = db.query(Category).all()
			db.close()
			return render_template('board/edit.html',u=u,title = 'New board',categories=category,board=board)
	except XaieconException as e:
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@board.route('/board/ban', methods = ['POST','GET'])
@login_required
def ban(u=None):
	bid = int(request.values.get('bid','0'))
	uid = int(request.values.get('uid','0'))
	if request.method == 'POST':
		db = open_db()

		reason = request.values.get('reason','No reason specified')

		if u.mods(bid) == False:
			return '',401

		# Board does not exist
		if db.query(Board).filter_by(id=bid).first() is None:
			return '',404
		# Already banned
		if db.query(BoardBan).filter_by(user_id=uid,board_id=bid).first() is not None:
			return '',400
		# Do not ban self
		if uid == u.id:
			return '',400

		sub = BoardBan(user_id=uid,board_id=bid,reason=reason)
		db.add(sub)
		db.commit()

		db.close()
		return redirect(f'/board/view?bid={bid}')
	else:
		return render_template('board/ban.html',u=u,title='Ban user',bid=bid,uid=uid)

@board.route('/board/unban', methods = ['POST'])
@login_required
def unban(u=None):
	db = open_db()
	
	bid = request.values.get('bid')
	uid = request.values.get('uid')

	if u.mods(bid) == False:
		return '',401

	# Board does not exist
	if db.query(Board).filter_by(id=bid).first() is None:
		return '',404
	# Do not unban self
	if uid == u.id:
		return '',400

	db.qeury(BoardBan).filter_by(user_id=uid,board_id=bid).delete()
	db.commit()

	db.close()
	return '',200

@board.route('/board/subscribe', methods = ['POST'])
@login_required
def subscribe(u=None):
	db = open_db()
	
	bid = request.values.get('bid')

	# Board does not exist
	if db.query(Board).filter_by(id=bid).first() is None:
		return '',404
	# Already subscribed
	if u.is_subscribed(bid) == True:
		return '',400

	sub = BoardSub(user_id=u.id,board_id=bid)
	db.add(sub)
	db.commit()

	db.close()
	return '',200

@board.route('/board/unsubscribe', methods = ['POST'])
@login_required
def unsubscribe(u=None):
	db = open_db()
	
	bid = request.values.get('bid')

	# Board does not exist
	if db.query(Board).filter_by(id=bid).first() is None:
		return '',404
	# Not subscribed
	if u.is_subscribed(bid) == False:
		return '',400

	db.query(BoardSub).filter_by(user_id=u.id,board_id=bid).delete()
	db.commit()

	db.close()
	return '',200

@board.route('/board/new', methods = ['GET','POST'])
@login_required
def new(u=None):
	try:
		db = open_db()

		if u.can_make_board == False:
			raise XaieconException('You are not allowed to make boards')

		if request.method == 'POST':
			name = request.values.get('name')
			descr = request.values.get('descr')
			category = request.values.get('category')
			keywords = request.values.get('keywords')
			
			if db.query(Board).filter_by(user_id=u.id).count() > 20:
				raise XaieconException('Limit of 20 boards reached')
			
			category = db.query(Category).filter_by(name=category).first()
			if category is None:
				raise XaieconException('Not a valid category')
			
			board = Board(
				name=name,
				descr=descr,
				user_id=u.id,
				category_id=category.id,
				keywords=keywords)
			
			db.add(board)
			db.commit()
			
			db.refresh(board)
			
			db.close()
			return redirect(f'/board/view?bid={board.id}')
		else:
			category = db.query(Category).all()
			db.close()
			return render_template('board/new.html',u=u,title = 'New board',categories=category)
	except XaieconException as e:
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

print('Board pages ... ok')
