#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Simple post-sharing base module
#

import os
import requests
import threading
import time
import secrets
import PIL
import io
import re

#import spacy

from bs4 import BeautifulSoup
from flask import Blueprint, render_template, request, jsonify, redirect, send_from_directory, abort
from flask_babel import gettext

from werkzeug.utils import secure_filename

from xaiecon.classes.base import open_db
from xaiecon.classes.user import User, UserFollow
from xaiecon.classes.post import Post
from xaiecon.classes.comment import Comment
from xaiecon.classes.category import Category
from xaiecon.classes.vote import Vote
from xaiecon.classes.view import View
from xaiecon.classes.board import Board, BoardSub
from xaiecon.classes.exception import XaieconException

from xaiecon.modules.core.markdown import md
from xaiecon.modules.core.cache import cache
from xaiecon.modules.core.limiter import limiter
from xaiecon.modules.core.helpers import send_notification, send_admin_notification, send_everyone_notification
from xaiecon.modules.core.wrappers import login_wanted, login_required, only_admin

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
	
	# Obtain category by name
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
	elif sort == 'old':
		post = post.order_by(asc(Post.id))
	else:
		abort(401)
	
	# Do query
	post = post.filter_by(is_nuked=False,is_deleted=False).options(joinedload('*')).all()
	
	db.close()
	return post

@post.route('/post/vote/<pid>', methods = ['POST'])
@login_required
def vote(u=None,pid=0):
	db = open_db()
	try:
		val = int(request.values.get('value','1'))
		
		if pid is None:
			abort(404)
		if val not in [-1,1]:
			abort(400)
		
		post = db.query(Post).filter_by(id=pid).first()
		if post is None:
			abort(404)
		
		user = db.query(User).filter_by(id=post.user_id).first()
		vote = db.query(Vote).filter_by(user_id=u.id,post_id=pid).first()
		
		if vote is not None and vote.value == val:
			db.query(User).filter_by(id=post.user_id).update({
				'net_points':user.net_points-vote.value})
			db.query(Vote).filter_by(user_id=u.id,post_id=pid).delete()
		else:
			db.query(Vote).filter_by(user_id=u.id,post_id=pid).delete()
			# Create vote relation
			vote = Vote(user_id=u.id,post_id=post.id,value=val)
			db.add(vote)
			
			db.query(User).filter_by(id=post.user_id).update({
				'net_points':user.net_points+val})
		
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
		cache.delete_memoized(view,pid=pid)
		cache.delete_memoized(list_posts)
		cache.delete_memoized(list_nuked)
		cache.delete_memoized(list_feed)
		return '',200
	except XaieconException as e:
		db.rollback()
		db.close()
		return jsonify({'error':e}),400

@post.route('/post/ballot/<pid>', methods = ['GET','POST'])
@login_wanted
@cache.memoize(timeout=8600)
def ballot(u=None,pid=0):
	db = open_db()
	try:
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
		
		cache.delete_memoized(view,pid=pid)
		cache.delete_memoized(list_posts)
		cache.delete_memoized(list_nuked)
		cache.delete_memoized(list_feed)
		
		return redirect(f'/post/view/{pid}')
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/admin/nuke/<pid>', methods = ['GET'])
@login_required
@only_admin
def admin_nuke(u=None,pid=0):
	db = open_db()
	
	post = db.query(Post).filter_by(id=pid).first()
	if post is None:
		abort(404)
	
	# Remove old image
	try:
		os.remove(os.path.join('user_data',post.image_file))
		os.remove(os.path.join('user_data',post.thumb_file))
	except FileNotFoundError:
		pass
	
	# Delete all stuff of the post
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
	
	# Kill user
	user = db.query(User).filter_by(id=post.user_id).first()
	db.query(User).filter_by(id=post.user_id).update({
		'ban_reason':'CSAM Automatic Removal',
		'is_banned':True})
	db.commit()
	db.refresh(user)
	
	db.close()
	
	# Delete caching
	cache.delete_memoized(view,pid=pid)
	cache.delete_memoized(list_posts)
	cache.delete_memoized(list_nuked)
	cache.delete_memoized(list_feed)
	return '',200

