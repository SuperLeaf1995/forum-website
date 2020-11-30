#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import secrets

from sqlalchemy.orm.state import InstanceState
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

class Vote(Base):
	__tablename__ = 'xaiecon_vote'
	
	id = Column(Integer, primary_key=True)
	value = Column(Integer, default=1)

	creation_date = Column(Integer, default=time.time())
	
	comment_id = Column(Integer, ForeignKey('xaiecon_comment.id'))
	post_id = Column(Integer, ForeignKey('xaiecon_post.id'))
	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	
	comment_info = relationship('Comment', foreign_keys=[comment_id])
	post_info = relationship('Post', foreign_keys=[post_id])
	user_info = relationship('User', foreign_keys=[user_id])
	
	uuid = Column(String(32), default=secrets.token_hex(16))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'Vote(%r,%r,%r,%r)' % (self.value,self.user_id,self.post_id,self.comment_id)
	
	@property
	def json(self):
		data = {'type':type(self).__name__}
		for o in self.__dict__:
			dict_item = self.__dict__[o]
			if isinstance(dict_item,InstanceState):
				continue
			data[o] = dict_item
		return data