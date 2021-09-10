#!/usr/bin/python
# -*- coding: utf-8 -*-


import logging, aiomysql

# 创建基本日志函数，变量 sql 出现了很多次，这里我们还不知道它的作用
def log(sql, args=()):
  logging.info('SQL: %s' % sql)

# 连接池函数
async def create_pool(loop, **kw):
  logging.info('create database connection pool...')
  # 声明 __pool 为全局变量
  global __pool
  __pool = await aiomysql.create_pool(
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

# select语句
async def select(sql, args, size=None):
  log(sql, args)
  global __pool
  async with __pool.get() as conn:
    async with conn.cursor(aiomysql.DictCursor) as cur:
      await cur.execute(sql.replace('?', '%s'), args or ())
      if size:
        rs = await cur.fetchmany(size)
      else:
        rs = await cur.fetchall()
    await cur.close()
    logging.info('rows returned: %s' % len(rs))
    return rs
  
# Insert, Update, Delete 语句 通用
async def execute(sql, args,autocommit=True):
  log(sql)
  print(args)
  global __pool
  with (await __pool) as conn:
    try:
      cur = await conn.cursor()
      await cur.execute(sql.replace('?', '%s'), args)
      # rowcount 获取行数，应该表示的是该函数影响的行数
      affected = cur.rowcount
      await cur.close()
    except BaseException as _:
    # 源码 except BaseException as e: 反正不用这个 e ，改掉就不报错
      # 将错误抛出，BaseEXception 是异常不用管
      raise
    # 返回行数
    return affected
  # async with __pool.get() as conn:
  #   if not autocommit:
  #     await conn.begin()
  #   try:
  #     async with conn.cursor(aiomysql.DictCursor) as cur:
  #       await cur.execute(sql.replace('?', '%s'), args)
  #       # rowcount 获取行数，应该表示的是该函数影响的行数
  #       affected = cur.rowcount
  #   except BaseException as e:
  #     if not autocommit:
  #         await conn.rollback()
  #     raise
  #   return affected

def create_args_string(num):
    L = []
    for _ in range(num):
    # 源码是 for n in range(num):  我看着反正 n 也不会用上，改成这个就不报错了
        L.append('?')
    return ', '.join(L)

class Field(object):

  def __init__(self, name, column_type, primary_key, default):
    self.name = name  
    self.column_type = column_type
    self.primary_key = primary_key
    self.default = default

  def __str__(self):
    return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)

class StringField(Field):

  def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
    super().__init__(name, ddl, primary_key, default)

class BooleanField(Field): 
  
  def __init__(self, name=None, default=False):
    super().__init__(name, 'boolean', False, default)

class IntegerField(Field):

  def __init__(self, name=None, primary_key=False, default=0):
    super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field):

  def __init__(self, name=None, primary_key=False, default=0.0):
    super().__init__(name, 'real', primary_key, default)

class TextField(Field):

  def __init__(self, name=None, default=None):
    super().__init__(name, 'text', False, default)

class ModelMetaclass(type):
    # __new__()方法接收到的参数依次是：
    # cls：当前准备创建的类的对象 class
    # name：类的名字 str
    # bases：类继承的父类集合 Tuple
    # attrs：类的方法集合
    def __new__(cls, name, bases, attrs):
        # 排除 Model 类本身，返回它自己
        if name=='Model':
            return type.__new__(cls, name, bases, attrs)
        # 获取 table 名称
        tableName = attrs.get('__table__', None) or name
        # 日志：找到名为 name 的 model
        logging.info('found model: %s (table: %s)' % (name, tableName))
        # 获取 所有的 Field 和主键名
        mappings = dict()
        fields = []
        primaryKey = None
        # attrs.items 取决于 __new__ 传入的 attrs 参数
        for k,v in attrs.items():
            # isinstance 函数：如果 v 和 Field 类型相同则返回 True ，不相同则 False
            if isinstance(v, Field):
                logging.info(' found mapping: %s ==> %s' % (k,v))
                mappings[k] = v
                # 这里的 v.primary_key 我理解为 ：只要 primary_key 为 True 则这个 field 为主键
                if v.primary_key:
                    # 找到主键，如果主键 primaryKey 有值时，返回一个错误
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    # 然后直接给主键赋值
                    primaryKey = k
                else:
                    # 没找到主键的话，直接在 fields 里加上 k
                    fields.append(k)
        if not primaryKey:
            # 如果主键为 None 就报错
            raise RuntimeError('Primary key not found.')
        for k in mappings.keys():
            # pop ：如果 key 存在于字典中则将其移除并返回其值，否则返回 default 
            attrs.pop(k)
        # 这个 lambda 看不懂呀
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings # 保存属性和列的映射关系
        attrs['__table__'] = tableName # table 名
        attrs['__primary_key__'] = primaryKey # 主键属性名
        attrs['__fields__'] = fields # 除主键外的属性名
        # 构造默认的 SELECT, INSERT, UPDAT E和 DELETE 语句
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):

  def __init__(self, **kw):
    super(Model,self).__init__(**kw)

  def __getattr__(self, key):
    try:
      return self[key]
    except KeyError:
      raise AttributeError(r"'Model' object has no attribute '%s'" % key)
  
  def __setattr__(self, key, value):
    self[key] = value

  def getValue(self, key):
    return getattr(self, key, None)

  def getValueOrDefault(self, key):
    value = getattr(self, key, None)
    if value is None:
      field = self.__mappings__[key]
      if field.default is not None:
        # 如果 field.default 不是 None ： 就把它赋值给 value
        value = field.default() if callable(field.default) else field.default
        logging.debug('using default value for %s: %s' % (key,str(value)))
        setattr(self, key, value)
    return value
  
  @classmethod
  async def findAll(cls, where=None, args=None, **kw):
    ' find objects by where clause. '
    sql = [cls.__select__]
    if where:
      sql.append('where')
      sql.append(where)
    if args is None:
      args = []
    orderBy = kw.get('orderBy', None)
    if orderBy:
      sql.append('order by')
      sql.append(orderBy)
    limit = kw.get('limit', None)
    if limit is not None:
      sql.append('limit')
      if isinstance(limit, int):
        sql.append('?')
        args.append(limit)
      elif isinstance(limit, tuple) and len(limit) == 2:
        sql.append('?, ?')
        args.extend(limit)
      else:
        raise ValueError('Invalid limit value: %s' % str(limit))
    rs = await select(' '.join(sql), args)
    return [cls(**r) for r in rs]

  @classmethod
  async def findNumber(cls, selectField, where=None, args=None):
    ## ' find number by select and where. '
    sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
    if where:
      sql.append('where')
      sql.append(where)
    rs = await select(' '.join(sql), args, 1)
    if len(rs) == 0:
      return None
    return rs[0]['_num_']

  
  @classmethod
  async def find(cls, pk):
    ## ' find object by primary key.'
    rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
    if len(rs) == 0:
      return None
    return cls(**rs[0])


  async def save(self):
    args = list(map(self.getValueOrDefault, self.__fields__))
    args.append(self.getValueOrDefault(self.__primary_key__))
    rows = await execute(self.__insert__, args)
    if rows != 1:
      logging.warn('failed to insert record: affected rows: %s' % rows)

  async def update(self):
    args = list(map(self.getValue, self.__fields__))
    args.append(self.getValue(self.__primary_key__))
    rows = await execute(self.__update__, args)
    if rows != 1:
      logging.warn('failed to update by primary key: affected rows: %s' % rows)

  async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to remove by primary key: affected rows: %s' % rows)


  
