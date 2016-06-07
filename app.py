#!/usr/bin/env python3
# _*_codeding:ctf-8 

__author__='Jason Zh Yan'
'main application and entry'
import jinja2
import logging;logging.basicConfig(level=logging.INFO)
import webtool
from webtool import RequestHandler,get,post
import asyncio,os,json,time
import datetime
from datetime import datetime
import orm
from aiohttp import web
from config import configs
from models import User,Blog,Comment
import hashlib

_COOKIE_KEY=configs.get('session').get('secret')
COOKIE_NAME=configs.get('COOKIE_NAME')

def init_jinja2(app,**kw):  #set jinja2 envirment for app ( in app['__templating__'] attribute )
    logging.info('init jinja2...')
    options=dict(           #set attribute
        autoescape=kw.get('autoescape',True),
        block_start_string=kw.get('block_start_string','{%'),
        block_end_string=kw.get('block_end_string','%}'),
        variable_start_string=kw.get('variable_start_string','{{'),
        variable_end_string=kw.get('variable_end_string','}}'),
        auto_reload=kw.get('auto_reload',True)
    )
    path=kw.get('path',None) #set path
    if path is None:
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
    logging.info('set jinja2 template path: %s'% path)
    env=jinja2.Environment(loader=jinja2.FileSystemLoader(path),**options)
    filters=kw.get('filters',None)
    if filters is not None:
        for name,f in filters.items():#if filters not empty,set envirment as filters'setting
            env.filters[name]=f
    app['__templating__']=env #恐怕关键在这里，应该是这个意思：设定app的模板语言为jinja2
    
#get user from cookie
@asyncio.coroutine
def cookie2user(cookie_str):
    '''
    check cookie and parse cookie , load user if cookie is valid
    '''
    if not cookie_str:
        return None
    try:
        L=cookie_str.split('-')
        if len(L)!=3:
            return None
        uid,expires,sha1=L
        if int(expires) < time.time():
            return None
        user = yield from User.find(uid)
        if user is None:
            return None
            
        s= '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1!=hashlib.sha1(s.encode('utf-8') ).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd='******'
        return user
    except Exception as e:
        logging.exception(e)
        return None
        
@asyncio.coroutine
def auth_factory(app,handler):
    @asyncio.coroutine
    def auth(request):
        logging.info('check user: %s %s' % (request.method,request.path) )
        request.__user__=None
        cookie_str=request.cookies.get(COOKIE_NAME)
        if cookie_str:
            user = yield from cookie2user(cookie_str)
            if user:
                logging.info('set user %s' % (user.email) )
                request.__user__=user
            if request.path.startswith('/manage/') and (request.__user__ is None or not request.__user__.admin):
                return web.HTTPFound('/login')
        return (yield from handler(request)) 
    return auth
        
        
    
@asyncio.coroutine#be prepared for middleware  
def logger_factory(app, handler):#app no use?
    @asyncio.coroutine
    def logger(request):
        # log record:
        logging.info('Request: %s %s' % (request.method, request.path))
        
        return (yield from handler(request))
    return logger
'''
@asyncio.coroutine
def logger_factory(app, handler):
    @asyncio.coroutine
    def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        # yield from asyncio.sleep(0.3)
        return (yield from handler(request))
    return logger
'''    
@asyncio.coroutine
def data_factorty(app,handler):#when 'post' find proper data for request
    @asyncio.coroutine
    def parse_data(request):
        if request.method=='POST':
            if request.content_type.startswith('application/json'):
                request.__data__=yield from request.json() 
                logging.info('request json:%s'%str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__=yield from request.post()
                logging.info('request from:%s' %str(request.__data__))
            return (yield from handler(request))
                
    
@asyncio.coroutine #be prepared for middleware
def response_factory(app,handler):#when 'get' ,find correct 
    @asyncio.coroutine
    def response(request):
        logging.info('response_factory now')
        #result:
        r=yield from handler(request)
        if isinstance(r,web.StreamResponse):
            return r
        if isinstance(r,bytes):
            resp=web.Response(body=r)
            resp.content_type='application/octet-stream'
            return resp
        if isinstance(r,str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp=web.Respense(body=r.encode('utf-8'))
            resp.content_type='text/html;charset=utf-8'
            return resp
        if isinstance(r,dict):
            template=r.get('__template__')
            if template is None:
                resp=web.Response(body=json.dumps(r,ensure_ascii=False, indent=4, default=lambda o:o.__dict__).encode('utf-8'))
                resp.content_type='application/json;charset=utf-8'
                return resp
            else:
                r.update({'__user__': request.__user__})
                resp=web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type='text/html;charset=utf-8'
                return resp
        if isinstance(r,int) and r>=100 and r<600:
            return web.Response(r)
        if isinstance(r,tuple) and len(r)==2:
            t,m=r
            if isinstance(t,int) and t>=100 and t<600:
                return web.Response(t,str(m))
        #default
        resp=web.Response(body=str(r).encode('utf-8'))
        resp.content_type='text/plain;charset=utf-8'
        return resp
    return response #why use this kind of double construction.for seperate the function's forming and using?
            
def datetime_filter(t):#input time now minus that,and output words
    delta=int(time.time() - t)
    if delta<60:
        return u'1 min ago'  #why use unicode?
    if delta<3600:
        return u'%s minutes ago'%(delta//60)
    if delta<86400:
        return u'%s hours ago'%(delta//3600)
    if delta<604800:
        return u'%s days ago'%(delta//86400)
    dt=datetime.fromtimestamp(t)
    return u'%s年%s月%s日'%(dt.year,dt.month,dt.day)
    
    
@asyncio.coroutine
def init(loop):
    yield from orm.create_pool(loop=loop,**configs['db']) #reate pool connect db
    app=web.Application(loop=loop,middlewares=[logger_factory, auth_factory, response_factory])#create app  #两个middleware，相当与两个对handler（url处理函数）的装饰器。接收一个handler,返回一个装饰后的handler。
    init_jinja2(app,filters=dict(datetime=datetime_filter))#init jinja2 setting for app
    webtool.add_routes(app,'handlers') #add routes for app, 'handlers' is modual name 
    webtool.add_static(app)    #add static for app
    #创建web应用                                          
    srv=yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)   #新建服务器由执行者（分出来的协程？）监听'127.0.0.1:9000'端口
    logging.info('server started at http://127.0.0.1:9000...')
    return srv
    
loop=asyncio.get_event_loop()        #创建事件循环
loop.run_until_complete(init(loop))  #开始事件循环
loop.run_forever()                   #一直循环




        
