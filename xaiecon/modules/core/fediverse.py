#
# Module that allows fediverse with other instances
#

import requests
import os
import json
import pprint

from flask import Blueprint, render_template, request, jsonify

from werkzeug.security import check_password_hash, generate_password_hash

from cryptography.fernet import Fernet
from xaiecon.modules.core.cache import cache
from xaiecon.classes.base import open_db
from xaiecon.classes.post import Post
from xaiecon.classes.user import User
from xaiecon.classes.board import Board
from xaiecon.classes.comment import Comment
from xaiecon.classes.vote import Vote
from xaiecon.classes.serverchain import Serverchain
from xaiecon.classes.exception import XaieconException

from xaiecon.modules.core.wrappers import login_wanted, login_required

fediverse = Blueprint('fediverse',__name__,template_folder='templates/fediverse')

@fediverse.route('/fediverse/recv')
def recv():
	db = open_db()

	ip_addr = request.remote_addr
	server = db.query(Serverchain).filter_by(ip_addr=ip_addr).first()
	if server is None:
		return jsonify({'message':'fuck you'}),401

	data = request.get_json(force=True)
	if data is None:
		return jsonify({'message':'no data'}),400

	for d in data.users:
		obj = User().from_json(d)
		db.add(obj)
	for d in data.boards:
		obj = Board().from_json(d)
		db.add(obj)
	for d in data.posts:
		obj = Post().from_json(d)
		db.add(obj)
	for d in data.comments:
		obj = Comment().from_json(d)
		db.add(obj)
	for d in data.votes:
		obj = Vote().from_json(d)
		db.add(obj)

	db.commit()
	db.close()
	return jsonify({'message':'done'}),200

@fediverse.route('/fediverse/endpoint', methods = ['GET'])
def endpoint():
	db = open_db()

	ip_addr = request.remote_addr
	# Check that we are chained to server first, otherwise just reject them
	server = db.query(Serverchain).filter_by(ip_addr=ip_addr).first()
	if server is None:
		return jsonify({'message':'fuck you'}),401

	users = db.query(User).filter(User.id>=int(request.values.get('last_user_id','0'))).all()
	boards = db.query(Board).filter(Board.id>=int(request.values.get('last_board_id','0'))).all()
	posts = db.query(Post).filter(Post.id>=int(request.values.get('last_post_id','0'))).all()
	comments = db.query(Comment).filter(Comment.id>=int(request.values.get('last_comment_id','0'))).all()
	votes = db.query(Vote).filter(Vote.id>=int(request.values.get('last_vote_id','0'))).all()
	
	#url = server.endpoint_url
	#requests.post(url, json=data)

	data = {
		'users':[x.json() for x in users],
		'boards':[x.json() for x in boards],
		'posts':[x.json() for x in posts],
		'comments':[x.json() for x in comments],
		'votes':[x.json() for x in votes]
	}

	url = server.endpoint_url
	requests.post(url, json=data)

	db.close()
	return jsonify({'message':'done syncing'}),200

def sync():
	db = open_db()
	data = {
		'last_comment_id':db.query(Comment).order_by(Comment.id.desc()).first().id,
		'last_post_id':db.query(Post).order_by(Post.id.desc()).first().id,
		'last_user_id':db.query(User).order_by(User.id.desc()).first().id,
		'last_board_id':db.query(Board).order_by(Board.id.desc()).first().id,
		'last_vote_id':db.query(Vote).order_by(Vote.id.desc()).first().id
	}

	# Alert all servers that we need to sync NOW
	servers = db.query(Serverchain).all()
	for s in servers:
		url = s.endpoint_url
		requests.post(url, json=data)

	db.close()

	# Wait for all of these lazy assholes to get up
	time.sleep(5)

print('Fediverse module ... ok')