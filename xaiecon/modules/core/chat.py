#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Module that allows fediverse with other instances
#

# TODO: implement activitypub

import requests
from bs4 import BeautifulSoup

from flask import Blueprint, render_template, request, jsonify, make_response, abort, session
from flask_babel import gettext

from werkzeug.security import generate_password_hash

from xaiecon.classes.base import open_db
from xaiecon.modules.core.wrappers import login_required

from xaiecon.classes.chat.channel import Channel
from xaiecon.classes.chat.message import Message
from xaiecon.classes.chat.server import Server, ServerJoin

from xaiecon.modules.core.markdown import md
from xaiecon.modules.core.socketio import socketio
from flask_socketio import emit, send

from sqlalchemy.orm import joinedload
from sqlalchemy import desc, asc

chat = Blueprint('chat',__name__,template_folder='templates/chat')

@chat.route('/chat', methods=['GET'])
@login_required
def chat_base(u=None):
	db = open_db()
	
	# Get our serverlist
	joins = db.query(ServerJoin).filter_by(user_id=u.id).all()
	servers = []
	for j in joins:
		server = db.query(Server).filter_by(id=j.server_id).options(joinedload('*')).first()
		servers.append(server)
	
	db.close()
	return render_template('chat/base.html',u=u,servers=servers)

@socketio.on('connect')
def connect():
	print('connection')

@socketio.on('message_send')
@login_required
def message_send(data=None,u=None):
	if data is None:
		return '',400
	
	if data['channel_id'] == 0:
		return '',400
	
	db = open_db()
	
	body_html = data['body']
	body_html = md(body_html)
	
	# Obtain embeds
	soup = BeautifulSoup(body_html,'html.parser')
	for a in soup.find_all('a'):
		try:
			if a.get('href',None) is None:
				continue
			
			# Append embed html
			embed = obtain_embed_url(a['href'])
			if embed is None:
				continue
			
			embed_html = f'<iframe width="560" height="315" src="{embed}" allowfullscreen frameborder=\'0\'></iframe>'
			body_html += embed_html
		except requests.exceptions.ConnectionError:
			pass
		except requests.exceptions.MissingSchema:
			pass
	
	print(body_html)
	
	# Create new message
	message = Message(
			body=data['body'],
			body_html=body_html,
			user_id=u.id,
			channel_id=data['channel_id'])
	db.add(message)
	db.commit()
	
	# Send everyone the message
	db.refresh(message)
	
	data = {
		'time_utc': message.creation_date,
		'username': u.username,
		'uid': u.id,
		'body': message.body_html,
		'msg_id': message.id,
		'channel_id': data['channel_id']
	}
	emit('make_message',data,broadcast=True)
	
	db.close()

# Return a embed url for message
# Works for:
# - PeerTube
# - Odysee
# - LBRY
def obtain_embed_url(link: str) -> str:
	headers = {'User-Agent':'xaiecon-embed-getter'}
	x = requests.get(link,headers=headers)
	if x.status_code not in [200]:
		return
	html = x.text
	soup = BeautifulSoup(html,'html.parser')
	
	platform = []
	platform.append(soup.find('meta',property='og:platform'))
	platform.append(soup.find('meta',property='og:site_name'))
	platform = [x for x in platform if x is not None]
	for p in platform:
		if p is None:
			continue
		
		p = p.get('content','')
		
		allowed_embeds = [
			'PeerTube',
			'LBRY',
			'YouTube'
		]
		if p == 'Xaiecon':
			return link
		if p not in allowed_embeds:
			continue
		meta = soup.find('meta',property='og:video:secure_url')
		if meta is None:
			meta = soup.find('meta',property='og:video:url')
			if meta is None:
				continue
			return meta.get('content')
		return meta.get('content')
	return None

@socketio.on('make_server')
@login_required
def make_server(data=None,u=None):
	if data is None:
		return '',400
	
	db = open_db()
	
	# Create new server
	server = Server(
			name=data['name'],
			user_id=u.id)
	db.add(server)
	db.commit()
	db.refresh(server)
	
	# Join person to new server
	serverjoin = ServerJoin(
			user_id=u.id,
			server_id=server.id)
	db.add(serverjoin)
	db.commit()
	
	data = {
		'server_id': server.id
	}
	emit('switch_server',data)
	
	data = {
		'server_uuid': server.uuid,
		'server_name': server.name
	}
	emit('serverinfo_of',data)
	
	db.close()

@socketio.on('join_server')
@login_required
def server_join(data=None,u=None):
	db = open_db()
	
	# Join person to the server
	server = db.query(Server).filter_by(uuid=data['uuid']).first()
	if server is None:
		return '',404
	
	# Check not already join
	serverjoin = db.query(ServerJoin).filter_by(user_id=u.id,server_id=server.id).first()
	if serverjoin is not None:
		return '',400
	
	serverjoin = ServerJoin(
			user_id=u.id,
			server_id=server.id)
	db.add(serverjoin)
	db.commit()
	
	data = {
		'server_uuid': server.uuid,
		'server_name': server.name
	}
	emit('serverinfo_of',data)
	
	db.close()

@socketio.on('make_channel')
@login_required
def make_channel(data=None,u=None):
	if data is None:
		return '',400
	
	if data['server_id'] == 0:
		return '',400
	
	db = open_db()
	
	# Create new channel
	channel = Channel(
			name=data['name'],
			server_id=data['server_id'])
	db.add(channel)
	db.commit()
	db.refresh(channel)
	
	# Join person to channel
	data = {
		'channel_id': channel.id
	}
	emit('switch_channel',data)
	
	db.close()

@socketio.on('serverinfo_of')
@login_required
def serverinfo_of(data=None,u=None):
	if data is None:
		return '',400
	
	db = open_db()
	server = db.query(Server).filter_by(id=data['server_id']).first()
	data = {
		'server_uuid': server.uuid,
		'server_name': server.name
	}
	emit('serverinfo_of',data)
	db.close()

@socketio.on('channels_of')
@login_required
def channels_of(data=None,u=None):
	if data is None:
		return '',400
	
	db = open_db()
	channels = db.query(Channel).filter_by(server_id=data['server_id']).all()
	data = {
		'channels': [x.json for x in channels]
	}
	emit('channels_of',data)
	db.close()

@socketio.on('messages_of')
@login_required
def messages_of(data=None,u=None):
	if data is None:
		return '',400
	
	db = open_db()
	
	# Messages in channel
	messages = db.query(Message).filter_by(channel_id=data['channel_id']).options(joinedload('*')).order_by(asc(Message.id)).all()
	messages = messages[-50:]
	
	all_data = []
	
	for m in messages:
		data = {
			'time_utc': m.creation_date,
			'username': u.username,
			'uid': u.id,
			'body': m.body_html,
			'msg_id': m.id,
			'channel_id': m.channel_id
		}
		all_data.append(data)
	
	# Send message list
	emit('messages_of',all_data)
	
	db.close()

@socketio.on('disconnect')
def disconnect():
	print('disconnected')

print('Chat module ... ok')