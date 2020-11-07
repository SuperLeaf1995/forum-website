#
# Simple post-sharing base module
#

import hashlib
from random import random

from os import path, remove
from flask import Blueprint, render_template, request, session, jsonify, redirect, send_from_directory, abort, send_file
from werkzeug.utils import secure_filename
from xaiecon.modules.core.cache import cache

from xaiecon.classes.base import open_db
from xaiecon.classes.user import User
from xaiecon.classes.post import Post
from xaiecon.classes.comment import Comment
from xaiecon.classes.log import Log
from xaiecon.classes.vote import Vote
from xaiecon.classes.exception import XaieconException

from xaiecon.modules.core.wrappers import login_wanted, login_required

from distutils.util import *
from sqlalchemy.orm import joinedload
from sqlalchemy import desc

comment = Blueprint('comment',__name__,template_folder='templates/comment')

@comment.route('/comment/vote', methods = ['GET','POST'])
@login_required
def vote(u=None):
	try:
		cid = request.values.get('cid')
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
		return '',200
	except XaieconException as e:
		return jsonify({'error':e}),400

@comment.route('/comment/reply', methods = ['POST'])
@login_required
def reply(u=None, cid=None):
	try:
		db = open_db()
		
		body = request.form.get('body')
		cid = request.form.get('cid')
		pid = request.form.get('pid')
		
		# Add reply
		reply = Comment(body=body,user_id=u.id,comment_id=cid)
		db.add(reply)
		db.commit()
		
		db.refresh(reply)
		
		# Increment number of comments
		post = db.query(Post).filter_by(id=pid).first()
		if post is None:
			abort(404)
		db.query(Post).filter_by(id=post.id).update({'number_comments':post.number_comments+1})
		
		db.close()
		return redirect(f'/comment/view?cid={reply.id}')
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@comment.route('/comment/view', methods = ['GET','POST'])
@login_wanted
def view(u=None):
	try:
		db = open_db()
		
		cid = request.values.get('cid','')

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
					comments.append(l)

		db.close()
		return render_template('post/details.html',u=u,title=post.title,post=post,comment=comments)
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

@comment.route('/comment/create', methods = ['POST'])
@login_required
def create(u=None):
	try:
		db = open_db()
		
		body = request.form.get('body')
		pid = request.form.get('pid')
		
		# Post exists in first place?
		post = db.query(Post).filter_by(id=pid).first()
		if post is None:
			abort(404)
		
		# Add comment
		comment = Comment(body=body,user_id=u.id,post_id=pid)
		db.add(comment)
		
		# Increment number of comments
		db.query(Post).filter_by(id=pid).update({'number_comments':post.number_comments+1})
		db.commit()
		
		db.close()
		return redirect(f'/post/view?pid={pid}')
	except XaieconException as e:
		return render_template('user_error.html',u=u,title = 'Whoops!',err=e)

print('Comment ... ok')
