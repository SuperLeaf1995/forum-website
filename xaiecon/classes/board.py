#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import secrets
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

class Board(Base):
	__tablename__ = 'xaiecon_board'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	descr = Column(String(255), nullable=False)
	keywords = Column(String(255), nullable=False)
	creation_date = Column(Integer, default=time.time())
	
	is_banned = Column(Boolean, default=False)
	ban_reason = Column(String(255), nullable=True)
	
	sub_count = Column(Integer, default=0)
	
	has_icon = Column(Boolean, default=False)
	icon_file = Column(String(255), nullable=True)
	
	fallback_thumb = Column(String(64), nullable=True)
	
	category_id = Column(Integer, ForeignKey('xaiecon_category.id'))
	category_info = relationship('Category', foreign_keys=[category_id])
	
	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	uuid = Column(String(255), default=secrets.token_hex(254))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'Board(%r,%r,%r,%r)' % (self.name,self.descr,self.user_id,self.category_id)

class BoardBan(Base):
	__tablename__ = 'xaiecon_board_ban'
	
	id = Column(Integer, primary_key=True)
	reason = Column(String(255), nullable=False)
	expiration_date = Column(Integer, default=time.time())

	board_id = Column(Integer, ForeignKey('xaiecon_board.id'))
	board_info = relationship('Board', foreign_keys=[board_id])

	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	uuid = Column(String(255), default=secrets.token_hex(254))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'BoardBan(%r,%r,%r,%r)' % (self.reason,self.user_id,self.board_id,self.expiration_date)

class BoardSub(Base):
	__tablename__ = 'xaiecon_board_sub'
	
	id = Column(Integer, primary_key=True)

	board_id = Column(Integer, ForeignKey('xaiecon_board.id'))
	board_info = relationship('Board', foreign_keys=[board_id])

	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	uuid = Column(String(255), default=secrets.token_hex(254))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'BoardSub(%r,%r)' % (self.user_id,self.board_id)