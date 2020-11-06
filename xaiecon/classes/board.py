import datetime
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker, relationship
from xaiecon.classes.base import Base
from xaiecon.classes.user import *
from xaiecon.classes.category import *

class Board(Base):
	__tablename__ = 'xaiecon_boards'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	descr = Column(String(255), nullable=False)
	keywords = Column(String(255), nullable=False)
	creation_date = Column(DateTime, default=datetime.datetime.utcnow)
	
	category_id = Column(Integer, ForeignKey('xaiecon_categories.id'))
	category_info = relationship('Category', foreign_keys=[category_id])
	
	user_id = Column(Integer, ForeignKey('xaiecon_users.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	def __init__(self, **kwargs):
		super(Board, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Board(%r,%r,%r,%r)' % (self.name,self.descr,self.user_id,self.category_id)
