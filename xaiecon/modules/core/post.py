 #
# Simple post-sharing base module
#

import requests
import threading
import time
import urllib
import urllib.parse

from bs4 import BeautifulSoup
from os import path, remove
from flask import Blueprint, render_template, request, session, jsonify, redirect, send_from_directory, abort, send_file
from werkzeug.utils import secure_filename

from xaiecon.modules.core.cache import cache
from xaiecon.classes.base import open_db
from xaiecon.classes.user import User
from xaiecon.classes.post import Post
from xaiecon.classes.log import Log
from xaiecon.classes.comment import Comment
from xaiecon.classes.category import Category
from xaiecon.classes.vote import Vote
from xaiecon.classes.view import View
from xaiecon.classes.board import Board
from xaiecon.classes.exception import XaieconException
from xaiecon.modules.core.wrappers import login_wanted, login_required

from distutils.util import *

from sqlalchemy.orm import joinedload
from sqlalchemy import desc, asc

post = Blueprint('post',__name__,template_folder='templates/post')

@post.route('/post/vote', methods = ['POST'])
@login_required
def vote(u=None):
	db = open_db()
	try:
		pid = request.values.get('pid')
		val = int(request.values.get('value',''))
		
		if pid is None:
			abort(404)
		if val not in [-1,1]:
			abort(400)
		
		post = db.query(Post).filter_by(id=pid).first()
		if post is None:
			abort(404)
		
		vote = db.query(Vote).filter_by(user_id=u.id,post_id=pid).first()
		
		if vote is not None and vote.value == val:
			db.query(Vote).filter_by(user_id=u.id,post_id=pid).delete()
		else:
			db.query(Vote).filter_by(user_id=u.id,post_id=pid).delete()
			# Create vote relation
			vote = Vote(user_id=u.id,post_id=post.id,value=val)
			db.add(vote)
		
		# Update vote count
		downvotes = db.query(Vote).filter_by(post_id=pid,value=-1).count()
		upvotes = db.query(Vote).filter_by(post_id=pid,value=1).count()
		db.query(Post).filter_by(id=pid).update({
			'downvote_count':downvotes,
			'upvote_count':upvotes,
			'total_vote_count':upvotes-downvotes})
		
		db.commit()
		
		db.close()
		cache.delete_memoized(ballot)
		return '',200
	except XaieconException as e:
		db.rollback()
		db.close()
		return jsonify({'error':e}),400

@post.route('/post/ballot', methods = ['GET','POST'])
@login_wanted
@cache.memoize(0)
def ballot(u=None):
	db = open_db()
	try:
		pid = request.values.get('pid')
		
		post = db.query(Post).filter_by(id=pid).first()
		if post is None:
			abort(404)
		
		vote = db.query(Vote).filter_by(post_id=post.id).options(joinedload('user_info')).all()
		
		db.close()
		return render_template('post/voters.html',u=u,title = 'Ballot',votes=vote)
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',e=e)

