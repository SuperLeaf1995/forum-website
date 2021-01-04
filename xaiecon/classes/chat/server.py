#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import secrets

from sqlalchemy.orm.state import InstanceState
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

class Server(Base):
	__tablename__ = 'xaiecon_chat_server'
	
	id = Column(Integer, primary_key=True)
	
	name = Column(String(255), nullable=False)
	has_icon = Column(Boolean, default=False)
	icon_file = Column(String(255), nullable=False)
	
	creation_date = Column(Integer, default=time.time())
	
	user_count = Column(Integer, default=1)
	
	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	uuid = Column(String(32), default=secrets.token_hex(16))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'Server(%r,%r,%r,%r)' % (self.id,self.name,self.has_icon,self.icon_file)
	
	@property
	def json(self):
		data = {'type':type(self).__name__}
		for o in self.__dict__:
			dict_item = self.__dict__[o]
			if isinstance(dict_item,InstanceState):
				continue
			data[o] = dict_item
		return data

class ServerJoin(Base):
	__tablename__ = 'xaiecon_chat_server_join'
	
	id = Column(Integer, primary_key=True)
	
	server_id = Column(Integer, ForeignKey('xaiecon_chat_server.id'))
	server_info = relationship('Server', foreign_keys=[server_id])
	
	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	uuid = Column(String(32), default=secrets.token_hex(16))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'ServerJoin(%r,%r)' % (self.user_id,self.server_id)
	
	@property
	def json(self):
		data = {'type':type(self).__name__}
		for o in self.__dict__:
			dict_item = self.__dict__[o]
			if isinstance(dict_item,InstanceState):
				continue
			data[o] = dict_item
		return data