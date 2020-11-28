#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import secrets

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
	
	uuid = Column(String(255), default=secrets.token_hex(254))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'Notification(%r,%r)' % (self.user_id,self.body)