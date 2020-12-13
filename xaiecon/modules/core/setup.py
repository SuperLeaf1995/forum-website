#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 13:17:08 2020

@author: superleaf1995
"""

from distutils.core import setup
from Cython.Build import cythonize

setup(
	ext_modules = cythonize((
		'apiapp.py',
		'asset.py',
		'babel.py',
		'board.py',
		'cache.py',
		'comment.py',
		'fediverse.py',
		'gdpr.py',
		'hcaptcha.py',
		'help.py',
		'helpers.py',
		'legal.py',
		'limiter.py',
		'log.py',
		'markdown.py',
		'oauthapp.py',
		'post.py',
		'user.py',
		'wrappers.py',))
)