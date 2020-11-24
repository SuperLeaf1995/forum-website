#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Simple post-sharing base module
#

import os
import requests
import threading
import time
import urllib
import urllib.parse
import secrets
import PIL
import io

from bs4 import BeautifulSoup
from flask import Blueprint, render_template, request, jsonify, redirect, send_from_directory, abort
from flask_misaka import markdown
from werkzeug.utils import secure_filename

from xaiecon.modules.core.cache import cache
from xaiecon.classes.base import open_db
from xaiecon.classes.user import User
from xaiecon.classes.post import Post
from xaiecon.classes.comment import Comment
from xaiecon.classes.category import Category
from xaiecon.classes.vote import Vote
from xaiecon.classes.view import View
from xaiecon.classes.board import Board
from xaiecon.classes.exception import XaieconException

from xaiecon.modules.core.helpers import send_notification
from xaiecon.modules.core.wrappers import login_wanted, login_required

from distutils.util import strtobool

from sqlalchemy.orm import joinedload
from sqlalchemy import desc, asc

post = Blueprint('post',__name__,template_folder='templates/post')

# Returns list of posts
def obtain_posts(u=None, sort='new', category='All', num=15, page=0):
	# Select data of SQL
	db = open_db()
	
	if num > 50:
		num = 50
	
	# Obtain category by name, if category does not exist then use All as
	# fallback
	category_obj = None
	if category != 'All':
		category_obj = db.query(Category).filter_by(name=category).first()
	
	is_nsfw = False
	if u is not None:
		is_nsfw = u.is_nsfw
	
	post = db.query(Post)
	
	if is_nsfw == False:
		post = post.filter_by(is_nsfw=False)
	
	# Only filter when category exists
	if category_obj is not None:
		post = post.filter_by(category_id=category_obj.id)
	
	# TODO: Use filter instead of array slice
	if sort == 'new':
		post = post.order_by(desc(Post.id))
		#post = post.filter(Post.id>=(page*num),Post.id>=((page+1)*num))
	elif sort == 'old':
		post = post.order_by(asc(Post.id))
		#post = post.filter(Post.id>=(page*num),Post.id<=((page+1)*num))
	else:
		abort(401)
	
	# Do query
	post = post.filter_by(is_nuked=False,is_deleted=False).options(joinedload('*')).all()
	
	db.close()
	return post

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

		# Give user fake internet points
		user = db.query(User).filter_by(id=post.user_id).first()
		db.query(User).filter_by(id=post.user_id).update({
			'net_points':user.net_points+val})
		
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
def ballot(u=None):
	db = open_db()
	try:
		pid = request.values.get('pid')
		
		post = db.query(Post).filter_by(id=pid).first()
		if post is None:
			abort(404)
		
		if post.show_votes == False:
			raise XaieconException('Poster disabled to see who voted')
		
		vote = db.query(Vote).filter_by(post_id=post.id).options(joinedload('user_info')).all()
		
		db.close()
		return render_template('post/voters.html',u=u,title = 'Ballot',votes=vote)
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',e=e)

