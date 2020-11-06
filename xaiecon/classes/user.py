import datetime
from flask import session
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker
from xaiecon.classes.base import Base, open_db
from xaiecon.classes.board import *
from xaiecon.classes.vote import *

class User(Base):
	__tablename__ = 'xaiecon_users'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	creation_date = Column(DateTime, default=datetime.datetime.utcnow)
	username = Column(String(255), nullable=False)
	biography = Column(String(8000), nullable=True)
	password = Column(String(510), nullable=False)
	auth_token = Column(String(510), nullable=False)
	email = Column(String(255), nullable=True)
	is_show_email = Column(Boolean, default=False)
	phone = Column(String(255), nullable=True)
	is_show_phone = Column(Boolean, default=False)
	fax = Column(String(255), nullable=True)
	is_show_fax = Column(Boolean, default=False)
	is_nsfw = Column(Boolean, default=False)
	is_admin = Column(Boolean, default=False)
	
	is_banned = Column(Boolean, default=False)
	ban_reason = Column(String(255), nullable=True)
	
	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
	
	def __repr__(self):
		return 'User(%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r)' % (self.name,
		self.biography,self.password,self.auth_token,self.email,self.is_show_email,
		self.fax,self.is_show_fax,self.is_nsfw,self.is_admin,self.unique_identifier,
		self.is_banned,self.ban_reason)

	def validate(self):
		if session.get('auth_token') != self.auth_token:
			return False
		return True
	
	def has_vote_on_post(self,pid=None):
		db = open_db()
		ret = db.query(Vote).filter_by(post_id=pid,user_id=self.id).first()
		db.close()
		
		return ret
	
	def has_vote_on_comment(self,cid=None):
		db = open_db()
		ret = db.query(Vote).filter_by(comment_id=cid,user_id=self.id).first()
		db.close()
		
		return ret
	
	def mods(self,bid=None):
		db = open_db()
		ret = db.query(Board).filter_by(id=bid,user_id=self.id).first()
		db.close()
		
		if ret is not None:
			return True
		return False
	
	def owned_boards(self):
		db = open_db()
		ret = db.query(Board).filter_by(user_id=self.id).all()
		db.close()
		return ret
