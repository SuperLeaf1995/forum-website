#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Simple post-sharing base module
#

from flask import Blueprint, render_template, request, jsonify, redirect,  abort
from flask_misaka import markdown
from flask_babel import gettext

from xaiecon.classes.base import open_db
from xaiecon.classes.post import Post
from xaiecon.classes.comment import Comment
from xaiecon.classes.user import UserFollow
from xaiecon.classes.vote import Vote
from xaiecon.classes.exception import XaieconException

from xaiecon.modules.core.cache import cache
from xaiecon.modules.core.post import view as view_p
from xaiecon.modules.core.post import list_posts, list_feed, list_nuked

from xaiecon.modules.core.helpers import send_notification
from xaiecon.modules.core.wrappers import login_wanted, login_required

from sqlalchemy.orm import joinedload

comment = Blueprint('comment',__name__,template_folder='templates/comment')

# AKA. Blanking the comment ;)
@comment.route('/comment/delete/<cid>', methods = ['GET','POST'])
@login_required
def delete(u=None,cid=0):
	db = open_db()
	
	# Query comment from id
	comment = db.query(Comment).filter_by(id=cid).first()
	if comment is None:
		abort(404)
	if comment.user_id != u.id and u.is_admin == False:
		abort(403)
	
	# Update comment
	db.query(Comment).filter_by(id=cid).update({
		'body':gettext('[deleted by user]'),
		'body_html':gettext('[deleted by user]')})
	db.commit()
	
	db.close()
	cache.delete_memoized(view)
	return redirect(f'/comment/view/{cid}')

@comment.route('/comment/edit/<cid>', methods = ['GET','POST'])
@login_required
def edit(u=None,cid=0):
	try:
		db = open_db()
		
		# Query comment from id
		comment = db.query(Comment).filter_by(id=cid).first()
		if comment is None:
			abort(404)
		if comment.user_id != u.id and u.is_admin == False:
			abort(403)
		
		if request.method == 'POST':
			body = request.form.get('body')
			
			if len(body) == 0:
				raise XaieconException(gettext('Body too short'))
			
			# Update comment
			db.query(Comment).filter_by(id=cid).update({
				'body':body,
				'body_html':markdown(body)})
			db.commit()
			
			db.close()
			cache.delete_memoized(view)
			return redirect(f'/comment/view/{cid}')
		else:
			db.close()
			return render_template('post/edit_comment.html',u=u,title='Edit comment',comment=comment)
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@comment.route('/comment/vote/<cid>', methods = ['GET','POST'])
@login_required
def vote(u=None,cid=0):
	try:
		val = int(request.values.get('value'))
		
		if cid is None or val is None or val not in [-1,1]:
			abort(400)
		
		db = open_db()
		
		vote = db.query(Vote).filter_by(user_id=u.id,comment_id=cid).first()
		comment = db.query(Comment).filter_by(id=cid).first()
		
		if comment is None:
			abort(404)
		
		# Delete previous vote
		db.query(Vote).filter_by(user_id=u.id,comment_id=cid).delete()
		
		if vote is not None and vote.value != val:
			# Create vote relation
			vote = Vote(user_id=u.id,comment_id=cid,value=val)
			db.add(vote)
		
		# Update vote count
		downvotes = db.query(Vote).filter_by(comment_id=cid,value=-1).count()
		upvotes = db.query(Vote).filter_by(comment_id=cid,value=1).count()
		db.query(Post).filter_by(id=cid).update({
			'downvote_count':downvotes,
			'upvote_count':upvotes,
			'total_vote_count':upvotes-downvotes})
		
		db.commit()
		
		db.close()
		
		cache.delete_memoized(view_p)
		cache.delete_memoized(list_posts)
		cache.delete_memoized(list_nuked)
		cache.delete_memoized(list_feed)
		return '',200
	except XaieconException as e:
		return jsonify({'error':e}),400

