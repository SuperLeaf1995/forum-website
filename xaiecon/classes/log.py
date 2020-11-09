import time
from sqlalchemy import *
from sqlalchemy.orm import relation, sessionmaker

from xaiecon.classes.base import Base

class Log(Base):
	__tablename__ = 'xaiecon_log'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	creation_date = Column(Integer, default=time.time())
	
	def __init__(self, **kwargs):
		super(Log, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Log(%r)' % (self.name)
