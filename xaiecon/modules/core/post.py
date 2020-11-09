#
# Simple post-sharing base module
#

import requests
import threading
import time
import urllib
import hashlib

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
	try:
		pid = request.values.get('pid')
		val = int(request.values.get('value',''))
		
		if pid is None:
			abort(404)
		if val not in [-1,1]:
			abort(400)
		
		db = open_db()
		
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
		cache.delete_memoized(list_posts)
		return '',200
	except XaieconException as e:
		return jsonify({'error':e}),400

@post.route('/post/ballot', methods = ['GET','POST'])
@login_wanted
@cache.memoize(604800)
def ballot(u=None):
	try:
		pid = request.values.get('pid')
		
		db = open_db()
		
		post = db.query(Post).filter_by(id=pid).first()
		if post is None:
			abort(404)
		
		vote = db.query(Vote).filter_by(post_id=post.id).options(joinedload('user_info')).all()
		
		db.close()
		return render_template('post/voters.html',u=u,title = 'Ballot',votes=vote)
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',e=e)

@post.route('/post/kick', methods = ['GET','POST'])
@login_required
def kick(u=None):
	try:
		pid = request.values.get('pid')
		db = open_db()
		if request.method == 'POST':
			post = db.query(Post).filter_by(id=pid).first()
			
			if post is None:
				abort(404)
			
			# User must be also mod of the post's origin board
			board = db.query(Board).filter_by(id=post.board_id).first()
			
			# Check that post is not already kicked and that user mods
			# the guild
			if board is not None:
				if not u.mods(board.unique_identifier) and u.is_admin == False:
					raise XaieconException('You do not mod the origin board')
			else:
				raise XaieconException('Post cannot be kicked because is not in any board')
			
			# Change post's bid to none
			db.query(Post).filter_by(id=pid).update({'board_id':1})
			db.commit()
			
			db.close()
			cache.delete_memoized(list_posts)
			return redirect(f'/post/view?pid={pid}')
		else:
			post = db.query(Post).filter_by(id=pid).first()
			db.close()
			return render_template('post/kick.html',u=u,title='Kick post',post=post)
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/yank', methods = ['GET','POST'])
@login_required
def yank(u=None):
	try:
		pid = request.values.get('pid')
		db = open_db()
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
			cache.delete_memoized(list_posts)
			return redirect(f'/post/view?pid={pid}')
		else:
			boards = db.query(Board).filter_by(user_id=u.id).options(joinedload('user_info')).all()
			post = db.query(Post).filter_by(id=pid).first()
			db.close()
			return render_template('post/yank.html',u=u,title='Yank post',post=post,boards=boards)
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/delete', methods = ['GET','POST'])
@login_required
def delete(u=None):
	try:
		pid = request.values.get('pid')
		
		db = open_db()
		
		post = db.query(Post).filter_by(id=pid).first()
		if post == None:
			abort(404)
		
		if u.id != post.user_id and u.is_admin == False:
			raise XaieconException('User is not authorized')
		
		# Set is_deleted to true
		db.query(Post).filter_by(id=pid).update({
			'is_deleted':True,
			'body':'[deleted]'})
		db.commit()
		db.close()
		cache.delete_memoized(list_posts)
		return '',200
	except XaieconException as e:
		return jsonify({'error':e}),400

