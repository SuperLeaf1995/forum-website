#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import secrets

from sqlalchemy.orm.state import InstanceState
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

# I can hear the sounds of thousands of developers screaming "wtf is this,
# where is muh oauth", and i reply "if you want your oauth go look to
# oauthapp.py, not here, this is suffering"
#
# This one is made for easy deployment, otherwise go use something serious like
# OAuthApp
class APIApp(Base):
	__tablename__ = 'xaiecon_apiapp'
	
	id = Column(Integer, primary_key=True)
	token = Column(String(128), nullable=False)
	name = Column(String(128), nullable=True)
	creation_date = Column(Integer, default=time.time())

	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	uuid = Column(String(255), default=secrets.token_hex(126))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'APIApp(%r,%r,%r,%r)' % (self.name,self.creation_date,self.token,self.user_id)
	
	@property
	def json(self):
		data = {'type':type(self).__name__}
		for o in self.__dict__:
			dict_item = self.__dict__[o]
			if isinstance(dict_item,InstanceState):
				continue
			data[o] = dict_item
		return data