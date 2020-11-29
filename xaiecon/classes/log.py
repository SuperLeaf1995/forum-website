#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import secrets

from sqlalchemy.orm.state import InstanceState
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

class Log(Base):
	__tablename__ = 'xaiecon_log'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	creation_date = Column(Integer, default=time.time())
	
	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	uuid = Column(String(255), default=secrets.token_hex(126))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'Log(%r)' % (self.name)
	
	@property
	def json(self):
		data = {'type':type(self).__name__}
		for o in self.__dict__:
			dict_item = self.__dict__[o]
			if isinstance(dict_item,InstanceState):
				continue
			data[o] = dict_item
		return data