@post.route('/post/nuke', methods = ['GET','POST'])
@login_required
def nuke(u=None):
	db = open_db()
	try:
		pid = request.values.get('pid')
		post = db.query(Post).filter_by(id=pid).first()
		if post is None:
			abort(404)
		
		# User must be also mod of the post's origin board
		board = db.query(Board).filter_by(id=post.board_id).first()
		
		# Check that post is not already nuked and that user mods
		# the guild
		if board is None:
			raise XaieconException('Post cannot be nuked because it is not in any board')
		if post.is_deleted == True or post.nuked == True:
			raise XaieconException('Post already nuked/deleted by user or someone else')
		if not u.mods(board.id) and u.is_admin == False:
			raise XaieconException('You do not mod the origin board')
		
		# "Nuke" post
		db.query(Post).filter_by(id=pid).update({'nuked':True,'nuker_id':u.id})
		db.commit()
		
		db.close()
		return redirect(f'/post/view?pid={pid}')
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/kick', methods = ['GET','POST'])
@login_required
def kick(u=None):
	db = open_db()
	try:
		pid = request.values.get('pid')
		if request.method == 'POST':
			post = db.query(Post).filter_by(id=pid).first()
			
			if post is None:
				abort(404)
			
			# User must be also mod of the post's origin board
			board = db.query(Board).filter_by(id=post.board_id).first()
			
			# Check that post is not already kicked and that user mods
			# the guild
			if board is None:
				raise XaieconException('Post cannot be kicked because it is not in any board')
			if not u.mods(board.id) and u.is_admin == False:
				raise XaieconException('You do not mod the origin board')
			
			# Change post's bid to general waters
			db.query(Post).filter_by(id=pid).update({'board_id':1})
			db.commit()
			
			db.close()
			return redirect(f'/post/view?pid={pid}')
		else:
			post = db.query(Post).filter_by(id=pid).first()
			db.close()
			return render_template('post/kick.html',u=u,title='Kick post',post=post)
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/yank', methods = ['GET','POST'])
@login_required
def yank(u=None):
	db = open_db()
	try:
		pid = request.values.get('pid')
		if request.method == 'POST':
			bid = request.values.get('bid')
			
			post = db.query(Post).filter_by(id=pid).first()
			
			# User must be also mod of the post's origin board
			# Or the post must not have a bid
			board = db.query(Board).filter_by(id=post.board_id).first()

			# If post is standalone or baord is not exists then just skip the
			# auth
			if board is not None or board.id == 1:
				if not u.mods(board.id) and u.is_admin == False:
					raise XaieconException('You do not mod the origin board')
				
			# Check that user mods the board he is trying to yank to
			if not u.mods(bid) and u.is_admin == False:
				raise XaieconException('You do not mod the target board')
			
			# Change post's bid
			board = db.query(Board).filter_by(id=bid).first()
			db.query(Post).filter_by(id=pid).update({'board_id':board.id})
			db.commit()
			
			db.close()
			return redirect(f'/post/view?pid={pid}')
		else:
			boards = db.query(Board).filter_by(user_id=u.id).options(joinedload('user_info')).all()
			post = db.query(Post).filter_by(id=pid).first()
			db.close()
			return render_template('post/yank.html',u=u,title='Yank post',post=post,boards=boards)
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/delete', methods = ['GET','POST'])
@login_required
def delete(u=None):
	db = open_db()
	try:
		pid = request.values.get('pid')
		
		post = db.query(Post).filter_by(id=pid).first()
		if post == None:
			abort(404)
		
		if u.id != post.user_id and u.is_admin == False:
			raise XaieconException('User is not authorized')
		
		# Set is_deleted to true
		db.query(Post).filter_by(id=pid).update({
			'is_deleted':True,
			'body':'Deleted by user',
			'is_link':False,
			'link_url':''})
		db.commit()
		db.close()
		return '',200
	except XaieconException as e:
		db.rollback()
		db.close()
		return jsonify({'error':e}),400

