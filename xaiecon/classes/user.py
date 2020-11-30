#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import secrets

from flask import session

from sqlalchemy.orm.state import InstanceState
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base, open_db
from xaiecon.classes.vote import Vote

class UserFollow(Base):
	__tablename__ = 'xaiecon_follower'
	
	id = Column(Integer, primary_key=True)
	
	creation_date = Column(Integer, default=time.time())
	
	show_in_feed = Column(Boolean, default=True)
	notify = Column(Boolean, default=True)
	
	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	target_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	target_info = relationship('User', foreign_keys=[user_id])
	
	uuid = Column(String(255), default=secrets.token_hex(254))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'UserFollow(%r,%r,%r)' % (self.user_id,self.target_id,self.creation_date)
	
	@property
	def json(self):
		data = {'type':type(self).__name__}
		for o in self.__dict__:
			dict_item = self.__dict__[o]
			if isinstance(dict_item,InstanceState):
				continue
			data[o] = dict_item
		return data

class User(Base):
	__tablename__ = 'xaiecon_user'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	image_file = Column(String(255), nullable=True)
	username = Column(String(255), nullable=False)
	biography = Column(String(8000), nullable=True)
	password = Column(String(510), nullable=False)
	auth_token = Column(String(510), nullable=False)
	
	email_auth_token = Column(String(255), nullable=True)
	email = Column(String(255), nullable=True)
	is_show_email = Column(Boolean, default=False)
	is_email_verified = Column(Boolean, default=False)
	
	phone = Column(String(255), nullable=True)
	is_show_phone = Column(Boolean, default=False)
	
	fax = Column(String(255), nullable=True)
	is_show_fax = Column(Boolean, default=False)
	
	is_nsfw = Column(Boolean, default=False)
	is_admin = Column(Boolean, default=False)
	can_make_board = Column(Boolean, default=True)
	uses_dark_mode = Column(Boolean, default=False)
	
	is_banned = Column(Boolean, default=False)
	ban_reason = Column(String(255), nullable=True)
	
	follow_count = Column(Integer, default=0)
	fallback_thumb = Column(String(64), nullable=True)
	
	creation_date = Column(Integer, default=time.time())
	net_points = Column(Integer, default=0)
	
	uuid = Column(String(255), default=secrets.token_hex(126))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

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
	
	@property
	def followers(self):
		db = open_db()
		ret = db.query(UserFollow).filter_by(target_id=self.id).all()
		db.close()
		return ret
	
	@property
	def following(self):
		db = open_db()
		ret = db.query(UserFollow).filter_by(user_id=self.id).all()
		db.close()
		return ret
	
	@property
	def followers_count(self) -> int:
		db = open_db()
		count = db.query(UserFollow).filter_by(target_id=self.id).count()
		db.close()
		return count
	
	@property
	def following_count(self) -> int:
		db = open_db()
		count = db.query(UserFollow).filter_by(user_id=self.id).count()
		db.close()
		return count
	
	def is_following(self, uid: int) -> bool:
		db = open_db()
		ret = db.query(UserFollow).filter_by(user_id=self.id,target_id=uid).first()
		return True if ret is not None else False
	
	@property
	def json(self):
		data = {'type':type(self).__name__}
		for o in self.__dict__:
			dict_item = self.__dict__[o]
			if isinstance(dict_item,InstanceState):
				continue
			data[o] = dict_item
		return data