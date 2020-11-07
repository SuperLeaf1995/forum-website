from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker

from xaiecon.classes.base import Base

class Log(Base):
	__tablename__ = 'xaiecon_logs'
	
	id = Column(Integer, primary_key=True)
	creation_date = Column(Time)
	name = Column(String(255), nullable=False)
	
	def __init__(self, **kwargs):
		super(Log, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Log(%r)' % (self.name)
