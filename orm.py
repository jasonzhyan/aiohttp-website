#!/usr/bin/env python3
# _*_codeding:ctf-8 

#orm.py

import aiomysql
import asyncio
import logging;logging.basicConfig(level=logging.INFO)

@asyncio.coroutine
def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )

'''
@asyncio.coroutine
def create_pool(loop,**kw):                     #create a connection pool
    logging.info('create database connection pool...')
    global __pool                               # global variable means there's only one __pool and all the functions can use the same pool
    __pool=yield from aiomysql.create_pool(     # create pool (give a value to a global variable "__pool" which is a instance)
                                                # and I think it is equals mysql.connector.connec(user=.....)   
        host=kw.get('host','localhost'),        # 为pool的参数赋值,kw为可视为（组装为）dict的关键字参数，这说明函数create_pool可接受关键字参数，或者命名关键字参数
        port=kw.get('port',3306),               # it means kw have a function".get" 3306是'port'不存在时的默认值
        user=kw['user'],
        password=kw['password'],                 # it means kw is a dictionary
        db=kw['db'],
        charset=kw.get('charset','utf8'),       #除了数据库名，用户名，密码，其他都有默认值
        autocommit=kw.get('aotocommit',True),
        maxsize=kw.get('maxsize',10),
        minsize=kw.get('minsize',1),
        loop=loop
    )
'''    
@asyncio.coroutine
def select(sql,args,size=None):           #create a "select" function with whom we can do select words
    logging.info(sql)  #what is log？
    global __pool                           #声明全局变量？
    with (yield from __pool) as conn:    #create a connection with connction pool "__pool"
        cursor=yield from conn.cursor(aiomysql.DictCursor)
        yield from cursor.execute(sql.replace('?','%s'),args or ()) #'?' is a SQL words and replace as '%s'
                                                       # But args is for what? list?
        if size:
            rs=yield from cursor.fetchmany(size)         #use different words recieve word from mysql base on if there is a value of "size"
        else:
            rs=yield from cursor.fetchall()                 #返回值是一组dict？
        yield from cursor.close()
        logging.info('rows returned: %s' % len(rs))          #calculate the elements in rs,and this is the row's number
        return rs          # Return a list in which there is the execute result
        
@asyncio.coroutine
def execute(sql,args):   #this function is used for the words"delete","update","modify","insert"
    logging.info(sql)
    global __pool #is there any affection with this row? and can I add this?
    with (yield from __pool) as conn:
        try:                        #为什么这里有try而select没有。这里容易出错?
            cursor=yield from conn.cursor()
            yield from cursor.execute(sql.replace('?','%s'),args)
            affected = cursor.rowcount
            yield from cursor.close()
        except BaseException as e:  #基础错误？框架异常基类
            raise
        return affected
 	           

def create_args_string(times):
    if times==0:
        return ''
    question_mark='?'
    for i in range(times-1):
        question_mark+=',?'
    return question_mark

class ModelMetaclass(type):

    def __new__(cls,name,bases,attrs):  #其实就是对attrs进行了预处理之后，调用基类的__new__和修改后的atrrs生成新类。并不实质性的涉及class构造过程

        if name == 'Model':               #规定了生成Model的子类的流程，因此先排除Model，其实这里的Model相当于Java的抽象类
            return type.__new__(cls,name,bases,attrs)          #cls相当于self，name是String，bases是tuple表示基类集合，attrs是dict表示属性集合（包括变量和和函数都是属性）
            
        tableName=attrs.get('__table__',None) or name
        logging.info('found model:%s(table:%s)' % (name,tableName))
        
        mappings=dict()
        fields=[]
        primaryKey=None
        for k,v in attrs.items():                 #寻找属性dict中属于Field的（列），加入dict：mappings中
            if isinstance(v,Field):
                logging.info('found mapping %s==>%s' % (k,v))
                mappings[k]=v
                if v.primary_key:
                
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field:%s' % k)#防止主key重复，那么 联合主key怎么办？
                    primaryKey=k                   #把primary key赋值给变量primaryKey    
                else:
                    fields.append(k)               #把非primarry key的列加入list：fields里
        if not primaryKey:
            raise RuntimeError('Primary key not found')                         #防止主key缺失
        for k in mappings.keys():              #在属性dictionary中删除已加入dict：mappings的那些
            attrs.pop(k)
        escaped_fields=list(map(lambda f: '`%s`' % f,fields))   #为什么要加``，``在sql里代表什么？
        attrs['__mappings__']=mappings                          #原来Model里的__mapping__属性 是在这里实现的
        attrs['__table__']=tableName                    
        attrs['__primary_key__']=primaryKey                    #把这四个变量加到attrs里（属性dict）
        attrs['__fields__']=fields
            
        #再创建四个sql语句也作为属性值记录，因为基类Model无法接触子类User的属性，所以语句的创建放在MetaClass里。
        attrs['__select__']='select `%s`,%s  from `%s` ' %(primaryKey,','.join(escaped_fields),tableName)#为什么每个列名、表名都要加上``???#防止与命令或内部变量重名
        attrs['__insert__']='insert into `%s` (%s,`%s`) values (%s)'%(tableName,','.join(escaped_fields),primaryKey,create_args_string(len(escaped_fields)+1))#create_args_string这个函数在哪里
        #attrs['__insert__']='insert into `%s`(%s,`%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__']='update `%s` set %s where `%s`=?' % (tableName,','.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f),fields)),primaryKey)
        attrs['__delete__']='delete from `%s` where `%s`=?' % (tableName,primaryKey)
        return type.__new__(cls,name,bases,attrs)
        #当建立Medol的子类subclass的时候，会使用以上metaclass，将表信息的列信息存储到自身的类属性中

