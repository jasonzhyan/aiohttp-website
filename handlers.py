#!/usr/bin/env python3
# _*_codeding:ctf-8 

#handlers.py
from apis import APIError,APIValueError,APIResourceNotFoundError,Page

from models import User,Blog,Comment
from datetime import datetime
from aiohttp import web

__author__='Jason Zh Yan'
' url handlers'
import logging;logging.basicConfig(level=logging.INFO)
from webtool import get,post
import asyncio
import webtool
import re
import json
from webtool import RequestHandler
from models import next_id
import time
import hashlib
from config import configs

_COOKIE_KEY=configs.get('session').get('secret') #is this what they call 'salt'?
COOKIE_NAME=configs.get('COOKIE_NAME')

#compute cookie 
def user2cookie(user,max_age):
    expires=str(int(time.time()+max_age))
    s='%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L=[user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)
    
@post('/api/authenticate')
def authenticate(*,email,passwd):
    
    if not email:
        raise APIValueError('email','Invalid email')
    if not passwd:
        raise APIValueError('password','Invalid password.')
    users = yield from User.findAll('email=?',[email])
    if len( users ) < 1:
        raise APIValueError('email','email is not exist')
    user=users[0]
    #check password
    
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(':'.encode('utf-8'))
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest() :
        raise APIValueError('passwd','Invalid passwd')
        
    password_sha1='%s:%s' % (user.id,passwd)
    print('user.passwd = '+user.passwd)
    print('hashlib.sha1(password_sha1.encode(\'utf-8\')).hexdigest() = '+hashlib.sha1(password_sha1.encode('utf-8')).hexdigest() )
    
    if user.passwd != hashlib.sha1(password_sha1.encode('utf-8')).hexdigest() :
        raise APIValueError('passwd','Invalid passwd')
     
    #authencate OK, set and return with cookie
    r=web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie( user, 86400), max_age=86400, httponly=True)
    user.passwd='******'
    r.content_type='application/json'
    r.body=json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

def get_page_index(page):
    return 1
    
@get('/api/blogs')
def get_api_blogs(*,page='1'):
    page_index=get_page_index(page)
    num= yield from Blog.findNumber('count(id)')
    p=Page(num, page_index)
    if num==0:
        return dict(page=p, blogs=() )
    blogs= yield from Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit) )
    return dict(page=p, blogs=blogs)
    
@get('/manage/blogs')
def manage_blogs(*,page='1'):
    return {
    '__template__':'manage_blogs.html',
    'page_index':get_page_index(page)
    }

@get('/')
def index(request):
    r={'__template__':'blogs.html'}
    about_blogs= yield from get_api_blogs()
    r.update( about_blogs )
    return r

    
@get('/test_index')
def test_index(request):
    summary='fsfsdf'
    blogs=[
      Blog(id='1',name='Test Blog',summary=summary,create_at=datetime.now().timestamp()-120),
      Blog(id='2',name='Hello',summary=summary+'1',create_at=datetime.now().timestamp()-600),
      Blog(id='3',name='Something',summary=summary,create_at=datetime.now().timestamp()-3600)
    ]
    return {
        '__template__':'blogs.html',
        'blogs':blogs,
        'user':request.__user__        
    }

'''
@get('/signin.html')
def signin(request):
    return{'__template__':'signin.html'}
'''
    
@get('/vue_test.html')
def vue_test(request):
    return {
        '__template__':'vue_test.html',
        'message':'Hello'    
    }

@get('/api/users')
def api_get_users(*,page='1'):

  #  page_index=get_page_index(page)#what's this?
  #  num=yield from User.findNumber('count(id)')#what's findNumber?                
  #  p=Page(num,page_index)#what's this?

    num,p=page,page   
    if num==0:
        return dict(page=p,users=())
    users=yield from User.findAll(orderBy='created_at desc') # , limit=(p.offset,p.limit)    
    for u in users:
        u.passwd='******'
    return dict(page=p,users=users)
    
_RE_EMAIL=re.compile(r'^[0-9a-z\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\_\-]+){1,4}$')
_RE_PASSWD_SHA1=re.compile(r'^[0-9a-f]{40}$')
    
@post('/api/users')
def api_post_users(*,email,name,passwd): 
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_PASSWD_SHA1.match(passwd):
        raise APIValueError('password')
    users=yield from User.findAll('email=?',[email])#this ,I have implemented this?
    if len(users)>0:
        raise APIError('register:failed','email','same email was already used')
    uid=next_id()
    password_sha1='%s:%s' % (uid,passwd)
    user=User(id=uid,name=name.strip(),email=email,passwd=hashlib.sha1(password_sha1.encode('utf-8')).hexdigest() , image='12345')
    yield from user.save()
    
    #make session cookies
    r=web.Response()
    #r.set_cookie(COOKIE_NAME,user2cookie(user,86400),max_age=86400,httponly=True)
    user.passwd='******'
    r.content_type='application/json'
    r.body=json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r
    
