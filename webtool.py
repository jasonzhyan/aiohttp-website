#!/usr/bin/env python3
# _*_codeding:ctf-8 

#webtool.py
__author__='Jason Zh Yan'
'define some tools'

#所谓的webtool，就是自定义的web框架

from urllib import parse
import asyncio,logging,inspect,os,functools
from aiohttp import web
import orm
from apis import APIError


'''
@asyncio.coroutine
def handle_url_xxx(request):
    pass
    url_parameter=request.match_info['key']
    query.parameter=parse_qs(request.query_string)#return dict
    text=render('template',data)
    return web.Response(text.encode(ctf-8))
'''
   
def get(path):# receive 1 parameter and add 2 arttributes.
#define decorator @get('/path')
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__method__='GET'
        wrapper.__route__=path
        return wrapper
    return decorator
        
def post(path):#define decorator @post('/path')
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):   
            return func(*args,**kw)
        wrapper.__method__='POST'
        wrapper.__route__=path
        return wrapper
    return decorator

def get_required_kw_args(fn): #fn is a router
    print(fn)
    args=[]
    params=inspect.signature(fn).parameters#get the required parameters
    for name,param in params.items():
        if param.kind==inspect.Parameter.KEYWORD_ONLY and param.default==inspect.Parameter.empty:
            args.append(name)
    return tuple(args)#return parameters whick have no default value,而且需要函数接收的是关键字参数，返回tuple，否则返回空tuple
         
        
def get_named_kw_args(fn):
    print(fn)
    args=[]
    params=inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind==inspect.Parameter.KEYWORD_ONLY:#命名关键字参数 #仅接受关键字参数
            args.append(name)
    return tuple(args)#return all required parameters
    
def has_named_kw_args(fn):
    print(fn)
    params=inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind==inspect.Parameter.KEYWORD_ONLY:#命名关键字参数
            return True
    return False
    
def has_var_kw_arg(fn):
    print(fn)
    params=inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind==inspect.Parameter.VAR_KEYWORD:#关键字参数
            return True
    return False    

def has_request_arg(fn):
    logging.info(fn)
    sig=inspect.signature(fn)
    params=sig.parameters
    found=False
    for name,param in params.items():
        if name=='request':# looking for 'request' param
            found=True
            continue
        #logging.info(inspect)
        if found and ( param.kind!=inspect.Parameter.VAR_POSITIONAL and param.kind!=inspect.Parameter.KEYWORD_ONLY and param.kind!=inspect.Parameter.VAR_KEYWORD ):
            raise ValueError('request paramter must be the last named parameter in function :%s%s'%(fn.__name__,str(sig)))
#not关键字参数，命名关键字参数，可变(位置？)参数，就不能在'request'之后出现
    return found

    
#class RequestHandler()
class RequestHandler(object):
    def __init__(self,app,fn):
        self._app=app
        self._func=fn
        self._has_request_arg=has_request_arg(fn)
        self._has_var_kw_arg=has_var_kw_arg(fn)
        self._has_named_kw_args=has_named_kw_args(fn)
        self._named_kw_args=get_named_kw_args(fn)
        self._required_kw_args=get_required_kw_args(fn)
        
    @asyncio.coroutine
    def __call__(self,request):
        kw=None
        logging.info('self._has_request_arg：'+str(self._has_request_arg) )
        print('self._has_var_kw_arg',self._has_var_kw_arg)
        print('self._has_named_kw_args',self._has_named_kw_args)
        print('self._named_kw_args',self._named_kw_args)
        print('self._required_kw_args',self._required_kw_args)
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            if request.method=='POST':
                if not request.content_type:# if type empty report error
                    return web.HTTPBadRequest('Missing content-type')
                ct=request.content_type.lower()
                if ct.startswith('application/json'):
                    params=yield from request.json()#what is request on earth 
                    if not isinstance(params,dict):
                        return web.HTTPbadRequest('JSON body must be object')#should return a dict!
                    kw=params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = yield from request.post()
                    kw=dict(**params)#build a dict
                else:#what situation?
                    return web.HTTPBadRequest('Unsupported Content-type:%s '% request.content_type)
            if request.method=='GET':
                qs=request.query_string#将被quote的字符串解码，即常规的url编码解码操作?那么request就是url请求?
                if qs:
                    kw=dict()
                    for k,v in parse.parse_qs(qs,True).items():#将字符串解释为dict(parse_sq将每个参数看做是一个数组，就算你只传了一个过来，也会被认为是数组，与java的request.getParametersMap类似)?
                        kw[k]=v[0]
                        
        if kw is None:
            kw=dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:#only has named keywords
                copy=dict()#make a copy for named keywords
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name]=kw[name]
                kw=copy
            #check named arg:
            for k,v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args: %s' % k)#same name warning
                kw[k]=v #add request.match_info to kw
        if self._has_request_arg:
            kw['request']=request
        #check required kw:
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest('Missing argument: %s' % name ) #check missing required 
                    
        logging.info('call with args:%s'% str(kw))
        try:
            r=yield from self._func(**kw)
            return r   #use fn to deal with changed request
        except APIError as e:        
            return dict(error=e.error,data=e.data,message=e.message)
                
        
        
        r=yield from self._func(**kw)
        return r

def add_static(app):# get path and add static path to app
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/',path))
    
def add_route(app,fn):    
    method=getattr(fn,'__method__',None)
    path=getattr(fn,'__route__',None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.'% str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn=asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))    
    app.router.add_route(method,path,RequestHandler(app,fn))
    
def add_routes(app,module_name):
    n=module_name.rfind('.')
    if n==(-1):
        mod=__import__(module_name,globals(),locals())
    else:
        name=module_name[n+1:]
        mod=getattr(__import__(module_name[:n],globals(),locals()[name]),name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn=getattr(mod,attr)
        if callable(fn):
            method=getattr(fn,'__method__',None)#fn is a function return web.Response object
            path=getattr(fn,'__route__',None)
            if method and path:
                add_route(app,fn)
                
                

                
    
    
    
    
    
         
