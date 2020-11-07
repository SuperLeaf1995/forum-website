from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base

from xaiecon.classes.base import Base

class Serverchain(Base):
	__tablename__ = 'xaiecon_serverchains'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	ip_addr = Column(String(255), nullable=False)
	
	def __init__(self, **kwargs):
		super(Serverchain, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Serverchain(%r,%r)' % (self.name,self.ip_addr)
