import os
import pymysql

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

mysql_host = os.getenv('mysql_host')
mysql_port = os.getenv('mysql_port')
mysql_user = os.getenv('mysql_user')
mysql_pwd = os.getenv('mysql_pwd')
mysql_db = os.getenv('mysql_db')

if os.getenv('PYTHONENV') == 'prod':
    SECRET_KEY = "6f998b1564aee153e8fc375ea1cdecdd6c40489611ad56cc32f3135b1bf47cd7"
    if not mysql_host:
        mysql_host = '10.157.36.11'
    if not mysql_port:
        mysql_port = 6033
    if not mysql_user:
        mysql_user = 'mysqladmin'
    if not mysql_pwd:
        mysql_pwd = '123456'
    if not mysql_db:
        mysql_db = 'sql_audit'
elif os.getenv('PYTHONENV') == 'stage':
    SECRET_KEY = "6f998b1564aee153e8fc375ea1cdecdd6c40489611ad56cc32f3135b1bf47cd8"
    mysql_host = '10.157.24.59'
    mysql_port = 3306
    mysql_user = 'system'
    mysql_pwd = 'root123'
    mysql_db = 'monitor'
elif os.getenv('PYTHONENV') == 'aliyun_stage':
    SECRET_KEY = "6f998b1564aee153e8fc375ea1cdecdd6c40489611ad56cc32f3135b1bf47cd8"
    mysql_host = '10.157.24.59'
    mysql_port = 3306
    mysql_user = 'system'
    mysql_pwd = 'root123'
    mysql_db = 'monitor'
else:
    SECRET_KEY = "6f998b1564aee153e8fc375ea1cdecdd6c40489611ad56cc32f3135b1bf47cd8"
    if not mysql_host:
        mysql_host = '127.0.0.1'
    if not mysql_port:
        mysql_port = 3306
    if not mysql_user:
        mysql_user = 'root'
    if not mysql_pwd:
        mysql_pwd = '123456'
    if not mysql_db:
        mysql_db = 'sql_audit'

engine = create_engine(
    'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(mysql_user, mysql_pwd, mysql_host, mysql_port, mysql_db),
    echo=False, pool_pre_ping=True)
localsession = sessionmaker(bind=engine)
Base = declarative_base()


def pymysql_config(db: str):
    connection = pymysql.connect(user=mysql_user, password=mysql_pwd, host=mysql_host, port=mysql_port, database=db)
    return connection


def exec_sql(sql):
    conn = pymysql_config(mysql_db)
    cursor = conn.cursor()  # 拿到游标，即mysql >
    rows = cursor.execute(sql)
    print(sql)
    print('%s row in set (0.00 sec)' % rows)
    conn.commit()  # 提交到数据库
    cursor.close()
    conn.close()
    return cursor.fetchall()


def exec_distal_sql(sql, user, pwd, host, port, db):
    conn = pymysql.connect(user=user, password=pwd, host=host, port=port, database=db)
    cursor = conn.cursor()  # 拿到游标，即mysql >
    print(sql)
    rows = cursor.execute(sql)
    print('%s row in set (0.00 sec)' % rows)
    conn.commit()  # 提交到数据库
    cursor.close()
    conn.close()
    return cursor.fetchall()


def exec_distal_sql_dict(sql, user, pwd, host, port, db):
    conn = pymysql.connect(user=user, password=pwd, host=host, port=port, database=db)
    cursor = conn.cursor(pymysql.cursors.DictCursor)  # 拿到游标，即mysql >
    print(sql)
    rows = cursor.execute(sql)
    print('%s row in set (0.00 sec)' % rows)
    conn.commit()  # 提交到数据库
    cursor.close()
    conn.close()
    return cursor.fetchall()
