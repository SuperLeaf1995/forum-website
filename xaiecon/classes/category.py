import time
from sqlalchemy import *
from sqlalchemy.orm import relationship

from xaiecon.classes.base import Base

class Category(Base):
	__tablename__ = 'xaiecon_category'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(4095), nullable=False)
	creation_date = Column(Integer, default=time.time())
	
	def __init__(self, **kwargs):
		super(Category, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'Category(%r,%r)' % (self.name,self.creation_date)
