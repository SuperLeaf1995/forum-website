#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
import sqlalchemy
import sqlalchemy.orm.state
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def open_db():
	i = 0
	while 1:
		try:
			engine = sqlalchemy.create_engine(os.environ.get('SQLALCHEMY_URL',''))
			engine.execute('SELECT 1')
		except sqlalchemy.exc.OperationalError:
			print('Waiting for database to start ...')
			time.sleep(1)
			i += 1
		else:
			break
		if i > 5:
			engine = sqlalchemy.create_engine('sqlite:///:memory:',echo=True)
			break
	
	Base.metadata.create_all(engine)
	Session = sqlalchemy.orm.sessionmaker(bind=engine)
	
	session = Session()
	
	return session