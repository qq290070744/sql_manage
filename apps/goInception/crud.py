from pymysql import connect
from pymysql.cursors import DictCursor
from fastapi import HTTPException
from database.config import pymysql_config
from utils.inception import inception_host, inception_port, inception_user, inception_pwd
from . import schemas


def inception_show_variables():
    try:
        con = connect(user=inception_user, password=inception_pwd, host=inception_host, port=inception_port, database='mysql')
        cur = con.cursor(DictCursor)
        flag = cur.execute("inception show variables;")
        res = cur.fetchall()
        cur.close()
        con.close()
        return {'data': res, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def set_inception_show_variables(inception_variables: schemas.Set_inception_show_variables):
    try:
        con = connect(user=inception_user, password=inception_pwd, host=inception_host, port=inception_port, database='mysql')
        cur = con.cursor(DictCursor)
        flag = cur.execute("inception set {} = {} ;".format(inception_variables.Variable_name, inception_variables.Value))
        res = cur.fetchall()
        cur.close()
        con.close()
        return {'data': res, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_inception_show_levels():
    try:
        con = connect(user=inception_user, password=inception_pwd, host=inception_host, port=inception_port, database='mysql')
        cur = con.cursor(DictCursor)
        flag = cur.execute("inception show levels;")
        res = cur.fetchall()
        cur.close()
        con.close()
        return {'data': res, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def set_inception_show_levels(inception_levels: schemas.Set_inception_show_levels):
    try:
        con = connect(user=inception_user, password=inception_pwd, host=inception_host, port=inception_port, database='mysql')
        cur = con.cursor(DictCursor)
        flag = cur.execute("inception set level {} = {} ;".format(inception_levels.Name, inception_levels.Value))
        res = cur.fetchall()
        cur.close()
        con.close()
        return {'data': res, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
