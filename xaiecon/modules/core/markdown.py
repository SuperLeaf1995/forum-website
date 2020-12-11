#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from misaka import Markdown, HtmlRenderer
import re

renderer = HtmlRenderer()
_md = Markdown(renderer=renderer,extensions=(
	'fenced-code',
	'strikethrough',
	'wrap',
	'superscript',
	'underline',
	'tables',
	'math',
	'math-explicit',
	'no_html',
	'space_headers',
	'no_intra_emphasis',
	'no_indented_code',
	'highlight',
	'autolink',))

user_mention = re.compile(r'([u][\/]|[@])([a-zA-Z0-9#][^ ,.;:\n\r\t<>\/\'])*\w+')
board_mention = re.compile(r'([vbcsrp][\/]|[+!])([a-zA-Z0-9][^ ,.;:\n\r\t<>\/\'])*\w+')

def create_user_link(matchobj: object):
	text = matchobj.group(0)
	name = None
	try:
		name = re.split(r'([u][\/]|[@])',text)[2]
		
		# Special pings (rendering for now)
		if name == 'everyone':
			return f'<a href=\'#\'>{text}</a>'
		elif name == 'here':
			return f'<a href=\'#\'>{text}</a>'
		
		tag = name.split('#')
		if len(tag) > 1:
			name = tag[0] # name
			uid = tag[1] # and tag
			ret = f'<a href=\'/user/view/{uid}\'><img style=\'border-radius:12px;width:24px;height:24px;\' src=\'/user/thumb/{uid}\'>{text}</a>'
		else:
			ret = f'<a href=\'/u/{name}\'>{text}</a>'
	except IndexError:
		pass
	return ret

def create_board_link(matchobj: object):
	text = matchobj.group(0)
	name = None
	try:
		name = re.split(r'([vbcsrp][\/]|[!+])',text)[2]
		tag = name.split('#')
		if len(tag) > 1:
			name = tag[0] # name
			bid = tag[1] # and tag
			ret = f'<a href=\'/board/view/{bid}\'><img style=\'border-radius:12px;width:24px;height:24px;\' src=\'/board/thumb/{bid}\'>{text}</a>'
		else:
			ret = f'<a href=\'/b/{name}\'>{text}</a>'
	except IndexError:
		pass
	return ret

# TODO: Better method to create mentionables the current method SUCKS and is
# horrible; if a master python programmer saw this they will absolutely cringe
def md(target: str) -> str:
	text = _md(target)
	text = board_mention.sub(create_board_link,text)
	text = user_mention.sub(create_user_link,text)
	return text