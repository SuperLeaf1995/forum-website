#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import secrets

from sqlalchemy.orm.state import InstanceState
from sqlalchemy import Column, Boolean, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

class Notification(Base):
	__tablename__ = 'xaiecon_notification'
	
	id = Column(Integer, primary_key=True)
	is_read = Column(Boolean, default=False)
	body = Column(String(16000), nullable=False)
	body_html = Column(String(16000), nullable=False)
	creation_date = Column(Integer, default=time.time())
	
	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	uuid = Column(String(32), default=secrets.token_hex(16))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'Notification(%r,%r)' % (self.user_id,self.body)
	
	@property
	def json(self):
		data = {'type':type(self).__name__}
		for o in self.__dict__:
			dict_item = self.__dict__[o]
			if isinstance(dict_item,InstanceState):
				continue
			data[o] = dict_item
		return data