@post.route('/post/unnuke', methods = ['GET','POST'])
@login_required
def unnuke(u=None):
	db = open_db()
	try:
		if u.is_admin == False:
			raise XaieconException('Only admins can un-nuke')

		pid = request.values.get('pid')
		post = db.query(Post).filter_by(id=pid).first()
		if post is None:
			abort(404)
		
		# Check that post is not already nuked and that user mods
		# the guild
		if post.is_deleted == True or post.is_nuked == False:
			raise XaieconException('Post already deleted or has been unnuked by user or someone else')
		
		# "Un-Nuke" post
		db.query(Post).filter_by(id=pid).update({'is_nuked':False})
		db.commit()
		
		db.close()
		return redirect(f'/post/view?pid={pid}')
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

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
		if post.is_deleted == True or post.is_nuked == True:
			raise XaieconException('Post already nuked/deleted by user or someone else')
		if not u.mods(board.id) and u.is_admin == False:
			raise XaieconException('You do not mod the origin board')
		
		# "Nuke" post
		db.query(Post).filter_by(id=pid).update({'is_nuked':True,'nuker_id':u.id})
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

		# Remove old image
		if post.is_image == True:
			try:
				os.remove(os.path.join('user_data',post.image_file))
				os.remove(os.path.join('user_data',post.thumb_file))
			except FileNotFoundError:
				pass
		
		# Set is_deleted to true
		db.query(Post).filter_by(id=pid).update({
			'is_deleted':True,
			'body':'[deleted by user]',
			'body_html':'[deleted by user]',
			'is_link':False,
			'is_image':False,
			'image_file':'',
			'thumb_file':'',
			'link_url':''})
		db.commit()
		db.close()
		return redirect(f'/post/view?pid={pid}')
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

				link = urllib.parse.quote(link,safe='/:$#?=&')
				parsed_link = urllib.parse.urlparse(link)

				if parsed_link.netloc == 'lbry.tv' or parsed_link.netloc == 'open.lbry.tv' or parsed_link.netloc == 'www.lbry.tv':
					embed_html = f'<iframe width="560" height="315" src="{link}" allowfullscreen></iframe>'
			
			is_nsfw = strtobool(request.form.get('is_nsfw','False'))
			
			if body == None or body == '':
				raise XaieconException('Empty body')
			if title == None or title == '':
				raise XaieconException('Empty title')

			body_html = ''
			
			# Remove old image
			try:
				if post.is_image == True:
					os.remove(os.path.join('user_data',post.image_file))
					os.remove(os.path.join('user_data',post.thumb_file))
			except FileNotFoundError:
				pass
			
			file = request.files['image']
			if file:
				try:
					# Build paths and filenames
					image_filename = secure_filename(f'{secrets.token_hex(12)}.jpeg')
					image_filepath = os.path.join('user_data',image_filename)

					thumb_filename = secure_filename(f'thumb_{image_filename}')
					thumb_filepath = os.path.join('user_data',thumb_filename)

					# Save full image file
					file.save(image_filepath)

					# Create thumbnail for image
					image = PIL.Image.open(image_filepath)
					image = image.convert('RGB')
					image.resize((128,128))
					image.save(thumb_filepath)

					db.query(Post).filter_by(id=pid).update({
						'image_file':image_filename,
						'thumb_file':thumb_filename,
						'is_image':True,
						'is_thumb':True})
				except PIL.UnidentifiedImageError:
					# Failure creating image!
					db.query(Post).filter_by(id=pid).update({
						'is_image':False,
						'is_thumb':False})
			else:
				db.query(Post).filter_by(id=pid).update({
					'is_image':False,
					'is_thumb':False})
				if is_link == True:
					img = obtain_post_thumb(link)
					if img is not None:
						thumb_filename = secure_filename(f'thumb_{secrets.token_hex(12)}.jpeg')
						thumb_filepath = os.path.join('user_data',thumb_filename)
						
						img = img.convert('RGB')
						img.resize((128,128))
						img.save(thumb_filepath)
						
						db.query(Post).filter_by(id=pid).update({
							'is_thumb':True,
							'thumb_file':thumb_filename})
			
			body_html = markdown(body)
			
			# Update post entry on database
			db.query(Post).filter_by(id=pid).update({
						'keywords':keywords,
						'body':body,
						'body_html':body_html,
						'is_link':is_link,
						'is_nsfw':is_nsfw,
						'title':title,
						'link_url':link,
						'category_id':category.id,
						'body_html':body_html,
						'embed_html':embed_html})
			db.commit()

			csam_thread = threading.Thread(target=csam_check_post, args=(u.id,post.link_url,))
			csam_thread.start()
			
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
			show_votes = strtobool(request.form.get('show_votes','False'))

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
			
			is_link = False
			embed_html = ''
			if link != '':
				is_link = True

				link = urllib.parse.quote(link,safe='/:$#?=&')
				parsed_link = urllib.parse.urlparse(link)

				if parsed_link.netloc == 'lbry.tv' or parsed_link.netloc == 'open.lbry.tv' or parsed_link.netloc == 'www.lbry.tv':
					embed_html = f'<iframe width="560" height="315" src="{link}" allowfullscreen></iframe>'
			
			is_nsfw = strtobool(request.form.get('is_nsfw','False'))

			if body == '' and is_link == False:
				raise XaieconException('Empty body')
			if title is None or title == '':
				raise XaieconException('Empty title')
			
			body_html = markdown(body)

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
						embed_html=embed_html,
						body_html=body_html,
						show_votes=show_votes)
			
			file = request.files['image']
			if file:
				try:
					# Build paths and filenames
					image_filename = secure_filename(f'{secrets.token_hex(12)}.jpeg')
					image_filepath = os.path.join('user_data',image_filename)
	
					thumb_filename = secure_filename(f'thumb_{image_filename}')
					thumb_filepath = os.path.join('user_data',thumb_filename)
	
					# Save full image file
					file.save(image_filepath)
	
					# Create thumbnail for image
					image = PIL.Image.open(image_filepath)
					image = image.convert('RGB')
					image.resize((128,128))
					image.save(thumb_filepath)
	
					post.image_file = image_filename
					post.thumb_file = thumb_filename
	
					post.is_image = True
					post.is_thumb = True
				except PIL.UnidentifiedImageError:
					pass
			else:
				post.is_image = False
				if is_link == True:
					img = obtain_post_thumb(link)
					if img is not None:
						thumb_filename = secure_filename(f'thumb_{secrets.token_hex(12)}.jpeg')
						thumb_filepath = os.path.join('user_data',thumb_filename)
						
						img = img.convert('RGB')
						img.resize((128,128))
						img.save(thumb_filepath)
						
						post.thumb_file = thumb_filename
						post.is_thumb = True
			
			db.add(post)
			db.commit()

			db.refresh(post)

			csam_thread = threading.Thread(target=csam_check_post, args=(u.id,post.id,))
			csam_thread.start()

			# Alert boardmaster of the posts in the guild
			send_notification(f'{post.title} - [/u/{post.user_info.username}](/user/view?uid={post.user_info.id}) on [/b/{board.name}](/board/view?bid={board.id})\n\r{post.body}',board.user_id)

			db.close()
			return redirect(f'/post/view?pid={post.id}')
		else:
			board = db.query(Board).filter_by(is_banned=False).options(joinedload('user_info')).all()
			categories = db.query(Category).all()
			db.close()
			return render_template('post/write.html',u=u,title='New post',boards=board,categories=categories)
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/thumb', methods = ['GET'])
@login_wanted
def thumb(u=None):
	id = int(request.values.get('pid',''))
	db = open_db()
	post = db.query(Post).filter_by(id=id).first()
	if post is None:
		abort(404)
	if post.thumb_file is None:
		abort(404)
	db.close()
	return send_from_directory('../user_data',post.thumb_file)

