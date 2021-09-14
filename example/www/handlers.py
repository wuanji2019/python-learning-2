#!/usr/bin/python
# -*- coding: utf-8 -*-


' url handlers '

from coroweb import get, post

from models import User, Comment, Blog

@get('/')
async def index(request):
  users = await User.findAll()
  return {
      '__template__': 'test.html',
      'users': users
  }
