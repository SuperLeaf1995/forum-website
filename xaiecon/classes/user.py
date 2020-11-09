import time
import typing

from flask import session
from sqlalchemy import *
from sqlalchemy.orm import relation, sessionmaker

from xaiecon.classes.base import Base, open_db
from xaiecon.classes.vote import Vote

class User(Base):
	__tablename__ = 'xaiecon_user'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	image_file = Column(String(255), nullable=True)
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

	creation_date = Column(Integer, default=time.time())
	
	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)

	def __repr__(self):
		return 'User(%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r)' % (self.name,
		self.biography,self.password,self.auth_token,self.email,self.is_show_email,
		self.fax,self.is_show_fax,self.is_nsfw,self.is_admin,self.is_banned,self.ban_reason)

	def validate(self) -> bool:
		if session.get('auth_token') != self.auth_token:
			return False
		return True
	
	def has_vote_on_post(self, pid: int) -> Vote:
		db = open_db()
		ret = db.query(Vote).filter_by(post_id=pid,user_id=self.id).first()
		db.close()
		return ret
	
	def has_vote_on_comment(self, cid: int) -> Vote:
		db = open_db()
		ret = db.query(Vote).filter_by(comment_id=cid,user_id=self.id).first()
		db.close()
		return ret
	
	def mods(self,bid: int) -> bool:
		from xaiecon.classes.board import Board

		db = open_db()
		ret = db.query(Board).filter_by(id=bid,user_id=self.id).first()
		db.close()
		
		if ret is not None:
			return True
		return False
	
	def owned_boards(self):
		from xaiecon.classes.board import Board

		db = open_db()
		ret = db.query(Board).filter_by(user_id=self.id).all()
		db.close()
		return ret
