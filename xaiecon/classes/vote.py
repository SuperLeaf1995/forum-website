import datetime

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker, relationship

from xaiecon.classes.base import Base

class Vote(Base):
	__tablename__ = 'xaiecon_votes'
	
	id = Column(Integer, primary_key=True)
	
	creation_date = Column(DateTime, default=datetime.datetime.utcnow)
	
	value = Column(Integer, default=1)
	
	comment_id = Column(Integer, ForeignKey('xaiecon_comments.id'))
	post_id = Column(Integer, ForeignKey('xaiecon_posts.id'))
	user_id = Column(Integer, ForeignKey('xaiecon_users.id'))
	
	comment_info = relationship('Comment', foreign_keys=[comment_id])
	post_info = relationship('Post', foreign_keys=[post_id])
	user_info = relationship('User', foreign_keys=[user_id])
	
	def __init__(self, **kwargs):
		super(Vote, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Vote(%r,%r,%r,%r)' % (self.value,self.user_id,self.post_id,self.comment_id)
