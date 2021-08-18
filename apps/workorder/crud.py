from sqlalchemy.orm import Session, aliased
from sqlalchemy import or_
from apps.user.schemas import UserOut
from database.models import Workorder, User, Instance, Sqlrecord, Role, Workorder_data_export
from fastapi import HTTPException
from utils.inception import inception, inception_host, inception_port, inception_user, inception_pwd
import pymysql
from database.config import pymysql_config, exec_sql
from database import config
import threading, time
from utils.AES_ECB_pkcs7_128 import en_pwd, de_pwd
from apps.workorder import schemas
from cassandra import ConsistencyLevel
# 引入Cluster模块
from cassandra.cluster import Cluster
# 引入DCAwareRoundRobinPolicy模块，可用来自定义驱动程序的行为
# from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement


def workorder(db: Session, user: UserOut, offset, limit):
    u1 = aliased(User)
    u2 = aliased(User)
    try:
        objs = db.query(Workorder.id, u1.username, u2.username, Instance.ins_name, Instance.host, Instance.type,
                        Workorder.dbname, Workorder.create_time, Workorder.remark).join(u1, u1.id == Workorder.approver_manager).join(
            u2, u2.id == Workorder.approver_dba).join(
            Instance, Instance.id == Workorder.instance_id).join(Sqlrecord, Sqlrecord.wkodid == Workorder.id).filter(
            Workorder.sponsor == user.id).distinct().order_by(Workorder.id.desc())
        count = objs.count()
        objs = objs.offset((offset - 1) * limit).limit(limit).all()
        res = [dict(
            zip(['id', 'approver_manager', 'approver_dba', 'ins_name', 'host', 'type', 'dbname', 'create_time', 'remark', 'sql', ],
                i)) for i in objs]
        for i in res:
            sql = db.query(Sqlrecord.id, Sqlrecord.content, Sqlrecord.status_code, User.username,
                           Sqlrecord.remark, Sqlrecord.affected_rows, Sqlrecord.execute_time).join(
                User, User.id == Sqlrecord.approved, isouter=True).filter(
                Sqlrecord.wkodid == i['id']).order_by(Sqlrecord.status_code.asc()).all()
            sql = [dict(zip(['id', 'sql', 'status_code', 'approved', 'remark', 'affected_rows', 'execute_time'], s)) for s in sql]
            for j in sql:
                # if j['status_code'] == 1:
                if not j['remark']: j['remark'] = ''
                if not j['approved']: j['approved'] = ''
            i['sql'] = sql[0:100]

        return {'data': res, 'total': count, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def pending_wo(db: Session, user: UserOut, offset, limit):
    try:
        role = db.query(Role).filter(Role.id == user.role_id).first()
        objs = db.query(Workorder.id, User.username, Instance.ins_name, Instance.host, Instance.type, Workorder.dbname, Workorder.create_time,
                        Workorder.remark).join(
            User, User.id == Workorder.sponsor).join(Instance, Instance.id == Workorder.instance_id).join(Sqlrecord, Sqlrecord.wkodid == Workorder.id)
        if role.role == '主管':
            objs = objs.filter(
                Workorder.approver_manager == user.id, Sqlrecord.remark == None, Sqlrecord.status_code == 1).distinct().order_by(Workorder.id.desc())
        elif role.role == 'DBA':
            objs = objs.filter(or_(Workorder.approver_manager == user.id, Workorder.approver_dba == user.id),
                               Sqlrecord.remark == None, Sqlrecord.status_code == 1).distinct().order_by(
                Workorder.id.desc())
        elif role.role == 'admin':
            objs = objs.filter(Sqlrecord.remark == None, Sqlrecord.status_code == 1).distinct().order_by(Workorder.id.desc())
        else:
            return {'data': None, 'msg': 'success', 'isemp': True}
        count = objs.count()
        objs = objs.all()
        res = [dict(zip(
            ['id', 'sponsor', 'ins_name', 'host', 'type', 'dbname', 'create_time', 'remark'], i)) for i in objs]
        res_bak = res.copy()
        for i in res_bak:
            sql = db.query(Sqlrecord.id, Sqlrecord.content, Sqlrecord.status_code,
                           Sqlrecord.remark, Sqlrecord.affected_rows, Sqlrecord.execute_time).filter(
                Sqlrecord.wkodid == i['id'], Sqlrecord.status_code == 1, Sqlrecord.remark == None).all()
            sql = [dict(zip(['id', 'sql', 'status_code', 'remark', 'affected_rows', 'execute_time'], s)) for s in sql if sql]
            i['sql'] = sql[0:100]
            if not i['sql']:
                res.remove(i)
        return {'data': res, 'total': count, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def update_sqlrecord(db: Session, id: int, user: UserOut, remark: str):
    try:
        obj = db.query(Sqlrecord).filter(Sqlrecord.id == id).first()
        obj.remark = remark
        obj.approved = user.id
        db.commit()
        return {'data': obj, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def commit_workorder(db: Session, id: int, user: UserOut):
    wkodid = db.query(Sqlrecord.wkodid).filter(Sqlrecord.id == id).first()
    wkod = db.query(Workorder.instance_id, Workorder.dbname).filter(Workorder.id == wkodid[0]).first()
    ins = db.query(Instance).filter(Instance.id == wkod[0]).first()
    sqlrecord = db.query(Sqlrecord).filter(Sqlrecord.id == id).first()

    def exec_inception():
        try:
            sql = " update sqlrecord set remark = '执行中',status_code='2' where id='{}' " \
                .format(id)
            exec_sql(sql)
            while 1:  # 如果同一个库有在执行的就阻塞
                db_name_list = []
                osc_list = get_osc(db, user).get('data')
                for i in osc_list:
                    db_name_list.append(i['DBNAME'])
                if wkod[1] not in db_name_list:
                    break
                print("同一个库有在执行-阻塞")
                time.sleep(10)
            ins.password = de_pwd(ins.password)
            res = []
            status_code = 3
            approved = user.id
            remark = ''
            sequence = ''
            affected_rows = '1'
            execute_time = '1'
            backup_dbname = ''
            if ins.db_type == "mysql":
                res = inception(ins.user, ins.password, ins.host, ins.port, wkod[1], sqlrecord.content, 'execute')
                for i in res:
                    sequence = i[7]
                    remark = str(i[4])
                    affected_rows = str(i[6])
                    execute_time = str(i[9])
                    backup_dbname = str(i[8])
                    if int(i[2]) == 2:
                        status_code = 2
                    print(i)
            elif ins.db_type == "cassandra":
                # 配置Cassandra集群的IP，记得改成自己的远程数据库IP哦
                contact_points = [ins.host, ]
                # 配置登陆Cassandra集群的账号和密码，记得改成自己知道的账号和密码
                auth_provider = PlainTextAuthProvider(username=ins.user, password=ins.password)
                # 创建一个Cassandra的cluster
                cluster = Cluster(contact_points=contact_points, auth_provider=auth_provider, port=ins.port)
                # 连接并创建一个会话
                session = cluster.connect()
                session.execute('use {};'.format(wkod[1]))
                session.execute(sqlrecord.content)
                cluster.shutdown()
            sql = " update sqlrecord set `remark` = '{}',`status_code`='{}',`approved`='{}',`sequence`='{}',`affected_rows`='{}',`execute_time`='{}',`backup_dbname`='{}' where `id`='{}';" \
                .format(remark.replace('\'', ' '), status_code, approved, sequence, affected_rows, execute_time, backup_dbname, id)
            exec_sql(sql)
        except Exception as e:
            sql = " update sqlrecord set remark = '{}',status_code='{}',approved='{}' where id='{}';" \
                .format(str(e).replace('\'', ' '), 2, user.id, id)
            exec_sql(sql)

    t = threading.Thread(target=exec_inception, )
    t.start()
    return {'data': None, 'msg': 'success'}


def commit_workorder_all(db: Session, wkodid: int, user: UserOut):
    wkod = db.query(Workorder.instance_id, Workorder.dbname).filter(Workorder.id == wkodid).first()
    ins = db.query(Instance).filter(Instance.id == wkod[0]).first()
    Sqlrecord_ = db.query(Sqlrecord.id, Sqlrecord.content).filter(Sqlrecord.wkodid == wkodid, Sqlrecord.status_code == 1).all()
    Sqlrecord_ = list(Sqlrecord_)
    sql = " update sqlrecord set remark = '执行中',status_code='2' where wkodid='{}' and status_code='1' " \
        .format(wkodid)
    exec_sql(sql)
    ins.password = de_pwd(ins.password)

    def func1():
        conn = pymysql_config(config.mysql_db)
        cursor = conn.cursor()
        status_code = 3
        approved = user.id
        remark = ''
        sequence = ''
        affected_rows = '1'
        execute_time = '1'
        backup_dbname = ''
        if ins.db_type == "mysql":
            while 1:  # 如果同一个库有在执行的就阻塞
                db_name_list = []
                osc_list = get_osc(db, user).get('data')
                for i in osc_list:
                    db_name_list.append(i['DBNAME'])
                if wkod[1] not in db_name_list:
                    break
                print("同一个库有在执行-阻塞")
                time.sleep(10)
            sql = ''
            for i_sql in Sqlrecord_:
                sql += i_sql.content + ';'

            res = inception(ins.user, ins.password, ins.host, ins.port, wkod[1], sql, 'execute')
            index = 0
            for i in res:
                if index == 0:
                    index += 1
                    continue
                sequence = i[7]
                remark = str(i[4])
                affected_rows = str(i[6])
                execute_time = str(i[9])
                backup_dbname = str(i[8])
                if int(i[2]) == 2:
                    status_code = 2
                print(i)
                if i[1] == 'CHECKED':
                    remark = '未执行(前一条sql执行失败,后面的sql未执行)！'
                sql = " update sqlrecord set `remark` = '{}',`status_code`='{}',`approved`='{}',`sequence`='{}',`affected_rows`='{}',`execute_time`='{}',`backup_dbname`='{}' where `id`='{}';" \
                    .format(remark.replace('\'', ' '), status_code, approved, sequence, affected_rows, execute_time, backup_dbname,
                            Sqlrecord_[index - 1].id)
                # exec_sql(sql)
                rows = cursor.execute(sql)
                conn.commit()
                index += 1

        elif ins.db_type == "cassandra":
            # 配置Cassandra集群的IP，记得改成自己的远程数据库IP哦
            contact_points = [ins.host, ]
            # 配置登陆Cassandra集群的账号和密码，记得改成自己知道的账号和密码
            auth_provider = PlainTextAuthProvider(username=ins.user, password=ins.password)
            # 创建一个Cassandra的cluster
            cluster = Cluster(contact_points=contact_points, auth_provider=auth_provider, port=ins.port)
            # 连接并创建一个会话
            session = cluster.connect()
            session.execute('use {};'.format(wkod[1]))
            for i_sql in Sqlrecord_:
                try:
                    id = i_sql.id
                    content = i_sql.content
                    session.execute(content)
                    sql = " update sqlrecord set `remark` = '{}',`status_code`='{}',`approved`='{}',`sequence`='{}',`affected_rows`='{}',`execute_time`='{}',`backup_dbname`='{}' where `id`='{}';" \
                        .format(remark.replace('\'', ' '), status_code, approved, sequence, affected_rows, execute_time, backup_dbname, id)
                    # exec_sql(sql)
                    rows = cursor.execute(sql)
                    conn.commit()
                except Exception as e:
                    sql = " update sqlrecord set remark = '{}',status_code='{}',approved='{}' where id='{}';" \
                        .format(str(e).replace('\'', ' '), 2, user.id, id)
                    # exec_sql(sql)
                    rows = cursor.execute(sql)
                    conn.commit()
            cluster.shutdown()
        cursor.close()
        conn.close()

    t = threading.Thread(target=func1)
    t.start()
    return {'data': None, 'msg': 'success'}


def history_order(db: Session, user: UserOut, offset: int, limit: int, start_time, end_time, is_check, sponsor, host, dbname):
    try:
        u1 = aliased(User)
        u2 = aliased(User)
        role = db.query(Role).filter(Role.id == user.role_id).first()
        objs = db.query(Workorder.id, User.username, Instance.ins_name, Instance.host, Instance.type,
                        Workorder.dbname, Workorder.create_time, Workorder.remark, u1.username, u2.username, Workorder.is_check).join(
            User, User.id == Workorder.sponsor).join(Instance, Instance.id == Workorder.instance_id).join(
            Sqlrecord, Sqlrecord.wkodid == Workorder.id).join(u1, u1.id == Workorder.approver_manager).join(
            u2, u2.id == Workorder.approver_dba)
        if role.role in ('admin', 'DBA'):
            objs = objs.distinct().order_by(Workorder.id.desc())
        if role.role in ['主管']:
            objs = objs.filter(Workorder.approver_manager == user.id).distinct().order_by(
                Workorder.id.desc())
        if is_check != 2:
            objs = objs.filter(Workorder.is_check == is_check)
        if start_time and end_time:
            timeArray = time.localtime(int(start_time))
            start_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            timeArray = time.localtime(int(end_time))
            end_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            objs = objs.filter(Workorder.create_time > start_time, Workorder.create_time < end_time)
        if sponsor:
            objs = objs.filter(User.username.like('%' + sponsor + '%'))
        if host:
            objs = objs.filter(Instance.host == host)
        if dbname:
            objs = objs.filter(Workorder.dbname == dbname)

        count = objs.count()
        objs = objs.offset((offset - 1) * limit).limit(limit).all()
        res = [dict(zip(
            ['id', 'sponsor', 'ins_name', 'host', 'type', 'dbname', 'create_time', 'remark', 'approver_manager', 'approver_dba', 'is_check'], i))
            for i in objs]
        res_bak = res.copy()
        for i in res_bak:
            sql = db.query(Sqlrecord.id, Sqlrecord.content, Sqlrecord.status_code,
                           Sqlrecord.remark, User.username, Sqlrecord.affected_rows, Sqlrecord.execute_time).join(
                User, User.id == Sqlrecord.approved, isouter=True).filter(
                Sqlrecord.wkodid == i['id']).order_by(Sqlrecord.status_code.asc()).all()
            sql = [dict(zip(['id', 'sql', 'status_code', 'remark', 'approved', 'affected_rows', 'execute_time'], s)) for s in sql if sql]
            for j in sql:
                if not j['remark']: j['remark'] = ''
                if not j['approved']: j['approved'] = ''
            i['sql'] = sql[0:100]
            # if not i['sql']:
            #     res.remove(i)
        return {'data': res, 'total': count, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def sql_list(db: Session, user: UserOut, offset: int, limit: int, id: int):
    try:
        sql = db.query(Sqlrecord.id, Sqlrecord.content, Sqlrecord.status_code,
                       Sqlrecord.remark, User.username, Sqlrecord.affected_rows, Sqlrecord.execute_time).join(
            User, User.id == Sqlrecord.approved, isouter=True).filter(
            Sqlrecord.wkodid == id).order_by(Sqlrecord.status_code.asc()).all()
        count = sql.count()
        objs = sql.offset((offset - 1) * limit).limit(limit).all()
        sql = [dict(zip(['id', 'sql', 'status_code', 'remark', 'approved', 'affected_rows', 'execute_time'], s)) for s in sql if sql]
        for j in sql:
            if not j['remark']: j['remark'] = ''
            if not j['approved']: j['approved'] = ''
        return {'data': sql, 'total': count, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def order_mark_check(db: Session, user: UserOut, id: int):
    try:
        workorder_ = db.query(Workorder).filter(Workorder.id == id).first()
        workorder_.is_check = 1
        db.commit()
        return {'data': None, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def data_export_order_mark_check(db: Session, user: UserOut, id: int):
    try:
        workorder_ = db.query(Workorder_data_export).filter(Workorder_data_export.id == id).first()
        workorder_.is_check = 1
        db.commit()
        return {'data': None, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def rollback_sql(db: Session, user: UserOut, id: int):
    try:
        role = db.query(Role).filter(Role.id == user.role_id).first()
        if role.role in ('admin', 'DBA'):
            sqlrecord = db.query(Sqlrecord).filter(Sqlrecord.id == id).first()
            sql_part = sqlrecord.content.lower().split()
            ins = db.query(Instance.user, Instance.password, Instance.host, Instance.port, Workorder.dbname). \
                join(Workorder, Workorder.id == sqlrecord.wkodid).first()
            con = pymysql_config(sqlrecord.backup_dbname)
            cur = con.cursor()
            cur.execute('select tablename from ' + '$_$inception_backup_information$_$' + ' where opid_time = "' + sqlrecord.sequence + '"')
            for x in cur.fetchall():
                table_name = x[0]
                flag = cur.execute('select rollback_statement from ' + table_name + ' where opid_time = "' + sqlrecord.sequence + '"')
                rb_sql = cur.fetchall()
                print(rb_sql)
                for i in rb_sql:
                    res = inception(user=ins[0], password=de_pwd(ins[1]), host=ins[2], port=ins[3], db=ins[4], sql=i[0], operate='execute')
                    for j in res:
                        if j[4]:
                            return {'data': None, 'msg': i[4]}
                    print(res)
            sqlrecord.remark = 'rollbacked'
            db.commit()
            cur.close()
            con.close()
            return {'data': None, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_rollbacksql(db: Session, user: UserOut, id: int):
    try:
        # role = db.query(Role).filter(Role.id == user.role_id).first()
        # if role.role in ('admin', 'DBA'):
        sqlrecord = db.query(Sqlrecord).filter(Sqlrecord.id == id).first()
        con = pymysql_config(sqlrecord.backup_dbname)
        cur = con.cursor()
        cur.execute('select tablename from ' + '$_$inception_backup_information$_$' + ' where opid_time = "' + sqlrecord.sequence + '"')
        data = ''
        for j in cur.fetchall():
            table_name = j[0]
            flag = cur.execute('select rollback_statement from ' + table_name + ' where opid_time = "' + sqlrecord.sequence + '"')
            rb_sql = cur.fetchall()
            print(rb_sql)
            for i in rb_sql:
                data += i[0]
        cur.close()
        con.close()
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def download_rollbacksql(db: Session, id: int):
    try:
        sqlrecord = db.query(Sqlrecord).filter(Sqlrecord.wkodid == id)
        con = pymysql_config(sqlrecord[0].backup_dbname)
        cur = con.cursor()
        data = ''
        for sql_li in sqlrecord:
            cur.execute('select tablename from ' + '$_$inception_backup_information$_$' + ' where opid_time = "' + sql_li.sequence + '"')
            for j in cur.fetchall():
                table_name = j[0]
                flag = cur.execute('select rollback_statement from ' + table_name + ' where opid_time = "' + sql_li.sequence + '"')
                rb_sql = cur.fetchall()
                print(rb_sql)
                for i in rb_sql:
                    data += i[0]

        cur.close()
        con.close()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_osc(db: Session, user: UserOut):
    try:
        sql = "inception get osc processlist;"
        conn = pymysql.connect(host=inception_host, user=inception_user, passwd=inception_pwd, port=inception_port, charset="utf8mb4", )
        cur = conn.cursor()
        ret = cur.execute(sql)
        result = cur.fetchall()
        cur.close()
        conn.close()
        data = []
        for i in result:
            data.append({"DBNAME": i[0], "TABLENAME": i[1], "COMMAND": i[2], "PERCENT": i[4], "REMAINTIME": i[5], "SQLSHA1": i[3]})
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def pause_osc(db: Session, user: UserOut, osc: schemas.Osc):
    print(osc.SQLSHA1)
    try:
        sql = "inception pause osc '{}';".format(osc.SQLSHA1)
        conn = pymysql.connect(host=inception_host, user=inception_user, passwd=inception_pwd, port=inception_port, charset="utf8mb4", )
        cur = conn.cursor()
        ret = cur.execute(sql)
        result = cur.fetchall()
        cur.close()
        conn.close()
        return {'data': result, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def resume_osc(db: Session, user: UserOut, osc: schemas.Osc):
    print(osc.SQLSHA1)
    try:
        sql = "inception resume osc '{}';".format(osc.SQLSHA1)
        conn = pymysql.connect(host=inception_host, user=inception_user, passwd=inception_pwd, port=inception_port, charset="utf8mb4", )
        cur = conn.cursor()
        ret = cur.execute(sql)
        result = cur.fetchall()
        cur.close()
        conn.close()
        return {'data': result, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def kill_osc(db: Session, user: UserOut, osc: schemas.Osc):
    print(osc.SQLSHA1)
    try:
        sql = "inception kill osc  '{}';".format(osc.SQLSHA1)
        conn = pymysql.connect(host=inception_host, user=inception_user, passwd=inception_pwd, port=inception_port, charset="utf8mb4", )
        cur = conn.cursor()
        ret = cur.execute(sql)
        result = cur.fetchall()
        cur.close()
        conn.close()
        return {'data': result, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def data_export_pending(db: Session, user: UserOut, offset, limit):
    try:
        role = db.query(Role).filter(Role.id == user.role_id).first()
        objs = db.query(Workorder_data_export.id, User.username, Instance.ins_name, Instance.host, Instance.type,
                        Workorder_data_export.dbname, Workorder_data_export.create_time, Workorder_data_export.sql,
                        Workorder_data_export.status, Workorder_data_export.remark).join(User, User.id == Workorder_data_export.sponsor).join(
            Instance, Instance.id == Workorder_data_export.instance_id)
        if role.role == '主管':
            objs = objs.filter(
                Workorder_data_export.approver_manager == user.id, Workorder_data_export.status == 0).distinct().order_by(
                Workorder_data_export.id.desc())
        elif role.role == 'DBA':
            objs = objs.filter(
                or_(Workorder_data_export.approver_manager == user.id, Workorder_data_export.approver_dba == user.id),
                Workorder_data_export.status == 0).distinct().order_by(Workorder_data_export.id.desc())
        elif role.role == 'admin':
            objs = objs.filter(Workorder_data_export.status == 0).distinct().order_by(Workorder_data_export.id.desc())
        else:
            return {'data': None, 'msg': 'success', 'isemp': True}
        count = objs.count()
        objs = objs.all()
        res = [dict(zip(
            ['id', 'sponsor', 'ins_name', 'host', 'type', 'dbname', 'create_time', 'sql', 'status', 'remark'], i)) for i in objs]
        return {'data': res, 'total': count, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def mod_data_export_status(db: Session, user: UserOut, data_export_status: schemas.Mod_data_export_status):
    try:
        obj = db.query(Workorder_data_export).filter(Workorder_data_export.id == data_export_status.id).first()
        obj.approved = user.id
        obj.status = data_export_status.status
        if data_export_status.status in (1, 2):
            obj.approver_manager = user.id
        obj.approve_time = time.strftime('%F %T')
        db.commit()
        return {'data': obj, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def workorder_data_export(db: Session, user: UserOut, offset, limit):
    u1 = aliased(User)
    u2 = aliased(User)
    try:
        objs = db.query(Workorder_data_export.id, Workorder_data_export.sponsor, Instance.ins_name, Instance.host, Instance.type,
                        Workorder_data_export.dbname, Workorder_data_export.create_time, Workorder_data_export.sql,
                        Workorder_data_export.status, Workorder_data_export.path, u1.username, u2.username, Workorder_data_export.remark,
                        Workorder_data_export.approve_time, Workorder_data_export.download_time).join(
            u1, u1.id == Workorder_data_export.approver_manager).join(
            u2, u2.id == Workorder_data_export.approver_dba).join(Instance, Instance.id == Workorder_data_export.instance_id).filter(
            Workorder_data_export.sponsor == user.id).distinct().order_by(Workorder_data_export.id.desc())
        count = objs.count()
        objs = objs.offset((offset - 1) * limit).limit(limit).all()
        res = [dict(
            zip(['id', 'sponsor', 'ins_name', 'host', 'type', 'dbname', 'create_time', 'sql', 'status', 'path', 'approver_manager', 'approver_dba',
                 'remark', 'approve_time', 'download_time'],
                i)) for i in objs]

        return {'data': res, 'total': count, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def historyorder_data_export(db: Session, user: UserOut, offset: int, limit: int, start_time, end_time, is_check, sponsor, host, dbname):
    u1 = aliased(User)
    u2 = aliased(User)
    try:
        role = db.query(Role).filter(Role.id == user.role_id).first()
        objs = db.query(Workorder_data_export.id, User.username, Instance.ins_name, Instance.host, Instance.type, Workorder_data_export.dbname,
                        Workorder_data_export.create_time, Workorder_data_export.sql, Workorder_data_export.status,
                        Workorder_data_export.path, Workorder_data_export.remark, u1.username, u2.username, Workorder_data_export.approve_time,
                        Workorder_data_export.download_time, Workorder_data_export.is_check).join(
            User, User.id == Workorder_data_export.sponsor).join(Instance, Instance.id == Workorder_data_export.instance_id).join(
            u1, u1.id == Workorder_data_export.approver_manager).join(u2, u2.id == Workorder_data_export.approver_dba)
        if role.role in ('admin', 'DBA'):
            objs = objs.distinct().order_by(Workorder_data_export.id.desc())
        elif role.role in ['主管']:
            objs = objs.filter(Workorder_data_export.approver_manager == user.id).distinct().order_by(Workorder_data_export.id.desc())
        else:
            return {'data': None, 'total': 0, 'msg': 'success'}
        if is_check != 2:
            objs = objs.filter(Workorder_data_export.is_check == is_check)
        if start_time and end_time:
            timeArray = time.localtime(int(start_time))
            start_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            timeArray = time.localtime(int(end_time))
            end_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            objs = objs.filter(Workorder_data_export.create_time > start_time, Workorder_data_export.create_time < end_time)
        if sponsor:
            objs = objs.filter(User.username.like('%' + sponsor + '%'))
        if host:
            objs = objs.filter(Instance.host == host)
        if dbname:
            objs = objs.filter(Workorder_data_export.dbname == dbname)
        count = objs.count()
        objs = objs.offset((offset - 1) * limit).limit(limit).all()
        res = [dict(zip(['id', 'sponsor', 'ins_name', 'host', 'type', 'dbname', 'create_time', 'sql', 'status', 'path', 'remark', 'approver_manager',
                         'approver_dba', 'approve_time', 'download_time', 'is_check'], i)) for i in objs]
        return {'data': res, 'total': count, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