@comment.route('/comment/reply/<cid>', methods = ['POST'])
@login_required
def write_reply(u=None,cid=0):
	try:
		db = open_db()
		
		body = request.form.get('body')
		pid = int(request.form.get('pid',''))
		
		if len(body) == 0:
			raise XaieconException('Body too short')
		
		# Add reply
		reply = Comment(body=body,body_html=markdown(body),user_id=u.id,comment_id=cid)
		db.add(reply)
		db.commit()
		
		db.refresh(reply)
		
		# Increment number of comments
		post = db.query(Post).filter_by(id=pid).options(joinedload('*')).first()
		if post is None:
			abort(404)
		db.query(Post).filter_by(id=pid).update({'number_comments':post.number_comments+1})
		
		# Notify user who was replied, and post poster alert boardmaster of
		# the posts in the guild
		
		# Notify user of comment which we replied
		comment = db.query(Comment).filter_by(id=reply.comment_id).first()
		
		# Notify post poster
		if post.user_id != u.id:
			send_notification(f'Comment by [/u/{comment.user_info.username}](/user/view/{post.user_info.id}) on [/b/{post.board_info.name}](/board/view/{post.board_info.id}) in post ***{post.title}*** [View](/comment/view/{comment.id})\n\r{reply.body}',post.user_id)
		# Notify commenter
		if comment.user_id != u.id:
			send_notification(f'Comment by [/u/{comment.user_info.username}](/user/view/{post.user_info.id}) on [/b/{post.board_info.name}](/board/view/{post.board_info.id}) in post ***{post.title}*** [View](/comment/view/{comment.id})\n\r{reply.body}',comment.user_id)
		
		db.close()
		
		cache.delete_memoized(view_p)
		cache.delete_memoized(view,cid=cid)
		cache.delete_memoized(list_posts)
		cache.delete_memoized(list_nuked)
		cache.delete_memoized(list_feed)
		return redirect(f'/comment/view/{cid}')
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@comment.route('/comment/view/<cid>', methods = ['GET','POST'])
@login_wanted
@cache.memoize(timeout=8600)
def view(u=None,cid=0):
	try:
		db = open_db()
		
		comment = db.query(Comment).filter_by(id=cid).options(joinedload('*')).first()
		if comment is None:
			abort(404)
		
		post_comment = None
		post_cid = cid
		post = None
		while post is None:
			post_comment = db.query(Comment).filter_by(id=post_cid).first()
			if post_comment.post_id is None:
				post_cid = post_comment.comment_id
			else:
				post = db.query(Post).filter_by(id=post_comment.post_id).options(joinedload('*')).first()
				if post is None:
					abort(404)
				break

		# This is how we get replies, pardon for so many cringe
		comments = []

		# First add the top comment(s)
		comment.depth_level = 1
		comments.append(comment)
		
		# The level of depth given is 3 comments, 1 the top comments, 2 the replies to the top
		# and 3, the replies to the replies, after that user has to go manually through each new
		# discussion. This saves us a lot of time instead of omega nesting ;)
		# Obtain comments that reference the current comment (top)
		comms = db.query(Comment).filter_by(comment_id=cid).options(joinedload('*')).all()
		if comms is not None:
			# Obtain the comments of comments
			for c in comms:
				c.depth_level = 2
				ecomms = db.query(Comment).filter_by(comment_id=c.id).options(joinedload('*')).all()
				
				comments.append(c)
				for l in ecomms:
					l.depth_level = 3

					# Deepest comments, check if they have even more children
					if db.query(Comment).filter_by(comment_id=l.id).first() is not None:
						l.more_children = True
					
					comments.append(l)
		
		db.close()
		return render_template('post/details.html',u=u,title=post.title,post=post,comment=comments)
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@comment.route('/comment/create/<pid>', methods = ['POST'])
@login_required
def create(u=None,pid=0):
	try:
		db = open_db()
		
		body = request.form.get('body')
		
		if len(body) == 0:
			raise XaieconException('Body too short')
		
		# Post exists in first place?
		post = db.query(Post).filter_by(id=pid).options(joinedload('*')).first()
		if post is None:
			abort(404)
		
		# Add comment
		comment = Comment(body=body,body_html=markdown(body),user_id=u.id,post_id=pid)
		db.add(comment)
		
		# Increment number of comments
		db.query(Post).filter_by(id=pid).update({'number_comments':post.number_comments+1})
		db.commit()
		
		send_notification(f'Comment by [/u/{comment.user_info.username}](/user/view/{post.user_info.id}) on [/b/{post.board_info.name}](/board/view/{post.board_info.id}) in post ***{post.title}*** [View](/comment/view/{comment.id})\n\r{comment.body}',post.user_id)
		
		# Notify followers
		follows = db.query(UserFollow).filter_by(target_id=u.id,notify=True).all()
		for f in follows:
			send_notification(f'Comment by [/u/{comment.user_info.username}](/user/view/{post.user_info.id}) on [/b/{post.board_info.name}](/board/view/{post.board_info.id}) in post ***{post.title}*** [View](/comment/view/{comment.id})\n\r{comment.body}',f.user_id)
		
		db.close()
		
		cache.delete_memoized(view_p)
		cache.delete_memoized(list_posts)
		cache.delete_memoized(list_nuked)
		cache.delete_memoized(list_feed)
		return redirect(f'/post/view/{pid}')
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

print('Comment ... ok')
