#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 23:19:38 2020

@author: superleaf1995
"""

import time
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

# This one sparks joy, this thing is lovely and beatiful, this is just beatiful
# the moment of beatiful increases when you see the scopes, hmmmm yes scopes
#
# This is the OAuthApp application for API endpoints
class OAuthApp(Base):
	__tablename__ = 'xaiecon_oauthapp'
	
	id = Column(Integer, primary_key=True)
	
	client_id = Column(String(128), nullable=False)
	client_secret = Column(String(128), nullable=False)
	name = Column(String(128), nullable=False)
	redirect_uri = Column(String(128), nullable=False)
	
	creation_date = Column(Integer, default=time.time())

	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'OAuthApp(%r,%r,%r)' % (self.name,self.creation_date,self.user_id)

class OAuthClient(Base):
	__tablename__ = 'xaiecon_oauthclient'
	
	id = Column(Integer, primary_key=True)
	
	oauth_code = Column(String(128), nullable=False)
	access_token = Column(String(128), nullable=False)
	refresh_token = Column(String(128), nullable=False)
	
	scope_read = Column(Boolean, default=False)
	scope_vote = Column(Boolean, default=False)
	scope_comment = Column(Boolean, default=False)
	scope_nuke = Column(Boolean, default=False)
	scope_yank = Column(Boolean, default=False)
	scope_kick = Column(Boolean, default=False)
	scope_post = Column(Boolean, default=False)
	scope_update = Column(Boolean, default=False)
	scope_board = Column(Boolean, default=False)
	scope_write = Column(Boolean, default=False)
	
	oauthapp_id = Column(Integer, ForeignKey('xaiecon_oauthapp.id'))
	oauthapp_info = relationship('OAuthApp', foreign_keys=[oauthapp_id])

	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'OAuthClient(%r)' % (self.id)