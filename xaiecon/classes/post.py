import time
from sqlalchemy import *
from sqlalchemy.orm import relation, sessionmaker, relationship

from xaiecon.classes.base import Base

class Post(Base):
	__tablename__ = 'xaiecon_post'
	
	id = Column(Integer, primary_key=True)
	title = Column(String(255), nullable=False)
	body = Column(String(16000), nullable=False)
	link_url = Column(String(4095), nullable=False)
	is_link = Column(Boolean, default=False)
	is_nsfw = Column(Boolean, default=False)
	keywords = Column(String(255), nullable=False)
	views = Column(Integer, default=1)
	number_comments = Column(Integer, default=0)
	creation_date = Column(Integer, default=time.time())
	
	downvote_count = Column(Integer, default=1)
	upvote_count = Column(Integer, default=1)
	total_vote_count = Column(Integer, default=1)
	
	is_deleted = Column(Boolean, default=False)
	
	category_id = Column(Integer, ForeignKey('xaiecon_category.id'))
	category_info = relationship('Category', foreign_keys=[category_id])
	
	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	board_id = Column(Integer, ForeignKey('xaiecon_board.id'))
	board_info = relationship('Board', foreign_keys=[board_id])
	
	def __init__(self, **kwargs):
		super(Post, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Post(%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r)' % (self.name,self.descr,
		self.link_url,self.is_link,self.is_nsfw,self.is_admin,self.keywords,
		self.user_id,self.downvote_count,self.upvote_count,self.total_vote_count,
		self.is_deleted,self.category_id)
