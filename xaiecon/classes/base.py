import os

from time import sleep
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker
from sqlalchemy.exc import OperationalError

from xaiecon.classes.exception import XaieconDatabaseException

Base = declarative_base()

def open_db():
	i = 0
	while 1:
		try:
			engine = create_engine(os.environ.get('SQLALCHEMY_URL',''))
			engine.execute('SELECT 1')
		except OperationalError:
			print('Waiting for database to start ...')
			sleep(1)
			i += 1
		else:
			break

		if i > 5:
			raise XaieconDatabaseException('Database timeout, either the database server is down or it\'s not accepting local connections. Contact sysadmin.')

	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	session = Session()
	
	return session