@post.route('/post/nuke/<pid>', methods = ['GET','POST'])
@login_required
def nuke(u=None,pid=0):
	db = open_db()
	try:
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
		
		cache.delete_memoized(view,pid=pid)
		cache.delete_memoized(list_posts)
		cache.delete_memoized(list_nuked)
		cache.delete_memoized(list_feed)
		
		send_admin_notification(f'Post with id {pid} has been nuked! Review it [here](/post/view/{pid}) and [do a final nuke](/admin/nuke/{pid}) if you consider it nescesary.')
		
		return redirect(f'/post/view/{pid}')
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/kick/<pid>', methods = ['GET','POST'])
@login_required
def kick(u=None,pid=0):
	db = open_db()
	try:
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
			
			cache.delete_memoized(view,pid=pid)
			cache.delete_memoized(list_posts)
			cache.delete_memoized(list_nuked)
			cache.delete_memoized(list_feed)
			
			return redirect(f'/post/view/{pid}')
		else:
			post = db.query(Post).filter_by(id=pid).first()
			db.close()
			return render_template('post/kick.html',u=u,title='Kick post',post=post)
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/yank/<pid>', methods = ['GET','POST'])
@login_required
def yank(u=None,pid=0):
	db = open_db()
	try:
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
			
			cache.delete_memoized(view,pid=pid)
			cache.delete_memoized(list_posts)
			cache.delete_memoized(list_nuked)
			cache.delete_memoized(list_feed)
			
			return redirect(f'/post/view/{pid}')
		else:
			boards = db.query(Board).filter_by(user_id=u.id).options(joinedload('user_info')).all()
			post = db.query(Post).filter_by(id=pid).first()
			db.close()
			return render_template('post/yank.html',u=u,title='Yank post',post=post,boards=boards)
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/delete/<pid>', methods = ['GET','POST'])
@login_required
def delete(u=None,pid=0):
	db = open_db()
	try:
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
		
		cache.delete_memoized(view,pid=pid)
		cache.delete_memoized(list_posts)
		cache.delete_memoized(list_nuked)
		cache.delete_memoized(list_feed)
		
		return redirect(f'/post/view/{pid}')
	except XaieconException as e:
		db.rollback()
		db.close()
		return jsonify({'error':e}),400

