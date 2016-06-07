#!/usr/bin/env python3
# _*_codeding:ctf-8 

#handlers.py

from models import User,Blog,Comment

__author__='Jason Zh Yan'
' url handlers'
from webtool import get,post
import asyncio
import webtool
from webtool import RequestHandler

@get('/')
def index(request):
    users=yield from User.findAll('image','about:blank')
    return {
        '__template__':'test.html',
        'users':users
    }

                
    
    
    
    
    
         
