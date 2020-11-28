#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import secrets
from sqlalchemy import Column, String, Integer

from xaiecon.classes.base import Base

class Category(Base):
	__tablename__ = 'xaiecon_category'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(4095), nullable=False)
	creation_date = Column(Integer, default=time.time())
	
	uuid = Column(String(255), default=secrets.token_hex(254))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'Category(%r,%r)' % (self.name,self.creation_date)
