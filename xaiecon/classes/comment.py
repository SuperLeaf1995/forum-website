#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

class Comment(Base):
	__tablename__ = 'xaiecon_comment'
	
	id = Column(Integer, primary_key=True)
	
	body_html = Column(String(16000), nullable=False)
	body = Column(String(16000), nullable=False)
	
	creation_date = Column(Integer, default=time.time())
	
	comment_id = Column(Integer, ForeignKey('xaiecon_comment.id'))
	post_id = Column(Integer, ForeignKey('xaiecon_post.id'))
	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	
	comment_info = relationship('Comment', foreign_keys=[comment_id])
	post_info = relationship('Post', foreign_keys=[post_id])
	user_info = relationship('User', foreign_keys=[user_id])
	
	def __init__(self, **kwargs):
		super(Comment, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Comment(%r,%r,%r,%r)' % (self.body,self.user_id,self.post_id,self.comment_id)

	def json(self):
		return {
			'body':self.body,
			'body_html':self.body_html,
			'creation_date':self.creation_date,
			'comment_id':self.comment_id,
			'post_id':self.post_id,
			'user_id':self.user_id
		}

	def from_json(self, json):
		self.body = json.body
		self.body_html = json.body_html
		self.creation_date = json.creation_date
		if json.comment_id != 0:
			self.comment_id = json.comment_id
		if json.post_id != 0:
			self.post_id = json.post_id
		self.user_id = json.user_id
