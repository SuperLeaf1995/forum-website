import os

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker

Base = declarative_base()

def open_db():
	engine = create_engine(os.environ.get('SQLALCHEMY_URL',''))
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	session = Session()
	
	return session