@post.route('/post/edit/<pid>', methods = ['POST','GET'])
@login_required
def edit(u=None,pid=0):
	db = open_db()
	try:
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
			category = int(request.form.get('category','0'))
			is_nsfw = strtobool(request.form.get('is_nsfw','False'))

			if len(title) > 255:
				raise XaieconException('Too long title')

			category = db.query(Category).filter_by(id=category).first()
			if category is None:
				raise XaieconException('Not a valid category')
			
			is_link = False
			embed_html = ''
			if link != '':
				is_link = True

				embed = obtain_embed_url(link)
				if embed is not None:
					embed_html = f'<iframe width="560" height="315" src="{embed}" allowfullscreen frameborder=\'0\'></iframe>'
			
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
						img.thumbnail((128,128))
						img.save(thumb_filepath)
						
						db.query(Post).filter_by(id=pid).update({
							'is_thumb':True,
							'thumb_file':thumb_filename})
			
			body_html = md(body)
			
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

			csam_thread = threading.Thread(target=csam_check_post, args=(u.id,post.id,))
			csam_thread.start()
			
			db.close()
			
			cache.delete_memoized(view,pid=pid)
			cache.delete_memoized(list_posts)
			cache.delete_memoized(list_nuked)
			cache.delete_memoized(list_feed)
			
			return redirect(f'/post/view/{pid}')
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
			category = int(request.values.get('category','0'))
			show_votes = strtobool(request.form.get('show_votes','False'))
			is_nsfw = strtobool(request.form.get('is_nsfw','False'))

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

				embed = obtain_embed_url(link)
				if embed is not None:
					embed_html = f'<iframe width="560" height="315" src="{embed}" allowfullscreen frameborder=\'0\'></iframe>'

			if body == '' and is_link == False:
				raise XaieconException('Empty body')
			if title is None or title == '':
				raise XaieconException('Empty title')
			
			body_html = md(body)
			
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
					image.thumbnail((128,128))
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
						
						timg = img.convert('RGB')
						timg.resize((128,128))
						timg.save(thumb_filepath)
						
						post.thumb_file = thumb_filename
						post.is_thumb = True
			
			db.add(post)
			db.commit()

			db.refresh(post)

			csam_thread = threading.Thread(target=csam_check_post, args=(u.id,post.id,))
			csam_thread.start()
			
			notif_msg = f'# {post.title}\n\rBy [/u/{post.user_info.username}](/user/view/{post.user_info.id}) on [/b/{board.name}](/board/view/{board.id})\n\r{post.body}'
			
			# Alert boardmaster of the posts in the guild
			if board.user_id != u.id:
				send_notification(notif_msg,board.user_id)
			
			# Notify followers
			follows = db.query(UserFollow).filter_by(target_id=u.id,notify=True).all()
			for f in follows:
				if f.user_id != u.id:
					send_notification(notif_msg,f.user_id)
			
			ping = body.find('@everyone')
			if ping != -1 and u.is_admin == True:
				users = db.query(User).all()
				for us in users:
					if us.id != u.id:
						send_notification(notif_msg,us.user_id)
			
			ping = body.find('@here')
			if ping != -1 and u.mods(post.board_id):
				subs = db.query(BoardSub).filter_by(board_id=post.board_id).all()
				users = [db.query(User).filter_by(id=subs.user_id).first() for s in subs]
				for us in users:
					if us.id != u.id:
						send_notification(notif_msg,us.user_id)
			
			for m in re.finditer(r'([u][\/]|[@])([a-zA-Z0-9#][^ ,.;:\n\r\t<>\/\'])*\w+',body):
				m = m.group(0)
				print(m)
				try:
					name = re.split(r'([u][\/]|[@])',m)[2]
					tag = name.split('#')
					
					# direct mention
					if len(tag) > 1:
						uid = int(tag[1])
						user = db.query(User).filter_by(id=uid).first()
						if user is None:
							raise IndexError
						send_notification(notif_msg,user.id)
					else:
						users = db.query(User).filter_by(username=name).all()
						if users is None:
							raise IndexError
						for user in users:
							send_notification(notif_msg,user.id)
				except IndexError:
					pass
			
			db.close()
			
			# Mess with everyone's feed
			cache.delete_memoized(list_posts)
			cache.delete_memoized(list_nuked)
			cache.delete_memoized(list_feed)
			
			return redirect(f'/post/view/{post.id}')
		else:
			board = db.query(Board).filter_by(is_banned=False).options(joinedload('user_info')).all()
			categories = db.query(Category).all()
			db.close()
			return render_template('post/write.html',u=u,title='New post',boards=board,categories=categories)
	except XaieconException as e:
		db.rollback()
		db.close()
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@post.route('/post/thumb/<pid>', methods = ['GET'])
@login_wanted
@limiter.exempt
def thumb(u=None,pid=0):
	db = open_db()
	post = db.query(Post).filter_by(id=pid).first()
	if post is None:
		abort(404)
	if post.thumb_file is None:
		abort(404)
	db.close()
	return send_from_directory('../user_data',post.thumb_file)

@post.route('/post/image/<pid>', methods = ['GET'])
@login_wanted
@limiter.exempt
def image(u=None,pid=0):
	db = open_db()
	post = db.query(Post).filter_by(id=pid).first()
	if post is None:
		abort(404)
	if post.image_file is None:
		abort(404)
	db.close()
	return send_from_directory('../user_data',post.image_file)

