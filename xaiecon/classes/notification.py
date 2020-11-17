import time

from sqlalchemy import *
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

class Notification(Base):
	__tablename__ = 'xaiecon_notification'
	
	id = Column(Integer, primary_key=True)
	is_read = Column(Boolean, default=False)
	body = Column(String(16000), primary_key=True)
	creation_date = Column(Integer, default=time.time())
	
	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	def __init__(self, **kwargs):
		super(Notification, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Notification(%r,%r)' % (self.user_id,self.body)