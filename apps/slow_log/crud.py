from sqlalchemy.orm import Session, aliased
from sqlalchemy import or_
from apps.user.schemas import UserOut
from database.models import Workorder, User, Instance, Sqlrecord, Role, Workorder_data_export, Slowlogs
from fastapi import HTTPException
from utils.inception import inception, inception_host, inception_port, inception_user, inception_pwd
import pymysql
from database.config import pymysql_config, exec_sql
import threading
from utils.AES_ECB_pkcs7_128 import en_pwd, de_pwd
from apps.slow_log import schemas
from fastapi.encoders import jsonable_encoder
import time
from database.config import engine


def post_slowlog(db: Session, SlowLog: schemas.SlowLog):
    try:
        slow = Slowlogs(**SlowLog.dict())
        slow.create_time = time.strftime("%F %T")
        db.add(slow)
        db.commit()
        return {'data': slow, 'msg': 'success', }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_slowlog(db: Session, offset: int, limit: int, dbid: int, start_time: str, end_time: str):
    try:
        obj = db.query(Instance.ins_name, Slowlogs.dbid, Slowlogs.db_user, Slowlogs.app_ip, Slowlogs.exec_duration, Slowlogs.rows_sent,
                       Slowlogs.rows_examined, Slowlogs.sql_pattern, Slowlogs.orig_sql, Slowlogs.create_time).join(
            Instance, Instance.id == Slowlogs.dbid)
        if dbid:
            obj = obj.filter(Slowlogs.dbid == dbid)
        if start_time:
            obj = obj.filter(Slowlogs.start_time > start_time, Slowlogs.start_time < end_time)
        obj = obj.order_by(Slowlogs.id.desc())
        total = obj.count()
        objs = jsonable_encoder(obj.offset((offset - 1) * limit).limit(limit).all())
        res = [dict(zip(['ins_name', 'dbid', 'db_user', 'app_ip', 'exec_duration', 'rows_sent', 'rows_examined', 'sql_pattern', 'orig_sql', '时间'], i))
               for i in objs]
        return {'data': res, 'msg': 'success', 'total': total, }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_slowlog_count_top30(db: Session, offset: int, limit: int, dbid: int, start_time: str, end_time: str):
    try:
        sql = """
        SELECT 
    COUNT(1) AS count,
    ins_name,
    dbid,
    db_user,
    app_ip,
    exec_duration,
    rows_sent,
    rows_examined,
    sql_pattern,
    orig_sql
FROM
    slowlogs,instance
WHERE slowlogs.dbid=instance.id 
        """
        if dbid:
            sql += " AND dbid = {} ".format(dbid)
        if start_time:
            sql += " AND '{}' <= start_time <= '{}'".format(start_time, end_time)
        sql += " GROUP BY fingerprint ORDER BY count DESC LIMIT {},{};".format((offset - 1) * limit, limit)
        total = 30
        conn = engine.raw_connection()
        cursor = conn.cursor(pymysql.cursors.SSDictCursor)
        cursor.execute(
            sql
        )
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        # res = [dict(
        #     zip(['count', 'ins_name', 'dbid', 'db_user', 'app_ip', 'exec_duration', 'rows_sent', 'rows_examined', 'sql_pattern', 'orig_sql', ], i))
        #     for i in result]
        return {'data': result, 'msg': 'success', 'total': total, }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_slowlog_time_top30(db: Session, offset: int, limit: int, dbid: int, start_time: str, end_time: str):
    try:
        sql = """
    SELECT 
    ins_name,
    dbid,
    db_user,
    app_ip,
     round(avg(exec_duration*1000000))/1000000 as exec_duration,
    round(avg(rows_sent)) as rows_sent,
    round(avg(rows_examined)) as rows_examined,
    sql_pattern,
    orig_sql
FROM
    slowlogs,instance      
WHERE slowlogs.dbid=instance.id 
        """
        if dbid:
            sql += " AND dbid = {} ".format(dbid)
        if start_time:
            sql += " AND '{}' <= start_time <= '{}' ".format(start_time, end_time)
        sql += " GROUP BY fingerprint ORDER BY exec_duration DESC LIMIT {},{};".format((offset - 1) * limit, limit)
        total = 30
        conn = engine.raw_connection()
        cursor = conn.cursor(pymysql.cursors.SSDictCursor)
        cursor.execute(
            sql
        )
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        # res = [dict(zip(['ins_name', 'dbid', 'db_user', 'app_ip', 'exec_duration', 'rows_sent', 'rows_examined', 'sql_pattern', 'orig_sql', ], i)) for
        #        i in result]
        return {'data': result, 'msg': 'success', 'total': total, }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
