from sqlalchemy.orm import Session
from pymysql import connect, cursors
from database.models import Instance, Privilege, Role, Workorder_data_export, Desensitization_info
from fastapi import HTTPException
from . import schemas
# import paramiko
from apps.user.schemas import UserOut
import re, os, time
from utils.AES_ECB_pkcs7_128 import en_pwd, de_pwd
import threading


def get_desensitization_info_list(db: Session, offset: int, limit: int, user=UserOut, ):
    try:
        objs = db.query(Desensitization_info.id, Desensitization_info.dbname, Desensitization_info.field, Instance.ins_name, ).filter(
            Desensitization_info.instance_id == Instance.id).order_by(Desensitization_info.id.desc())
        count = objs.count()
        objss = objs.offset((offset - 1) * limit).limit(limit).all()
        res = [dict(zip(['id', 'dbname', 'field', 'ins_name', ], i)) for i in objss]

        return {'data': res, 'msg': 'success', "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def add_desensitization_info(db: Session, desensitization_info: schemas.Add_desensitization_info, user=UserOut, ):
    try:
        desensitization_info_ = Desensitization_info(instance_id=desensitization_info.id, dbname=desensitization_info.dbname,
                                                     field=desensitization_info.field)
        db.add(desensitization_info_)
        db.commit()
        return {'data': None, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def del_desensitization_info(db: Session, id: int, user=UserOut, ):
    try:
        obj = db.query(Desensitization_info).filter(Desensitization_info.id == id).first()
        db.delete(obj)
        db.commit()
        return {'data': obj, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