@post.route('/post/embed/<pid>', methods = ['GET'])
@login_wanted
@cache.memoize(timeout=8600)
def embed(u=None,pid=0):
	db = open_db()
	
	# Query post from database
	post = db.query(Post).filter_by(id=pid).options(joinedload('*')).first()
	if post is None:
		abort(404)
	
	# Dont let people see nsfw
	if post.is_nsfw == True and u.is_nsfw == False:
		abort(403)
	
	ret = render_template('post/embed.html',u=u,title=post.title,post=post)
	
	db.close()
	return ret

@post.route('/post/view/<pid>', methods = ['GET'])
@login_wanted
@cache.memoize(timeout=86400)
def view(u=None,pid=0):
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
	
	cache.delete_memoized(list_posts)
	cache.delete_memoized(list_nuked)
	cache.delete_memoized(list_feed)
	
	return ret

@post.route('/post/list', methods = ['GET'])
@post.route('/post/list/<category>', methods = ['GET'])
@post.route('/post/list/<category>/<sort>/<int:page>', methods = ['GET'])
@post.route('/post/list/<category>/<sort>/<int:page>', methods = ['GET'])
@login_wanted
@cache.memoize(timeout=86400)
def list_posts(u=None, sort='new', page=0, category='All'):
	num = 50
	
	# Obtain posts
	posts = obtain_posts(u=u,sort=sort,category=category,page=page,num=num)
	
	# Slice out useless posts
	posts = posts[(page*num):((page+1)*num)]
	
	return render_template('post/list.html',u=u,title='Post frontpage',posts=posts,
		page=page,num=num,category=category,sort=sort)

@post.route('/post/nuked', methods = ['GET'])
@post.route('/post/nuked/<category>', methods = ['GET'])
@post.route('/post/nuked/<category>/<sort>/<int:page>', methods = ['GET'])
@post.route('/post/nuked/<category>/<sort>/<int:page>', methods = ['GET'])
@login_required
@cache.memoize(timeout=86400)
def list_nuked(u=None, sort='new', page=0, category='All'):
	num = 50
	
	if u.is_admin == False:
		abort(403)
	
	# Obtain posts
	posts = obtain_posts(u=u,sort=sort,category=category,page=page,num=num)
	
	# Slice out useless posts
	posts = posts[(page*num):((page+1)*num)]
	
	return render_template('post/list.html',u=u,title='Post frontpage',posts=post,
		page=page,num=num,category=category,sort=sort)

@post.route('/post/feed', methods = ['GET'])
@post.route('/post/feed/<category>', methods = ['GET'])
@post.route('/post/feed/<category>/<sort>/<int:page>', methods = ['GET'])
@post.route('/post/feed/<category>/<sort>/<int:page>', methods = ['GET'])
@login_required
@cache.memoize(timeout=86400)
def list_feed(u=None, sort='new', page=0, category='All'):
	num = 50
	
	# Obtain posts
	posts = obtain_posts(u=u,sort=sort,category=category,page=page,num=num)
	
	# Remove all posts not in subscribed boards
	subs_id = [x.id for x in u.subscribed_boards()]
	# And also remove posts when they are not of followed persons
	follows_id = [x.id for x in u.following]
	
	for p in posts:
		if p.board_id not in subs_id and p.user_id not in follows_id and u.has_vote_on_post(p.id) == False:
			posts.remove(p)
			continue
	
	# Slice out useless posts
	posts = posts[(page*num):((page+1)*num)]
	
	return render_template('post/list.html',u=u,title='My feed',posts=posts,
		page=page,num=num,category=category,sort=sort)

@post.route('/post/title_by_url', methods = ['GET'])
@limiter.exempt
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

