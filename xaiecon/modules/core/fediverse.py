#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Module that allows fediverse with other instances
#

import requests
import time
import rsa

import base64
import hashlib
import Crypto
from Crypto.Cipher import AES

from flask import Blueprint, render_template, request, jsonify
from flask_babel import gettext

from xaiecon.classes.base import open_db
from xaiecon.classes.post import Post
from xaiecon.classes.user import User
from xaiecon.classes.board import Board
from xaiecon.classes.comment import Comment
from xaiecon.classes.vote import Vote
from xaiecon.classes.serverchain import Serverchain

from xaiecon.modules.core.wrappers import login_required, login_wanted

fediverse = Blueprint('fediverse',__name__,template_folder='templates/fediverse')

class AES256(object):
	def __init__(self, key):
		self.bs = AES.block_size
		self.key = hashlib.sha256(key.encode()).digest()
	
	def encrypt(self, raw):
		raw = self._pad(raw)
		iv = Crypto.Random.new().read(AES.block_size)
		cipher = AES.new(self.key, AES.MODE_CBC, iv)
		return base64.b64encode(iv+cipher.encrypt(raw.encode()))
	
	def decrypt(self, enc):
		enc = base64.b64decode(enc)
		iv = enc[:AES.block_size]
		cipher = AES.new(self.key, AES.MODE_CBC, iv)
		return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

# this endpoint is called when a chainer wants to chain
# and returns the public key so the other person
# can give us their private key for establishing a secure
# E2E connection
@fediverse.route('/fediverse/init/start', methods = ['GET','POST'])
@login_wanted
def init_start(u=None):
	ip_addr = request.remote_addr
	
	(pub_key, priv_key) = rsa.newkeys(1024)
	
	headers = {'User-Agent':'Xaiecon Chainer'}
	
	x = requests.get(f'https://{ip_addr}/init/recv_pub',headers=headers)

@fediverse.route('/fediverse/init/recv_pub', methods = ['GET','POST'])
@login_wanted
def init_recv_pub(u=None):
	ip_addr = request.remote_addr
	
	headers = {'User-Agent':'Xaiecon Chainer'}
	
	

@fediverse.route('/fediverse/add', methods = ['GET','POST'])
@login_required
def add_instance(u=None):
	return render_template('fediverse/add.html',u=u,title='Add instance')

@fediverse.route('/fediverse/recv', methods = ['GET','POST'])
def recv():
	db = open_db()

	ip_addr = request.remote_addr
	server = db.query(Serverchain).filter_by(ip_addr=ip_addr).first()
	if server is None:
		return jsonify({'message':f'fuck you {ip_addr}'}),401

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

@fediverse.route('/fediverse/endpoint', methods = ['POST','GET'])
def endpoint():
	db = open_db()

	ip_addr = request.remote_addr
	# Check that we are chained to server first, otherwise just reject them
	server = db.query(Serverchain).filter_by(ip_addr=ip_addr).first()
	if server is None:
		return jsonify({'message':f'fuck you {ip_addr}'}),401

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

@fediverse.route('/fediverse/sync', methods = ['GET','POST'])
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
	return '',200

print('Fediverse module ... ok')