import datetime
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker, relationship

from xaiecon.classes.base import Base

class Comment(Base):
	__tablename__ = 'xaiecon_comments'
	
	id = Column(Integer, primary_key=True)
	body = Column(String(4095), nullable=False)
	
	creation_date = Column(DateTime, default=datetime.datetime.utcnow)
	
	comment_id = Column(Integer, ForeignKey('xaiecon_comments.id'))
	post_id = Column(Integer, ForeignKey('xaiecon_posts.id'))
	user_id = Column(Integer, ForeignKey('xaiecon_users.id'))
	
	comment_info = relationship('Comment', foreign_keys=[comment_id])
	post_info = relationship('Post', foreign_keys=[post_id])
	user_info = relationship('User', foreign_keys=[user_id])
	
	def __init__(self, **kwargs):
		super(Comment, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Comment(%r,%r,%r,%r)' % (self.body,self.user_id,self.post_id,self.comment_id,
		self.downvote_count,self.upvote_count,self.total_vote_count)
