import time

from sqlalchemy import *
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
	
	def __init__(self, **kwargs):
		super(Vote, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Vote(%r,%r,%r,%r)' % (self.value,self.user_id,self.post_id,self.comment_id)

	def json(self):
		return {
			'value':self.value,
			'creation_date':self.creation_date,
			'comment_id':self.comment_id,
			'post_id':self.post_id,
			'user_id':self.user_id
		}

	def from_json(self, json):
		self.value = json.value
		self.creation_date = json.creation_date
		if json.comment_id != 0:
			self.comment_id = json.comment_id
		if json.post_id != 0:
			self.post_id = json.post_id
		self.user_id = json.user_id