@get('/test')
def test(request):
    users = yield from User.findAll()
    return {
        '__template__': 'test.html',
        'users': users
    }
    
@get('/show_blogs')  
def test_blogs(request):
    blogs = yield from Blog.findAll()
    return {
        '__template__': 'show_blogs_list.html',
        'blogs': blogs
    }
    
@get('/register.html')
def register(request):
    return {
        '__template__':'register.html',
        } 

@get('/register_liao.html')
def register_liao(request):
    return {
        '__template__':'register_liao.html',
        }
        
@get('/register_self.html')
def register_self(request):
    return {
        '__template__':'register_self.html',
        }
        
def check_admin(request):
    return request.__user__.admin    
    
    
@post('/api/edit_blog')
def edit_blog(request, *, name, summary, content, **kw):
    print( check_admin(request))
    if(not name or not name.strip()):
        raise APIValueError('name','No empty name permited')
    if not summary or not summary.strip():
        raise APIValueError('summary','empty summary')
    if not content or not content.strip():
        content=' '
    if request.__user__:
        blog=Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, name=name.strip(), summary=summary.strip() , content=content.strip() )
        if kw['bid']:
            bid=kw['bid']
            print('bid='+str(bid) )
            blog.id=bid
            print(', blog.id='+str(blog.id))
            created_at=kw['created_at']
            print('created_at='+str(created_at))
            blog.created_at=created_at
            print(', blog.created_at='+str(created_at))
        yield from blog.save()
        return blog#################################################################
    else:
        raise APIError('sign in error','unsign in','please signin')
        return None

@get('/manage/users')
def manage_users(request):
    about_users = yield from api_get_users()
    d= {'__template__':'manage_users.html'}
    d.update(about_users)    
    json_users=json.dumps(d['users'], ensure_ascii=False)#create a jsonfy object here
    d.update(dict(json_users=json_users) )
    print('json_users is: ', json_users)
    return d
    #dict(__template__='manage_users.html', page=p, users=users, json_users=json_users)


    
@get("/manage/blogs")
def manage_blogs(request):
    return {
        '__template__':'manage_blogs_test.html'
        }

@get('/manage/blogs_test')
def manage_blogs_test(request):
    d={'__template__':'manage_blogs_test.html'}
    about_blogs= yield from get_api_blogs()
    d.update( about_blogs )
    toTime= dict(toTime= datetime.fromtimestamp)
    d.update(toTime)
    return d #return dict(__template__='manage_blogs_test.html', page=p, blogs=blogs, toTime= datetime.fromtimestamp)
        
@get("/manage/new_blog")
def edit_new_blogs(request):
    return {
        '__template__':'manage_blog_edit.html',
        'id': '',
        'action':'/api/edit_blog'        
        }

@get('/manage/blog/{id}')
def manage_blog_edit(id, request):
    return {
        '__template__':'manage_blog_edit.html',
        'id':id,
        'action':'/api/edit_blog'        
    }

@get('/api/comments/by_blog/{blog_id}')
def get_api_comments_by_blog_id(blog_id):
    comments=yield from Comment.findAll('`blog_id` = ?', [blog_id], orderBy='created_at')
    return comments

    
@get('/blog/{id}')
def single_blog_page(id):
    blog= yield from Blog.find(id)
    if blog:
        comments= yield from get_api_comments_by_blog_id(blog.id)               
        return {
            '__template__':'single_blog.html',
            'blog':blog,
            'comments':comments
        } 
    else:
        raise APIValueError('blog','wrong blog id')
        return None

@get('/api/blog/{id}')
def get_api_blog(id):
    blog=yield from Blog.find(id)    
    if blog:
        return blog
    else:
        raise APIValueError('id','wrong id')
        return None

@get('/login')
def login(request):
    return {
        '__template__':'/signin.html',        
        'action':'/api/authenticate'
    }


@post('/api/comment')
def post_api_comment(*, new_comment, blog_id, user_id, user_name, user_image):
    
    comment= Comment(content=new_comment, blog_id=blog_id, user_id=user_id, user_name=user_name, user_image=user_image)
    yield from comment.save()
    r=web.Response()
    r.content_type='application/json'
    r.body=json.dumps(comment, ensure_ascii=False).encode('utf-8')
    return r

@get('/manage/comments')
def get_manage_comments(request):
    return{
        '__template__':'manage_comments.html',
    }

@get('/api/comments')
def get_api_comments(*,page=1):
    comments= yield from Comment.findAll( orderBy='created_at')
    print('###################################################')
    print(comments)
    print('###################################################')
    return dict(comments=comments)
         
