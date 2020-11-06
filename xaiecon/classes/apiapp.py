import datetime
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker, relationship
from xaiecon.classes.base import Base

# Note: Not actually OAuth
class APIApp(Base):
	__tablename__ = 'xaiecon_api_app'
	
	id = Column(Integer, primary_key=True)
	token = Column(String(128), nullable=False)
	name = Column(String(128), nullable=True)
	creation_date = Column(DateTime, default=datetime.datetime.utcnow)
	
	user_id = Column(Integer, ForeignKey('xaiecon_users.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	def __init__(self, **kwargs):
		super(APIApp, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'APIApp(%r,%r)' % (self.name,self.creation_date)
