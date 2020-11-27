#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

from sqlalchemy import Column, Integer, String, Boolean

from xaiecon.classes.base import Base

class Serverchain(Base):
	__tablename__ = 'xaiecon_serverchain'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	ip_addr = Column(String(255), nullable=False)
	
	# Our public key we give to the other server
	our_public_key = Column(String(255), nullable=True)
	# Our private key we store for ourselves for decrypting data
	our_private_key = Column(String(255), nullable=True)
	# The private key of the other server, hashed with our public key
	their_private_key = Column(String(255), nullable=True)
	
	is_banned = Column(Boolean, default=False)
	is_active = Column(Boolean, default=False)
	is_online = Column(Boolean, default=False)
	creation_date = Column(Integer, default=time.time())
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'Serverchain(%r,%r,%r,%r,%r,%r,%r,%r)' % (self.name,self.ip_addr,
			self.is_banned,self.is_online,self.is_active,self.endpoint_url,
			self.internal_password,self.external_password)