import time

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

class View(Base):
	__tablename__ = 'xaiecon_view'
	
	id = Column(Integer, primary_key=True)
	creation_date = Column(Integer, default=time.time())

	post_id = Column(Integer, ForeignKey('xaiecon_post.id'))
	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))

	post_info = relationship('Post', foreign_keys=[post_id])
	user_info = relationship('User', foreign_keys=[user_id])
	
	def __init__(self, **kwargs):
		super(View, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Vote(%r,%r)' % (self.user_id,self.post_id)