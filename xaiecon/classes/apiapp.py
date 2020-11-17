import time
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

# I can hear the sounds of thousands of developers screaming "wtf is this,
# where is muh oauth", and i reply "if you want your oauth go look to
# oauthapp.py, not here, this is suffering"
#
# This one is made for easy deployment, otherwise go use something serious like
# OAuthApp
class APIApp(Base):
	__tablename__ = 'xaiecon_apiapp'
	
	id = Column(Integer, primary_key=True)
	token = Column(String(128), nullable=False)
	name = Column(String(128), nullable=True)
	creation_date = Column(Integer, default=time.time())

	user_id = Column(Integer, ForeignKey('xaiecon_user.id'))
	user_info = relationship('User', foreign_keys=[user_id])
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def __repr__(self):
		return 'APIApp(%r,%r,%r,%r)' % (self.name,self.creation_date,self.token,self.user_id)