@post.route('/post/edit', methods = ['POST','GET'])
@login_required
def edit(u=None):
	db = open_db()
	try:
		pid = request.values.get('pid')
		
		post = db.query(Post).filter_by(id=pid).first()
		if post is None:
			abort(404)
		
		if u.id != post.user_id and u.is_admin == False:
			raise XaieconException('User is not authorized')
		
		if request.method == 'POST':
			body = request.form.get('body')
			title = request.form.get('title')
			keywords = request.form.get('keywords')
			link = request.form.get('link','')
			category = int(request.form.get('category',''))

			if len(title) > 255:
				raise XaieconException('Too long title')

			category = db.query(Category).filter_by(id=category).first()
			if category is None:
				raise XaieconException('Not a valid category')
			
			is_link = False
			embed_html = ''
			if link != '':
				is_link = True
				parsed_link = urllib.parse.urlparse(link)
				link = urllib.parse.quote(link,safe='/:$#')

				if parsed_link.netloc == 'lbry.tv' or parsed_link.netloc == 'open.lbry.tv' or parsed_link.netloc == 'www.lbry.tv':
					embed_html = f'<iframe width="560" height="315" src="{link}" allowfullscreen></iframe>'
			
			is_nsfw = strtobool(request.form.get('is_nsfw','False'))
			
			if body == None or body == '':
				raise XaieconException('Empty body')
			if title == None or title == '':
				raise XaieconException('Empty title')

			body_html = ''

			# Update post entry on database
			db.query(Post).filter_by(id=pid).update({
						'keywords':keywords,
						'body':body,
						'is_link':is_link,
						'is_nsfw':is_nsfw,
						'title':title,
						'link_url':link,
						'category_id':category.id,
						'body_html':body_html,
						'embed_html':embed_html})
			db.commit()
			
			db.close()
			return redirect(f'/post/view?pid={pid}')
		else:
			categories = db.query(Category).all()
			db.close()
			return render_template('post/edit.html',u=u,title='Edit',post=post,categories=categories)
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/write', methods = ['POST','GET'])
@login_required
def write(u=None):
	db = open_db()
	try:
		if request.method == 'POST':
			body = request.form.get('body','')
			title = request.form.get('title')
			keywords = request.form.get('keywords')
			link = request.form.get('link','')
			bid = request.form.get('bid')
			category = int(request.values.get('category',''))

			if len(title) > 255:
				raise XaieconException('Too long title')
			if len(body) > 16000:
				raise XaieconException('Too long body')
			
			category = db.query(Category).filter_by(id=category).first()
			if category is None:
				raise XaieconException('Not a valid category')
			board = db.query(Board).filter_by(id=bid).first()
			if board is None:
				raise XaieconException('Invalid board')
			bid = board.id

			if u.is_banned_from_board(bid) == True:
				raise XaieconException(f'You\'re banned from /b/{board.name}')
			
			if link != '':
				is_link = True
				parsed_link = urllib.parse.urlparse(link)
				link = urllib.parse.quote(link,safe='/:$#')

				if parsed_link.netloc == 'lbry.tv' or parsed_link.netloc == 'open.lbry.tv' or parsed_link.netloc == 'www.lbry.tv':
					embed_html = f'<iframe width="560" height="315" src="{link}" allowfullscreen></iframe>'
			
			is_nsfw = strtobool(request.form.get('is_nsfw','False'))

			if body == '' and is_link == False:
				raise XaieconException('Empty body')
			if title is None or title == '':
				raise XaieconException('Empty title')
			
			body_html = ''

			post = Post(keywords=keywords,
						title=title,
						body=body,
						link_url=link,
						is_link=is_link,
						user_id=u.id,
						is_nsfw=is_nsfw,
						downvote_count=0,
						upvote_count=0,
						total_vote_count=0,
						category_id=category.id,
						board_id=bid,
						embed_html='',
						body_html=body_html)
			
			db.add(post)
			db.commit()
			
			db.refresh(post)

			csam_thread = threading.Thread(target=csam_check_post, args=(id,post.link_url,))
			csam_thread.start()

			db.close()
			return redirect(f'/post/view?pid={post.id}')
		else:
			board = db.query(Board).options(joinedload('user_info')).all()
			categories = db.query(Category).all()
			db.close()
			return render_template('post/write.html',u=u,title = 'New post', boards = board, categories=categories)
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/view', methods = ['GET'])
@login_wanted
def view(u=None):
	pid = request.values.get('pid')
	if pid == None:
		abort(404)
	
	# Obtain postpath and send it
	db = open_db()
	
	# Query post from database
	post = db.query(Post).filter_by(id=pid).options(joinedload('*')).first()
	if post is None:
		abort(404)
	# Dont let people see nsfw
	if post.is_nsfw == True and u.is_nsfw == False:
		abort(403)

	comment = db.query(Comment).filter_by(post_id=post.id).options(joinedload('*')).order_by(desc(Comment.id)).all()
	
	# This is how we get replies, pardon for so many cringe
	comments = []

	# First add the top comment(s)
	for c in comment:
		c.depth_level = 1
		comments.append(c)

		# Obtain comments that reference the current comment (top)
		comms = db.query(Comment).filter_by(comment_id=c.id).options(joinedload('*')).all()
		if comms is not None:
			# Obtain the comments of comments
			for d in comms:
				d.depth_level = 2
				ecomms = db.query(Comment).filter_by(comment_id=d.id).options(joinedload('*')).all()
				
				comments.append(d)
				for l in ecomms:
					l.depth_level = 3

					# Deepest comments, check if they have even more children
					if db.query(Comment).filter_by(comment_id=l.id).options(joinedload('*')).first() is not None:
						l.more_children = True

					comments.append(l)
	
	# Add one view
	if u is not None:
		if db.query(View).filter_by(user_id=u.id,post_id=pid) is None:
			view = View(user_id=u.id,post_id=pid)
			db.add(view)
			db.query(Post).filter_by(id=pid).update({'views':post.views+1})
			db.commit()

	db.close()
	return render_template('post/details.html',u=u,title=post.title,post=post,comment=comments)