class Model(dict,metaclass=ModelMetaclass):#实现特殊方法的dict，1.特殊的__getattr__和__setattr__  2.可以去读__mapping__[key]里的default信息 3.但是__maping__是什么

    def __init__(self,**kw):
        super(Model,self).__init__(**kw) #调用父类  等于 dict.__init__(self,**kw)   ，这里有点怪？？为什么既有Medel又有self？Model代表类，self代表instance？ dict可没有__mapping__
        
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" %key)#r 是什么意思，哦我想起来了，转义符
            
    def __setattr__(self,key,value): #these 2 function means to use the elements from dict just like use a attribute.
        self[key]=value
        
    def getValue(self,key):
        return getattr(self,key,None) #1. not defined? Maybe it is equal to __getattr__+default value. 2. why None，because this is a default value.
        
    def getValueOrDefault(self,key):
        value=getattr(self,key,None)
        if value is None:                   #去读数据库里的table上的列的信息。如果有default值就读出来并且赋值记录。No!!!不是读数据库里的，而是类属性里的
            field=self.__mappings__[key]    #but 这个mapping是什么记录映射关系的dict？类似传入pool里的那一大堆命名关键字，然后被组装为dictionary-mapping？              
            if field.default is not None:
                value=field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s:%s' %(key,str(value)))
                setattr(self,key,value)
        return value
        
    @classmethod #添加类方法 class方法  Is only for subclass?
    @asyncio.coroutine  #使用时直接操作class来操作对应table，还真是把类当作对象使了
    def find(cls,pk): #class,primarykey
        'find object by primary key.'            
        #这里不对啊，Model里没有定义__select__也没有定义__primary_key__，都是在metaclass里添加的，class函数就可以调用？不会出错？
        #动态语言真神奇，不调用就不存在一样。这样的话一样可以在Model里调用属性生成命令，只不过没法像metaClass里一样生成新属性      
        rs=yield from select ('%s where `%s`=?' % (cls.__select__, cls.__primary_key__),[pk],1)#row select?，调用类属性
        if len(rs)==0:
            return None
        return cls(**rs[0])  #生成一个类的实例作为返回值，代表找到table里的一行数据，还好本来sql里的一行数据就表示一个对象。
       
    @classmethod
    @asyncio.coroutine  
    def findAll(cls,where='',args=None,*,orderBy='',**kw):        #unfinished method and need more test!!!
        'find object by k0=v0.' 
        sql=list()
        sql.append(cls.__select__)
        if where:
            sql.append(' where '+where)    
        if orderBy:
            sql.append(' order by '+ orderBy)
        
        rs=yield from select('%s ' %(' '.join(sql) ),args)
        resultList=[]
        for i in rs:
            resultList.append(cls(**i))
            
        if kw.get('limit'):
            offset, limit= kw.get('limit')
            return resultList[offset:offset+limit]
        return resultList
        
    @asyncio.coroutine
    def findNumber(sql):
        return 1
    
    @asyncio.coroutine
    def remove(self):
        args=self.getValue(self.__primary_key__)
        rows=yield from execute(self.__delete__,[args])#'delete from `users` where `id`=?','001448009226486361e7bcaaa634173b480cf9a680b543e000'
        if rows!=1:
            logging.warn('failed to delete record:affected rows is:%s' % rows)
        return rows
        
    #ORM之后，类就是表，实例就是sql表里的一行数据，也就相当于sql表里的一个对象。
    #想要对表操作就直接处理相应的class，想要对一行数据操作时才生成一个实例进行
    #操作，无论删除添加。批量处理数据，估计应该批量生成实例。
    
    @asyncio.coroutine #添加实例方法 instance
    def save(self):
        args=list(map(self.getValueOrDefault,self.__fields__))
        primary_key=self.getValueOrDefault(self.__primary_key__)
        args.append(primary_key)#把主键 的值又加了一遍，不会重复吗？ answer：no，因为fields里不含有主键
        ins= yield from self.find(primary_key )
        if ins:
            rows=yield from execute(self.__update__, args)
        else:
            rows=yield from execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record:affected rows:%s' % rows)
        return rows

        
class Field(object):                                              #Model是table，那Field就是 Table里的 column

    def __init__(self,name,column_type,primary_key,default):
        self.name=name
        self.column_type=column_type
        self.primary_key=primary_key
        self.default=default
        
    def __str__(self):                                          #打印时打印 类名，列类型，列名，
        return '<%s,%s,%s>' %(self.__class__.__name__,self.column_type,self.name)
        
class StringField(Field): #列类型column_type为字符型'varchar(100)'的Field

    def __init__(self,name=None,primary_key =False,default=None,ddl='varchar(100)'):
    #                           primary_key=True,
        super().__init__(name,ddl,primary_key,default)
        
class IngeterField(Field):#列类型column type为数值型int(20)的Field
    
    def __init__(self,name=None,primary_key=False,default=None,ddl='int(20)'):
        super().__init__(self,ddl,primary_key,default)
        
class BooleanField(Field):
    def __init__(self,name=None,primary_key=False,default=False,ddl='bool'):
        super().__init__(name,ddl,primary_key,default)

class FloatField(Field):
    def __init__(self,name=None,primary_key=False,default=None,ddl='real'):
        super().__init__(name,ddl,primary_key,default)

class TextField(Field):    
    def __init__ (self,name=None,primary_key=False,default=None,ddl='mediumtext'):
        super().__init__(name,ddl,primary_key,default)
        
    
    