@post.route('/post/image', methods = ['GET'])
@login_wanted
def image(u=None):
	id = int(request.values.get('pid',''))
	db = open_db()
	post = db.query(Post).filter_by(id=id).first()
	if post is None:
		abort(404)
	if post.image_file is None:
		abort(404)
	db.close()
	return send_from_directory('../user_data',post.image_file)

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
	
	# Add one view
	if u is not None:
		if db.query(View).filter_by(user_id=u.id,post_id=pid).first() is None:
			view = View(user_id=u.id,post_id=pid)
			db.add(view)
			db.query(Post).filter_by(id=pid).update({'views':post.views+1})
			db.commit()

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
	
	ret = render_template('post/details.html',u=u,title=post.title,post=post,comment=comments)
	
	db.close()
	return ret

@post.route('/post/list', methods = ['GET'])
@post.route('/post/list/<sort>', methods = ['GET'])
@login_wanted
def list_posts(u=None, sort='new'):
	category = request.values.get('category','All')
	page = int(request.values.get('page','0'))
	num = int(request.values.get('num','15'))
	
	# Obtain posts
	posts = obtain_posts(u=u,sort=sort,category=category,page=page,num=num)
	
	# Slice out useless posts
	posts = posts[(page*num):((page+1)*num)]
	
	return render_template('post/list.html',u=u,title='Post frontpage',posts=posts,
		page=page,num=num,category=category,sort=sort)

@post.route('/post/nuked/<sort>', methods = ['GET'])
@login_required
def list_nuked(u=None, sort='new'):
	category = request.values.get('category','All')
	page = int(request.values.get('page','0'))
	num = int(request.values.get('num','15'))
	
	# Obtain posts
	posts = obtain_posts(u=u,sort=sort,category=category,page=page,num=num)
	
	# Slice out useless posts
	posts = posts[(page*num):((page+1)*num)]
	
	return render_template('post/list.html',u=u,title='Post frontpage',posts=post,
		page=page,num=num,category=category,sort=sort)