@post.route('/post/list', methods = ['GET'])
@post.route('/post/list/<sort>', methods = ['GET'])
@login_wanted
def list_posts(u=None, sort='new'):
	# Select data of SQL
	db = open_db()

	category = request.values.get('category','All')
	page = int(request.values.get('page','0'))
	num = int(request.values.get('num','15'))
	
	category_obj = None
	if category != 'All':
		category_obj = db.query(Category).filter_by(name=category).first()
		if category_obj is None:
			category_obj = db.query(Category).filter_by(name='All').first()
	
	is_nsfw = False
	if u is not None:
		is_nsfw = u.is_nsfw
	
	post = db.query(Post)
	
	if is_nsfw == False:
		post = post.filter_by(is_nsfw=False)
	if category_obj is not None:
		post = post.filter_by(category_id=category_obj.id)
	
	if sort == 'new':
		post = post.order_by(desc(Post.id))
	elif sort == 'old':
		post = post.order_by(asc(Post.id))
	else:
		abort(401)
	
	post = post.options(joinedload('*')).filter(Post.id>=(page*num),Post.id<=((page+1)*num)).all()
	
	db.close()
	return render_template('post/list.html',u=u,title='Post frontpage',posts=post,
		page=page,num=num,category=category,sort=sort)

@post.route('/post/nuked/<sort>', methods = ['GET'])
@login_required
def list_nuked(u=None, sort='new'):
	# Select data of SQL
	db = open_db()

	category = request.values.get('category','All')
	page = int(request.values.get('page','0'))
	num = int(request.values.get('num','15'))
	
	category_obj = None
	if category != 'All':
		category_obj = db.query(Category).filter_by(name=category).first()
		if category_obj is None:
			category_obj = db.query(Category).filter_by(name='All').first()
	
	is_nsfw = False
	if u is not None:
		is_nsfw = u.is_nsfw
	
	post = db.query(Post)
	
	if is_nsfw == False:
		post = post.filter_by(is_nsfw=False)
	if category_obj is not None:
		post = post.filter_by(category_id=category_obj.id)
	
	if sort == 'new':
		post = post.order_by(desc(Post.id))
	elif sort == 'old':
		post = post.order_by(asc(Post.id))
	else:
		abort(401)
	
	post = post.options(joinedload('*')).filter(Post.id>=(page*num),Post.id<=((page+1)*num)).all()
	
	db.close()
	return render_template('post/list.html',u=u,title='Post frontpage',posts=post,
		page=page,num=num,category=category,sort=sort)

