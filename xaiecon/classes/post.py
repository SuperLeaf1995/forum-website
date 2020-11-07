import datetime
import time
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker, relationship

from xaiecon.classes.base import Base

class Post(Base):
	__tablename__ = 'xaiecon_posts'
	
	id = Column(Integer, primary_key=True)
	title = Column(String(255), nullable=False)
	body = Column(String(16000), nullable=False)
	link_url = Column(String(4095), nullable=False)
	is_link = Column(Boolean, default=False)
	is_nsfw = Column(Boolean, default=False)
	creation_date = Column(DateTime, default=datetime.datetime.utcnow)
	keywords = Column(String(255), nullable=False)
	views = Column(Integer, default=1)
	number_comments = Column(Integer, default=0)
	
	downvote_count = Column(Integer, default=1)
	upvote_count = Column(Integer, default=1)
	total_vote_count = Column(Integer, default=1)
	
	is_deleted = Column(Boolean, default=False)
	
	category_id = Column(Integer, ForeignKey('xaiecon_categories.id'))
	category_info = relationship('Category', foreign_keys=[category_id])
	
	user_id = Column(Integer, ForeignKey('xaiecon_users.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	board_id = Column(Integer, ForeignKey('xaiecon_boards.id'))
	board_info = relationship('Board', foreign_keys=[board_id])
	
	def __init__(self, **kwargs):
		super(Post, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Post(%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r)' % (self.name,self.descr,
		self.link_url,self.is_link,self.is_nsfw,self.is_admin,self.keywords,
		self.user_id,self.downvote_count,self.upvote_count,self.total_vote_count,
		self.is_deleted,self.category_id)