@post.route('/post/edit', methods = ['POST','GET'])
@login_required
def edit(u=None):
	try:
		db = open_db()
		
		pid = request.values.get('pid')
		
		post = db.query(Post).filter_by(id=pid).first()
		if post is None:
			abort(404)
		
		if u.id != post.user_id and u.is_admin == False:
			raise XaieconException('User is not authorized')
		
		if request.method == 'POST':
			description = request.form.get('description')
			name = request.form.get('name')
			keywords = request.form.get('keywords')
			link = request.form.get('link','')

			if len(name) > 255:
				raise XaieconException('Too long name')
			
			if link:
				is_link = True
				if link == None:
					raise XaieconException('Provide a valid link')
			else:
				is_link = False
				link = ''
			
			is_nsfw = strtobool(request.form.get('is_nsfw','False'))
			
			if description == None or description == '':
				raise XaieconException('Empty description')
			if name == None or name == '':
				raise XaieconException('Empty name')
			
			# Update post entry on database
			db.query(Post).filter_by(id=pid).update({
						'keywords':keywords,
						'body':description,
						'is_link':is_link,
						'is_nsfw':is_nsfw,
						'title':name,
						'link_url':link})
			db.commit()
			
			db.close()
			cache.delete_memoized(list_posts)
			return redirect(f'/post/view?pid={pid}')
		else:
			db.close()
			return render_template('post/edit.html',u=u,title = 'Edit',post = post)
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/write', methods = ['POST','GET'])
@login_required
def write(u=None):
	try:
		if request.method == 'POST':
			db = open_db()
			
			description = request.form.get('description','')
			name = request.form.get('name')
			keywords = request.form.get('keywords')
			link = request.form.get('link','')
			bid = request.form.get('bid')
			category = request.values.get('category')

			if len(name) > 255:
				raise XaieconException('Too long name')
			if len(description) > 16000:
				raise XaieconException('Too long body')
			
			category = db.query(Category).filter_by(name=category).first()
			if category is None:
				raise XaieconException('Not a valid category')
			
			is_link = False
			if link != '':
				is_link = True
			
			is_nsfw = strtobool(request.form.get('is_nsfw','False'))

			if description == '' and is_link == False:
				raise XaieconException('Empty description')
			if name is None or name == '':
				raise XaieconException('Empty name')
			
			board = db.query(Board).filter_by(id=bid).first()
			if board is None:
				raise XaieconException('Invalid board')
			
			bid = board.id
			
			post = Post(keywords=keywords,
						title=name,
						body=description,
						link_url=link,
						is_link=is_link,
						user_id=u.id,
						is_nsfw=is_nsfw,
						downvote_count=0,
						upvote_count=0,
						total_vote_count=0,
						category_id=category.id)
			if bid is not None:
				post.board_id = bid
			
			db.add(post)
			db.commit()
			
			db.refresh(post)
			
			db.close()
			cache.delete_memoized(list_posts)
			return redirect(f'/post/view?pid={post.id}')
		else:
			db = open_db()
			board = db.query(Board).options(joinedload('user_info')).all()
			categories = db.query(Category).all()
			db.close()
			return render_template('post/write.html',u=u,title = 'New post', boards = board, categories=categories)
	except XaieconException as e:
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

	comment = db.query(Comment).filter_by(post_id=post.id).order_by(desc(Comment.id)).all()
	
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
					if db.query(Comment).filter_by(comment_id=l.id).first() is not None:
						l.more_children = True

					comments.append(l)
	
	# Add one view
	db.query(Post).filter_by(id=pid).update({'views':post.views+1})
	db.commit()
	
	res = render_template('post/details.html',u=u,title=post.title,post=post,comment=comments)
	db.close()
	return res, 200

@post.route('/post/list', methods = ['GET'])
@login_wanted
@cache.memoize(604800)
def list_posts(u=None):
	# Select data of SQL
	db = open_db()
	
	sort = request.values.get('sort','new')
	category = request.values.get('category','All')
	
	category_obj = None
	if category != 'All':
		category_obj = db.query(Category).filter_by(name=category).first()
	
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
	
	post = post.options(joinedload('*')).all()
	
	db.close()
	return render_template('post/list.html',u=u,title='Post frontpage',posts=post)

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
		if request.method == 'POST':
			# Select data of SQL
			db = open_db()
			
			query = request.form.get('query')
			query = query.split(' ')
			
			# TODO: Do better algo
			is_nsfw = u.is_nsfw
			
			post = db.query(Post)
			
			if is_nsfw == False:
				post = post.filter_by(is_nsfw=False)
				
			post = post.options(joinedload('category')).order_by(desc(Post.id)).options(joinedload('category')).all()
			
			res = render_template('post/list.html',u=u,title = 'Post frontpage', posts = post)
			
			# Close the database
			db.close()
			return res
		else:
			return render_template('post/list.html',u=u,title = 'Post frontpage')
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

print('Post share ... ok')
