import time
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

class Log(Base):
	__tablename__ = 'xaiecon_log'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	creation_date = Column(Integer, default=time.time())
	
	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	def __init__(self, **kwargs):
		super(Log, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Log(%r)' % (self.name)
