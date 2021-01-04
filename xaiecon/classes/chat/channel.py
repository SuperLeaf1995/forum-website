#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import secrets

from sqlalchemy.orm.state import InstanceState
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

class Channel(Base):
	__tablename__ = 'xaiecon_chat_channel'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	
	creation_date = Column(Integer, default=time.time())
	
	server_id = Column(Integer, ForeignKey('xaiecon_chat_server.id'))
	server_info = relationship('Server', foreign_keys=[server_id])
	
	uuid = Column(String(32), default=secrets.token_hex(16))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'Channel(%r,%r)' % (self.id,self.name)
	
	@property
	def json(self):
		data = {'type':type(self).__name__}
		for o in self.__dict__:
			dict_item = self.__dict__[o]
			if isinstance(dict_item,InstanceState):
				continue
			data[o] = dict_item
		return data