# TODO: Insert even more neural networks
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
			
			post = db.query(Post)
			is_nsfw = False
			if u is not None:
				is_nsfw = u.is_nsfw
			if is_nsfw == False:
				post = post.filter_by(is_nsfw=False)
			
			posts = post.options(joinedload('*')).order_by(desc(Post.creation_date)).all()
			for p in posts:
				alist = [
					p.title,
					p.body,
					p.user_info.username,
					p.category_info.name,
					p.board_info.name
				]
				
				threshold = 0
				for q in query:
					for a in alist:
						for t in a.split(' '):
							if q.lower() == t.lower():
								threshold = 1
								break
					
					if threshold == 0:
						posts.remove(p)
						break
			
			# Slice out useless posts
			posts = posts[(page*num):((page+1)*num)]
			
			# Close the database
			db.close()
			return render_template('post/list.html',u=u,title='Post frontpage',posts=posts,page=page,num=num)
		except XaieconException as e:
			return render_template('user_error.html',u=u,title='Whoops!',err=e)
	else:
		return render_template('post/list.html',u=u,title='Post frontpage')

# Return a embed url for post
# Works for:
# - PeerTube
# - Odysee
# - LBRY
def obtain_embed_url(link: str) -> str:
	headers = {'User-Agent':'xaiecon-embed-getter'}
	x = requests.get(link,headers=headers)
	if x.status_code not in [200]:
		return
	html = x.text
	soup = BeautifulSoup(html,'html.parser')
	
	platform = []
	platform.append(soup.find('meta',property='og:platform'))
	platform.append(soup.find('meta',property='og:site_name'))
	platform = [x for x in platform if x is not None]
	for p in platform:
		if p is None:
			continue
		
		p = p.get('content','')
		
		allowed_embeds = [
			'PeerTube',
			'LBRY',
			'YouTube'
		]
		if p == 'Xaiecon':
			return link
		if p not in allowed_embeds:
			continue
		meta = soup.find('meta',property='og:video:secure_url')
		return meta.get('content')
	return None

# Obtain thumbnail for post
def obtain_post_thumb(link: str):
	headers = {'User-Agent':'xaiecon-thumbnail-getter'}
	try:
		x = requests.get(link,headers=headers)
	except requests.exceptions.InvalidURL:
		return None
	if x.status_code not in [200]:
		return None
	
	filetype, extension = x.headers.get('content-type','text/html').split('/')
	if filetype == 'image':
		# Read the image, if it succeds then return that image
		try:
			im = PIL.Image.open(io.BytesIO(x.content))
			w, h = im.size
			return im
		except PIL.UnidentifiedImageError:
			pass
	
	html = x.text
	soup = BeautifulSoup(html,'html.parser')
	
	# Get image from meta tag or img tags
	# We save this image in the server like if it was a upload
	lst = []
	lst.append(soup.find('meta',property='twitter:image'))
	lst.append(soup.find('meta',property='og:image'))
	for i in soup.find_all('img'):
		lst.append(i)
	lst = [x for x in lst if x is not None]
	for img in lst:
		try:
			content = img.get('content')
			if content == '' or content is None:
				content = img.get('src')
				content = '{link}/{content}'
				if content == '' or content is None:
					continue
			
			x = requests.get(f'{content}',headers=headers)
			im = PIL.Image.open(io.BytesIO(x.content))
			w, h = im.size
			if w <= 100 or h <= 100:
				continue
			return im
		except requests.exceptions.InvalidURL:
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
			x = requests.get(f'https://{os.environ.get("DOMAIN_NAME")}/post/thumb/{post.id}',headers=headers)
			if x.status_code in [200, 451]:
				break
			else:
				time.sleep(10)
		for i in range(10):
			x = requests.get(f'https://{os.environ.get("DOMAIN_NAME")}/post/image/{post.id}',headers=headers)
			if x.status_code in [200, 451]:
				break
			else:
				time.sleep(10)

	# If status code is not 451, else...
	if x.status_code != 451:
		return

	print(f'Offensive post {post.id} found!')

	# Ban user
	
	user = db.query(User).filter_by(id=post.user_id).first()
	db.query(User).filter_by(id=post.user_id).update({
		'ban_reason':'CSAM Automatic Removal',
		'is_banned':True})
	db.commit()
	db.refresh(user)
	
	db.close()
	cache.delete_memoized(view)
	return

print('Post share ... ok')

# B :D