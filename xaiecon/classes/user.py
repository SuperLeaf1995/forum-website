#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

from flask import session
from sqlalchemy import Column, Integer, String, Boolean

from xaiecon.classes.base import Base, open_db
from xaiecon.classes.vote import Vote

class User(Base):
	__tablename__ = 'xaiecon_user'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	image_file = Column(String(255), nullable=True)
	username = Column(String(255), nullable=False)
	biography = Column(String(8000), nullable=True)
	password = Column(String(510), nullable=False)
	auth_token = Column(String(510), nullable=False)
	email = Column(String(255), nullable=True)
	is_show_email = Column(Boolean, default=False)
	phone = Column(String(255), nullable=True)
	is_show_phone = Column(Boolean, default=False)
	fax = Column(String(255), nullable=True)
	is_show_fax = Column(Boolean, default=False)
	is_nsfw = Column(Boolean, default=False)
	is_admin = Column(Boolean, default=False)
	can_make_board = Column(Boolean, default=True)
	
	is_banned = Column(Boolean, default=False)
	ban_reason = Column(String(255), nullable=True)

	creation_date = Column(Integer, default=time.time())
	net_points = Column(Integer, default=0)
	
	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)

	def __repr__(self):
		return 'User(%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r)' % (self.name,
		self.biography,self.password,self.auth_token,self.email,self.is_show_email,
		self.fax,self.is_show_fax,self.is_nsfw,self.is_admin,self.is_banned,self.ban_reason)

	def validate(self) -> bool:
		if session.get('auth_token') != self.auth_token:
			return False
		return True
	
	def has_vote_on_post(self, pid: int) -> Vote:
		db = open_db()
		ret = db.query(Vote).filter_by(post_id=pid,user_id=self.id).first()
		db.close()
		return ret
	
	def has_vote_on_comment(self, cid: int) -> Vote:
		db = open_db()
		ret = db.query(Vote).filter_by(comment_id=cid,user_id=self.id).first()
		db.close()
		return ret
	
	def mods(self, bid: int) -> bool:
		from xaiecon.classes.board import Board

		db = open_db()
		ret = db.query(Board).filter_by(id=bid,user_id=self.id).first()
		db.close()
		
		if ret is None:
			return False
		return True

	def is_subscribed(self, bid: int) -> bool:
		from xaiecon.classes.board import BoardSub

		db = open_db()
		ret = db.query(BoardSub).filter_by(board_id=bid,user_id=self.id).first()
		db.close()

		if ret is None:
			return False
		return True

	def is_banned_from_board(self, bid: int) -> bool:
		from xaiecon.classes.board import BoardBan

		db = open_db()
		ret = db.query(BoardBan).filter_by(board_id=bid,user_id=self.id).first()
		db.close()

		if ret is None:
			return False
		return True
	
	def moderated_boards(self):
		from xaiecon.classes.board import Board

		db = open_db()
		ret = db.query(Board).filter_by(user_id=self.id).all()
		db.close()
		return ret

	def subscribed_boards(self):
		from xaiecon.classes.board import Board, BoardSub

		db = open_db()
		sub = db.query(BoardSub).filter_by(user_id=self.id).all()
		ret = []
		for s in sub:
			b = db.query(Board).filter_by(id=s.board_id).first()
			ret.append(b)
		
		db.close()
		return ret
	
	@property
	def unread_notifications(self):
		from xaiecon.classes.notification import Notification
		
		db = open_db()
		ret = db.query(Notification).filter_by(user_id=self.id,is_read=False).all()
		db.close()
		return ret
	
	@property
	def unread_notifications_number(self) -> int:
		from xaiecon.classes.notification import Notification
		
		db = open_db()
		count = db.query(Notification).filter_by(user_id=self.id,is_read=False).count()
		db.close()
		return count

	def json(self):
		return {
			'name':self.name,
			'image_file':self.image_file,
			'username':self.username,
			'biography':self.biography,
			'password':self.password,
			'auth_token':self.auth_token,
			'email':self.email,
			'is_show_email':self.is_show_email,
			'phone':self.phone,
			'is_show_phone':self.is_show_phone,
			'fax':self.fax,
			'is_show_fax':self.is_show_fax,
			'is_nsfw':self.is_nsfw,
			'is_admin':self.is_admin,
			'is_banned':self.is_banned,
			'ban_reason':self.ban_reason,
			'creation_date':self.creation_date
		}

	def from_json(self, json):
		self.name = json.name
		self.image_file = json.image_file
		self.username = json.username
		self.biography = json.biography
		self.password = json.password
		self.auth_token = json.auth_token
		self.email = json.email
		self.is_show_email = json.is_show_email
		self.phone = json.phone
		self.is_show_phone = json.is_show_phone
		self.fax = json.fax
		self.is_show_fax = json.is_show_fax
		self.is_nsfw = json.is_nsfw
		self.is_admin = json.is_admin
		self.is_banned = json.is_banned
		self.ban_reason = json.ban_reason
		self.creation_date = json.creation_date