@post.route('/post/feed/<sort>', methods = ['GET'])
@login_required
def feed_posts(u=None, sort='new'):
	# Select data of SQL
	db = open_db()

	category = request.values.get('category','All')
	page = int(request.values.get('page','0'))
	num = int(request.values.get('num','15'))
	
	category_obj = None
	if category != 'All':
		category_obj = db.query(Category).filter_by(name=category).first()
		if category_obj is None:
			category_obj = db.query(Category).filter_by(name='All').first()
	
	is_nsfw = False
	if u is not None:
		is_nsfw = u.is_nsfw
	
	post = db.query(Post)
	
	if is_nsfw == False:
		post = post.filter_by(is_nsfw=False)
	if category_obj is not None:
		post = post.filter_by(category_id=category_obj.id)
	
	if sort == 'new':
		post = post.order_by(desc(Post.id))
	elif sort == 'old':
		post = post.order_by(asc(Post.id))
	else:
		abort(401)
	
	post = post.options(joinedload('*')).filter(Post.id>=(page*num),Post.id<=((page+1)*num)).all()

	# If only show user feed then remove all posts
	# That are not in their subscription
	subs = u.subscribed_boards()
	subs_id = []
	for s in subs:
		subs_id.append(s.id)
	for i in range(0,len(post)):
		if post[i].board_id not in subs_id:
			post.pop(i)
	
	db.close()
	return render_template('post/list.html',u=u,title='Post frontpage',posts=post,
		page=page,num=num,category=category,sort=sort)

@post.route('/post/title_by_url', methods = ['GET'])
def title_by_url():
	# Used by javascript for getting title and put it as title
	# for using url'ed posts
	url = request.values.get('url')
	if url is None:
		return '',400

	html = urllib.request.urlopen(url)
	if html is None:
		return '',400

	html = html.read().decode('utf8')

	soup = BeautifulSoup(html, 'html.parser')
	title = soup.find('title')
	if title is None:
		return '',400

	return title, 200

@post.route('/post/search', methods = ['GET','POST'])
@login_wanted
def search(u=None):
	try:
		page = int(request.values.get('page','0'))
		num = int(request.values.get('num','15'))
		if request.method == 'POST':
			# Select data of SQL
			db = open_db()
			
			query = request.form.get('query')
			query = query.split(' ')
			
			is_nsfw = False
			if u is not None:
				is_nsfw = u.is_nsfw
			
			post = db.query(Post)
			
			if is_nsfw == False:
				post = post.filter_by(is_nsfw=False)
			
			posts = []
			for q in query:
				ps = post.options(joinedload('*')).order_by(desc(Post.id)).filter_by(title=q).filter(Post.id>=(page*num),Post.id<=((page+1)*num)).all()
				for p in ps:
					posts.append(p)
			
			# Close the database
			db.close()
			return render_template('post/list.html',u=u,title='Post frontpage',posts=posts)
		else:
			return render_template('post/list.html',u=u,title='Post frontpage')
	except XaieconException as e:
		return render_template('user_error.html',u=u,title='Whoops!',err=e)

# Check user for csam, if so ban the user
def csam_check_post(id: id,link: str):
	db = open_db()

	# Let's see if this is csam
	user = db.query(User).filter_by(id=id).first()

	headers = {'User-Agent':'xaiecon-csam-check'}
	for i in range(10):
		x = requests.get(link,headers=headers)
		if x.status_code in [200, 451]:
			break
		else:
			time.sleep(10)
	if x.status_code != 451:
		return

	# Ban user
	db.query(User).filter_by(id=id).update({
		'ban_reason':'CSAM Automatic Removal',
		'is_banned':True})
	db.commit()
	db.refresh(user)

	os.remove(os.path.join('user_data',user.image_file))
	
	db.close()
	return

print('Post share ... ok')