@post.route('/post/feed/<sort>', methods = ['GET'])
@login_required
def feed_posts(u=None, sort='new'):
	category = request.values.get('category','All')
	page = int(request.values.get('page','0'))
	num = int(request.values.get('num','15'))
	
	# Obtain posts
	posts = obtain_posts(u=u,sort=sort,category=category,page=page,num=num)
	
	# Remove all posts not in subscribed boards
	subs = u.subscribed_boards()
	subs_id = []
	for s in subs:
		subs_id.append(s.id)
	
	for p in posts:
		if p.board_id not in subs_id:
			posts.remove(p)
			continue
	
	# Slice out useless posts
	posts = posts[(page*num):((page+1)*num)]
	
	return render_template('post/list.html',u=u,title='My feed',post=post,
		page=page,num=num,category=category,sort=sort)

@post.route('/post/title_by_url', methods = ['GET'])
def title_by_url():
	# Used by javascript for getting title and put it as title
	# for using url'ed posts
	url = request.values.get('url')
	if url == '':
		return '',400

	headers = {'User-Agent':'xaiecon-busy'}
	x = requests.get(url, headers=headers)

	soup = BeautifulSoup(x.content,'html.parser')
	title = soup.find('title')
	if title is None:
		return '',400

	return title,200

@post.route('/post/search', methods = ['GET','POST'])
@login_wanted
def search(u=None):
	page = int(request.values.get('page','0'))
	num = int(request.values.get('num','15'))
	if request.method == 'POST':
		try:
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
				ps = post.options(joinedload('*')).order_by(desc(Post.creation_date)).filter_by(title=q).filter(Post.id>=(page*num),Post.id<=((page+1)*num)).all()
				for p in ps:
					posts.append(p)
			
			# Close the database
			db.close()
			return render_template('post/list.html',u=u,title='Post frontpage',posts=posts)
		except XaieconException as e:
			return render_template('user_error.html',u=u,title='Whoops!',err=e)
	else:
		return render_template('post/list.html',u=u,title='Post frontpage')

# Obtain thumbnail for post
def obtain_post_thumb(link: str):
	headers = {'User-Agent':'xaiecon-thumbnail-getter'}
	x = requests.get(link,headers=headers)
	if x.status_code not in [200,451]:
		return
	html = x.text
	soup = BeautifulSoup(html, 'html.parser')
	
	# Get image from img tag
	for img in soup.find_all('img'):
		try:
			# Get image by GET'ing it via HTTP and then Pillow'ing it
			x = requests.get(img['src'],headers=headers)
			im = PIL.Image.open(io.BytesIO(x.content))
			w, h = im.size
			if w <= 128 or h <= 128:
				continue
			return im
		except KeyError:
			continue
	return None

# Check user for csam, if so ban the user
def csam_check_post(uid: int, pid: int):
	db = open_db()

	post = db.query(Post).filter_by(id=pid).first()

	# Nothing to scan
	if post.is_link == False and post.is_image == False:
		return

	headers = {'User-Agent':'xaiecon-csam-check'}

	# Check link of post
	if post.is_link == True:
		for i in range(10):
			x = requests.get(post.link_url,headers=headers)
			if x.status_code in [200, 451]:
				break
			else:
				time.sleep(10)

	# And check image if it has one...
	if post.is_image == True:
		for i in range(10):
			x = requests.get(f'https://{os.environ.get("DOMAIN_NAME")}/post/thumb?pid={post.id}',headers=headers)
			if x.status_code in [200, 451]:
				break
			else:
				time.sleep(10)
		for i in range(10):
			x = requests.get(f'https://{os.environ.get("DOMAIN_NAME")}/post/image?pid={post.id}',headers=headers)
			if x.status_code in [200, 451]:
				break
			else:
				time.sleep(10)

	# If status code is not 451, else...
	if x.status_code != 451:
		return

	print(f'Offensive post {post.id} found!')

	# Remove all posts with offending url
	offensive_posts = db.query(Post).filter_by(link_url=post.link_url).all()
	for p in offensive_posts:
		if p.is_image == True:
			# Remove images
			os.remove(os.path.join('user_data',p.thumb_file))
			os.remove(os.path.join('user_data',p.image_file))

		# Blank posts
		db.query(Post).filter_by(id=p.id).update({
			'link_url':'',
			'is_image':False,
			'image_file':'',
			'thumb_file':'',
			'body':'[deleted by automatic csam detection]',
			'body_html':'[deleted by automatic csam detection]'
		})

		# Ban everyone involved
		user = db.query(User).filter_by(id=p.user_id).first()
		db.query(User).filter_by(id=p.user_id).update({
			'ban_reason':'CSAM Automatic Removal',
			'is_banned':True})
		db.commit()
		db.refresh(user)
	
	db.close()
	return

print('Post share ... ok')
