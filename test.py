#!/usr/bin/env python3
# _*_codeding:ctf-8 
#models.py
import orm
from models import User, Blog, Comment
import asyncio

@asyncio.coroutine
def test(loop):
    
    yield from orm.create_pool(loop=loop,user='root',password='password',db='first')
    u=User(name='3',email='31',passwd='311')
    yield from u.save()
    u=User(name='4',email='41',passwd='411')
    yield from u.save()
    us=yield from User.findAll('name','1')
    print(us)   
    print(type(us[0].getValue(us[0].__primary_key__)))
    num=yield from us[0].remove()
    print(num)

loop = asyncio.get_event_loop()
   
loop.run_until_complete(test(loop))
loop.close()

#for x in test(loop):
#    print('x=',x)
'''
def test(loop):
    
    yield from orm.create_pool(loop,user='www-data',password='www-data',db='first')
    
    #u=User(name='test',email='test@test.com',passwd='11111',image='nothing')
    
    #yield from u.save()

loop=asyncio.get_event_loop()    
loop.run_until_complete(test(loop))
loop.close()

#for x in test(loop):
#    print('x=',x)
    
#loop=asyncio.get_event_loop()
#yield from orm.create_pool(loop,user='www-data',password='www-data',database='firsttime')
'''
