import time
from sqlalchemy import *
from sqlalchemy.orm import relation, sessionmaker, relationship

from xaiecon.classes.base import Base

# Note: Not actually OAuth
class APIApp(Base):
	__tablename__ = 'xaiecon_apiapp'
	
	id = Column(Integer, primary_key=True)
	token = Column(String(128), nullable=False)
	name = Column(String(128), nullable=True)
	creation_date = Column(Integer, default=time.time())

	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	def __init__(self, **kwargs):
		super(APIApp, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'APIApp(%r,%r,%r,%r)' % (self.name,self.creation_date,self.token,self.user_id)
