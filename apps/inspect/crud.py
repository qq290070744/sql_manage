from sqlalchemy.orm import Session
from . import schemas
from utils.inception import inception
from fastapi import HTTPException
from apps.user.schemas import UserOut
from database.models import User, Role, Privilege, Instance, Workorder, Sqlrecord
from utils.AES_ECB_pkcs7_128 import de_pwd, en_pwd
import time, os


def inspect(db: Session, query: schemas.Query, user):
    global pri
    res = []
    sql = []
    try:
        ins = db.query(Instance).filter(Instance.id == query.selectHost).first()
        role = db.query(Role).filter(Role.id == user.role_id).first()
        if role.role not in ('admin', 'DBA'):
            pri = db.query(Privilege).join(Instance, Instance.id == Privilege.instance_id).filter(
                Instance.id == ins.id, Privilege.role_id == user.role_id).first()
            if not pri:
                return {'data': ['权限拒绝'], 'msg': 'success'}
            pri = pri.privileges.split(',')
            pri.append('use')
        if ins.db_type == 'mysql':
            res = inception(user=ins.user, password=de_pwd(ins.password), host=ins.host, port=ins.port, db=query.selectDb,
                            sql=query.sql.strip().replace('\n', ' '), operate='check')
            if len(res) == 1:
                return {'data': ['注释无法提交！'], 'msg': 'success'}
            # print(res)
            # if len(res) > 10001:
            #     return {'data': ['超过10000条SQL，无法提交，请联系管理员！'], 'msg': 'success'}
            cont = [i[4] for i in res if (not sql.append({"sql": i[5], "affected_rows": i[6], "execute_time": i[9]}) and i[4])]
            if role.role not in ('admin', 'DBA'):
                for i in sql:
                    op = i['sql'].split(' ')
                    if op[0].lower() not in pri or (op[0].lower() in ('alter', 'create') and op[1].lower() != 'table'):
                        if op[1].lower() == 'index':
                            continue
                        return {'data': ["没有权限! 拒绝" + i['sql'].split(' ')[0]], 'msg': 'success'}
            if any(cont):
                return {'data': cont, 'msg': 'success'}
            wkod = Workorder(sponsor=user.id, approver_manager=query.manager, approver_dba=query.dba,
                             instance_id=query.selectHost, dbname=query.selectDb, remark=query.remark, create_time=time.strftime("%F %T"))
            db.add(wkod)
            db.commit()
            for i in sql[1:]:
                sqlrd = Sqlrecord(content=i['sql'], affected_rows=i['affected_rows'], execute_time=i['execute_time'], status_code=1, wkodid=wkod.id)
                db.add(sqlrd)
            db.commit()
        elif ins.db_type == 'cassandra':
            li = query.sql.strip().replace('\n', ' ').split(";")
            wkod = Workorder(sponsor=user.id, approver_manager=query.manager, approver_dba=query.dba,
                             instance_id=query.selectHost, dbname=query.selectDb, remark=query.remark, create_time=time.strftime("%F %T"))
            db.add(wkod)
            db.commit()
            for i in li:
                if len(i) == 0:
                    continue
                sqlrd = Sqlrecord(content=i, affected_rows='1', execute_time='1', status_code=1, wkodid=wkod.id)
                db.add(sqlrd)
            db.commit()
        return {'data': None, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_master_ins(db: Session, user=UserOut):
    try:
        role = db.query(Role).filter(user.role_id == Role.id).first()
        if role.role in ('admin', 'DBA'):
            ins_part = db.query(Instance).filter(Instance.type == 'master')
            count = ins_part.count()
        else:
            ins_part = db.query(Instance).join(Privilege, Instance.id == Privilege.instance_id, ).filter(
                Privilege.role_id == user.role_id, Instance.type == 'master')
            count = ins_part.count()
        return {'data': ins_part.all(), 'total': count, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_approver(db: Session, user: UserOut):
    try:
        role = db.query(Role).filter(user.role_id == Role.id).first()
        if role.role == 'DBA':
            manager = db.query(User).join(Role, User.role_id == Role.id).filter(Role.department == role.department,
                                                                                User.id != user.id).all()
        elif role.role == 'admin':
            manager = db.query(User).join(Role, User.role_id == Role.id).filter(Role.role == 'DBA').all()
        else:
            manager = db.query(User).join(Role, User.role_id == Role.id).filter(Role.department == role.department,
                                                                                Role.role == '主管').all()
        dba = db.query(User).join(Role, User.role_id == Role.id).filter(Role.role == 'DBA').all()
        return {'data': {'manager': manager, 'dba': dba}, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_approver_data_export(db: Session, user: UserOut):
    try:
        role = db.query(Role).filter(user.role_id == Role.id).first()
        if role.role == 'DBA':
            manager = db.query(User).join(Role, User.role_id == Role.id).filter(Role.department == role.department,
                                                                                User.id != user.id).all()
        elif role.role == 'admin':
            manager = db.query(User).join(Role, User.role_id == Role.id).filter(Role.role == 'DBA').all()
        else:
            manager = db.query(User).join(Role, User.role_id == Role.id).filter(Role.department == role.department,
                                                                                Role.role == '主管').all()
        dba = db.query(User).join(Role, User.role_id == Role.id).filter(Role.role == 'DBA').all()
        return {'data': {'manager': manager, 'dba': dba}, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def alter_merge(db: Session, query: schemas.alter_merge_sql):
    try:
        sql = query.sql.replace('"', '\\"')
        sql = sql.replace('\n', ' ')
        sql = sql.replace('`', '\\`')
        command = """ soar -query="{}" -report-type rewrite -rewrite-rules mergealter """.format(sql)
        print(command)
        res = os.popen(command)
        sql = res.read()
        return {'data': {'sql': sql}, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
