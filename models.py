#!/usr/bin/env python3
# _*_codeding:ctf-8 
#models.py


import aiomysql
import asyncio
import logging;logging.basicConfig(level=logging.INFO)
from orm import Model,StringField,IngeterField,BooleanField,FloatField,TextField
#from orm import 
import time
import uuid

def next_id():
    return '%015d%s000'%(int(time.time()*1000),uuid.uuid4().hex)#uuid 是python中生成唯一id、uuid4()——基于随机数由伪随机数得到，有一定的重复概率，该概率可以计算出来。

                

class User(Model):
    __table__='users'
    # 
    id=StringField(primary_key = True, default=next_id, ddl='varchar(50)')    #当不按照顺序使用默认参数时，需要写上参数名，这就是一个例子
    email=StringField(ddl='varchar(50)')        #这些属性将最终保存在作为dict的属性__mapping__中，只是起到一个在类中保存sql table信息的作用，无实质性的作用                  
    passwd=StringField(ddl='varchar(50)')       #也不会影响实例，但是有两个例外，一个是primary为True的属性把name保存在类属性__primary_key__中，以及生成的sql语句中
    admin=BooleanField()                        #另一个是default值会用到，因为getValueOrDefault()方法会调用__mapping__里的对应属性的default值。
    name=StringField(ddl='varchar(50)')         #其实还有一个，就是Feild对象的name属性，如果跟你使用的key不一样的话，会被调出来替换key生成sql语句。
    image=StringField(default='about:blank',ddl='varchar(500)')
    created_at=FloatField(default=time.time)
    
class Blog(Model):
    __table__='blogs'
    
    id=StringField(primary_key=True, default=next_id, ddl='varchar(50)')#允许匿名用户发表blog？还是无意义的id值？
    #so many StringFeild's default value is varchar(50),why don't set class StringFeild ddl=varchar(50)?
    user_id=StringField(ddl='varchar(50)')
    user_name=StringField(ddl='varchar(50)')
    user_image=StringField(ddl='varchar(500)')
    name=StringField(ddl='varchar(50)')
    summary=StringField(ddl='varchar(50)')
    content=TextField()
    created_at=FloatField(default=time.time)
    key_words=StringField(default='', ddl='varchar(200)')
    
class Comment(Model):
    __table__='comments'
    
    id=StringField(primary_key=True,default=next_id,ddl='varchar(50)')#这就是说的找无意义的值作primary Key???
    blog_id=StringField(ddl='varchar(50)')
    user_id=StringField(ddl='varchar(50)')
    user_name=StringField(ddl='varchar(50)')
    user_image=StringField(ddl='varchar(500)')
    content=TextField()
    created_at=FloatField(default=time.time)
    
