from sqlalchemy.orm import Session
from pymysql import connect, cursors
from database.models import Instance, Privilege, Role, Workorder_data_export, Desensitization_info, Query_log, User, Exec_shell_log
from fastapi import HTTPException
from . import schemas
# import paramiko
from apps.user.schemas import UserOut
import re, os, time
from utils.AES_ECB_pkcs7_128 import en_pwd, de_pwd
import threading
from fastapi.encoders import jsonable_encoder
import sqlparse
from database.config import exec_distal_sql_dict
import csv
from cassandra import ConsistencyLevel
# 引入Cluster模块
from cassandra.cluster import Cluster
# 引入DCAwareRoundRobinPolicy模块，可用来自定义驱动程序的行为
# from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement


def get_ins(db: Session, user=UserOut):
    try:
        role = db.query(Role).filter(user.role_id == Role.id).first()
        if role.role in ('admin', 'DBA'):
            ins_part = db.query(Instance).filter(Instance.type == 'slave').all()
        else:
            ins_part = db.query(Instance).join(Privilege, Instance.id == Privilege.instance_id, ).filter(Privilege.role_id == user.role_id,
                                                                                                         Instance.type == 'slave').all()
        return {'data': ins_part, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_schema(db: Session, id: int):
    try:
        obj = db.query(Instance).filter(Instance.id == id).first()
        if obj.db_type == "mysql":
            con = connect(user=obj.user, password=de_pwd(obj.password),
                          host=obj.host, port=obj.port, connect_timeout=1)
            cur = con.cursor()
            flag = cur.execute('show databases')
            res = cur.fetchall()
            cur.close()
            con.close()
            data = []
            for j in [dict(zip(('db',), i)) for i in res if
                      i[0] not in ('information_schema', 'performance_schema', 'sys', 'mysql',)]:
                if "3306" not in j['db']:
                    data.append(j)

            return {'data': data, 'msg': 'success'}
        elif obj.db_type == "cassandra":
            # 配置Cassandra集群的IP，记得改成自己的远程数据库IP哦
            contact_points = [obj.host, ]
            # 配置登陆Cassandra集群的账号和密码，记得改成自己知道的账号和密码
            auth_provider = PlainTextAuthProvider(username=obj.user, password=de_pwd(obj.password))
            # 创建一个Cassandra的cluster
            cluster = Cluster(contact_points=contact_points, auth_provider=auth_provider, port=obj.port)
            # 连接并创建一个会话
            session = cluster.connect()
            rows = session.execute('SELECT keyspace_name FROM system_schema.keyspaces;')
            data = []
            for row in rows:
                for i in row:
                    data.append({"db": i})
            cluster.shutdown()
            return {'data': data, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # finally:


def get_table(db: Session, id: int, dbname: str):
    try:
        obj = db.query(Instance).filter(Instance.id == id).first()
        if obj.db_type == "mysql":
            con = connect(user=obj.user, password=de_pwd(obj.password), host=obj.host, port=obj.port, database=dbname,
                          connect_timeout=1)
            # cur=con.cursor(cursor=cursors.DictCursor)
            cur = con.cursor()
            flag = cur.execute('show tables')
            res = cur.fetchall()
            # tables = {i[0]: [j[0] for j in cur.fetchall()] for i in res}
            tables = {i[0]: [j[0] for j in cur.fetchall()] for i in res if
                      cur.execute('desc ' + i[0])}
            cur.close()
            con.close()
            return {'data': {'tables': tables}, 'msg': 'success'}
        elif obj.db_type == "cassandra":
            # 配置Cassandra集群的IP，记得改成自己的远程数据库IP哦
            contact_points = [obj.host, ]
            # 配置登陆Cassandra集群的账号和密码，记得改成自己知道的账号和密码
            auth_provider = PlainTextAuthProvider(username=obj.user, password=de_pwd(obj.password))
            # 创建一个Cassandra的cluster
            cluster = Cluster(contact_points=contact_points, auth_provider=auth_provider, port=obj.port)
            # 连接并创建一个会话
            session = cluster.connect()
            rows = session.execute("SELECT  table_name FROM system_schema.tables where keyspace_name='{}';".format(dbname))
            tables = {}
            for row in rows:
                for i in row:
                    tables[i] = []
                    # rows1 = session.execute(
                    #     "SELECT  column_name FROM system_schema.columns where keyspace_name='{}' and table_name='{}';".format(dbname, i))
                    # for j in rows1:
                    #     tables[i].append(j[0])
            cluster.shutdown()
            return {'data': {'tables': tables}, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # finally:
    #     cur.close()
    #     con.close()


def get_desc(db: Session, id: int, dbname: str, table: str):
    try:
        obj = db.query(Instance).filter(Instance.id == id).first()
        if obj.db_type == "mysql":
            con = connect(user=obj.user, password=de_pwd(obj.password), host=obj.host, port=obj.port, database=dbname,
                          connect_timeout=1)
            cur = con.cursor()
            flag = cur.execute('show create table ' + table)
            res = cur.fetchone()
            cur.close()
            con.close()
            return {'data': res, 'msg': 'success'}
        elif obj.db_type == "cassandra":
            # 配置Cassandra集群的IP，记得改成自己的远程数据库IP哦
            contact_points = [obj.host, ]
            # 配置登陆Cassandra集群的账号和密码，记得改成自己知道的账号和密码
            auth_provider = PlainTextAuthProvider(username=obj.user, password=de_pwd(obj.password))
            # 创建一个Cassandra的cluster
            cluster = Cluster(contact_points=contact_points, auth_provider=auth_provider, port=obj.port)
            # 连接并创建一个会话
            session = cluster.connect()
            rows = session.execute(
                "select column_name,type,kind from system_schema.columns where keyspace_name='{}' and table_name='{}';".format(dbname, table))
            res = ' 字段 \n'
            for row in rows:
                res += str(row) + "\n"
            res += '\n 索引 \n'
            rows1 = session.execute(
                "SELECT index_name,options FROM system_schema.indexes where keyspace_name='{}' and table_name='{}';".format(dbname, table))
            for row in rows1:
                res += str(row) + "\n"
            cluster.shutdown()
            return {'data': [table, res], 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # finally:
    #     cur.close()
    #     con.close()


def sqlscore(db: Session, que: schemas.Query):
    try:
        obj = db.query(Instance).filter(Instance.id == que.selectHost).first()
        sql = que.sql.replace('"', '\\"')
        sql = sql.replace('`', '\\`')
        if obj.db_type == "mysql":
            soaryaml = """
    test-dsn:
      addr: {}:{}
      schema: {}
      user: {}
      password: {}
      disable: false
    allow-online-as-test: true
            """.format(obj.host, obj.port, que.selectDb, obj.user, de_pwd(obj.password))
        else:
            soaryaml = ''
        with open("/etc/soar.yaml", "w") as f:
            f.write(soaryaml)
        command = """ soar -query="{}"  """.format(
            sql)
        print(command)
        res = os.popen(command)
        return {'data': res.readlines(), 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def sqlexec(db: Session, que: schemas.Query, user=UserOut):
    is_select = que.sql.strip().replace('\n', ' ').split(' ')[0].lower()
    print(is_select)
    if is_select not in ['select', 'explain', 'desc', 'show']:
        return {'data': None, 'msg': '仅支持select操作'}
    try:
        cou = 0
        res = []
        obj = db.query(Instance).filter(Instance.id == que.selectHost).first()
        obj1 = db.query(Desensitization_info).filter(Desensitization_info.instance_id == que.selectHost,
                                                     Desensitization_info.dbname == que.selectDb).all()
        field_list = []
        for i in obj1:
            field_list.append(i.field)
        stmts = sqlparse.split(que.sql)
        for stmt in stmts:
            stmt_parsed = sqlparse.parse(stmt)
            for j in str(stmt_parsed[0].tokens[2]).split(','):
                x = j.split()
                if len(x) == 2:
                    if x[0].upper() in field_list or x[0].lower() in field_list:
                        field_list.append(x[1].upper())
                        field_list.append(x[1].lower())
                elif len(x) == 3:
                    if x[0].upper() in field_list or x[0].lower() in field_list:
                        field_list.append(x[2].upper())
                        field_list.append(x[2].lower())
        if is_select in ['select', ]:
            if 'limit' in que.sql or 'LIMIT' in que.sql or 'FILTERING' in que.sql or 'filtering' in que.sql:
                sql = que.sql
            else:
                sql = re.sub('limit.*|;.*', ' limit ' + str(que.limit2), que.sql + ' ;', 0, re.I)
        else:
            sql = que.sql
        if obj.db_type == "mysql":
            con = connect(user=obj.user, password=de_pwd(obj.password), host=obj.host, port=obj.port, database=que.selectDb,
                          connect_timeout=1)
            cur = con.cursor(cursors.SSDictCursor)
            cur.execute(sql)
            row = cur.fetchone()
            while row:
                for k in row:
                    row[k] = str(row[k])
                    if k.upper() in field_list or k.lower() in field_list:
                        row[k] = "脱敏字段不显示***"
                cou += 1
                # if (que.offset - 1) * que.limit < cou <= (que.offset - 1) * que.limit + que.limit:
                res.append(row)
                row = cur.fetchone()
            cur.close()
            con.close()
        elif obj.db_type == "cassandra":
            # 配置Cassandra集群的IP，记得改成自己的远程数据库IP哦
            contact_points = [obj.host, ]
            # 配置登陆Cassandra集群的账号和密码，记得改成自己知道的账号和密码
            auth_provider = PlainTextAuthProvider(username=obj.user, password=de_pwd(obj.password))
            # 创建一个Cassandra的cluster
            cluster = Cluster(contact_points=contact_points, auth_provider=auth_provider, port=obj.port)
            # 连接并创建一个会话
            session = cluster.connect()
            session.execute('use {};'.format(que.selectDb))
            # 定义一条cql查询语句
            cql_str = sql
            simple_statement = SimpleStatement(cql_str, consistency_level=ConsistencyLevel.ONE)
            # 对语句的执行设置超时时间为None
            execute_result = session.execute(simple_statement, timeout=None)
            print(execute_result.column_names)
            li = []
            for i in execute_result:
                cou += 1
                dic = {}
                idx = 0
                for j in execute_result.column_names:
                    dic[j] = str(i[idx])
                    idx += 1
                    if j.upper() in field_list or j.lower() in field_list:
                        dic[j] = "脱敏字段不显示***"
                li.append(dic)
            res = li
            cluster.shutdown()
        quelog = Query_log(sponsor=user.id, instance_id=que.selectHost, dbname=que.selectDb, sql=que.sql, create_time=time.strftime("%F %T"))
        db.add(quelog)
        db.commit()
        return {'data': res, 'total': cou, 'msg': 'success'}
    except Exception as e:
        return {'data': None, 'total': None, 'msg': str(e)}
    # finally:
    #     cur.close()
    #     con.close()


def submit_workorder_data_export(db: Session, que: schemas.Submit_workorder_data_export, user):
    if que.sql.strip().replace('\n', ' ').split(' ')[0].lower() not in ['select', 'explain']:
        return {'data': None, 'msg': '仅支持select操作'}
    # command = """ soar -query="{}" -only-syntax-check  """.format(que.sql.strip())
    # print(command)
    # res = os.popen(command).read()
    # if len(str(res).split()) != 0:
    #     return {'data': None, 'msg': '语法错误: {}'.format(res)}
    try:

        obj = db.query(Instance).filter(Instance.id == que.selectHost).first()
        obj1 = db.query(Desensitization_info).filter(Desensitization_info.instance_id == que.selectHost,
                                                     Desensitization_info.dbname == que.selectDb).all()
        field_list = []
        for i in obj1:
            field_list.append(i.field)
        stmts = sqlparse.split(que.sql)
        for stmt in stmts:
            stmt_parsed = sqlparse.parse(stmt)
            for j in str(stmt_parsed[0].tokens[2]).split(','):
                x = j.split()
                if len(x) == 2:
                    if x[0].upper() in field_list or x[0].lower() in field_list:
                        field_list.append(x[1].lower())
                        field_list.append(x[1].upper())
                elif len(x) == 3:
                    if x[0].upper() in field_list or x[0].lower() in field_list:
                        field_list.append(x[2].lower())
                        field_list.append(x[2].upper())
        path = "data_export/{}.csv".format(time.strftime("%Y%m%d%H%M%S"))
        t = threading.Thread(target=data_export_background,
                             args=(que.sql, path, obj.user, obj.password, obj.host, obj.port, que.selectDb, field_list, obj.db_type))
        t.start()
        wkod = Workorder_data_export(sponsor=user.id, approver_manager=que.manager, approver_dba=que.dba, instance_id=que.selectHost,
                                     dbname=que.selectDb, sql=que.sql, status=0, path=path, remark=que.remark, create_time=time.strftime("%F %T"))
        db.add(wkod)
        db.commit()

        return {'data': None, 'msg': 'success'}
    except Exception as e:
        return {'data': None, 'msg': str(e)}


def data_export_background(sql, path, user, password, host, port, selectDb, field_list, db_type):
    res = []
    if not os.path.isdir("data_export"):
        os.makedirs('data_export')
    if db_type == 'mysql':
        con = connect(user=user, password=de_pwd(password), host=host, port=port, database=selectDb,
                      connect_timeout=1)
        cur = con.cursor(cursors.SSDictCursor)
        cur.execute(sql)
        res = cur.fetchall()
        cur.close()
        con.close()
    elif db_type == 'cassandra':
        # 配置Cassandra集群的IP，记得改成自己的远程数据库IP哦
        contact_points = [host, ]
        # 配置登陆Cassandra集群的账号和密码，记得改成自己知道的账号和密码
        auth_provider = PlainTextAuthProvider(username=user, password=de_pwd(password))
        # 创建一个Cassandra的cluster
        cluster = Cluster(contact_points=contact_points, auth_provider=auth_provider, port=port)
        # 连接并创建一个会话
        session = cluster.connect()
        session.execute('use {};'.format(selectDb))
        # 定义一条cql查询语句
        cql_str = sql
        simple_statement = SimpleStatement(cql_str, consistency_level=ConsistencyLevel.ONE)
        # 对语句的执行设置超时时间为None
        execute_result = session.execute(simple_statement, timeout=None)
        print(execute_result.column_names)
        li = []
        for i in execute_result:
            dic = {}
            idx = 0
            for j in execute_result.column_names:
                dic[j] = str(i[idx])
                idx += 1
                if j.upper() in field_list or j.lower() in field_list:
                    dic[j] = "脱敏字段不显示***"
            li.append(dic)
        res = li
        cluster.shutdown()

    if len(res) > 0:
        rows = []
        for i in res:
            values = []
            for j in i:
                i[j] = str(i[j])
                if j.upper() in field_list or j.lower() in field_list:
                    i[j] = "脱敏字段不显示***"
                field = str(i[j])
                if "," in field:
                    field = "\"{}\"".format(field)
                field = field.replace('\n', ' ')
                values.append(field)
            rows.append(values)
        with open(path, 'w', encoding="gbk", newline='')as f:
            f_csv = csv.writer(f)
            f_csv.writerow(res[0].keys())
            f_csv.writerows(rows)


def get_query_log(db: Session, offset, limit, sponsor, dbname, start_time, end_time):
    try:
        obj = db.query(Query_log.dbname, Query_log.sql, Query_log.create_time, User.username, Instance.ins_name).join(
            User, Query_log.sponsor == User.id, ).join(Instance, Query_log.instance_id == Instance.id)
        if sponsor:
            obj = obj.filter(User.username == sponsor)
        if dbname:
            obj = obj.filter(Query_log.dbname == dbname)
        if start_time and end_time:
            timeArray = time.localtime(int(start_time))
            start_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            timeArray = time.localtime(int(end_time))
            end_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            obj = obj.filter(Query_log.create_time > start_time, Query_log.create_time < end_time)

        obj = obj.order_by(Query_log.id.desc())
        total = obj.count()
        objs = jsonable_encoder(obj.offset((offset - 1) * limit).limit(limit).all())
        res = [dict(zip(['dbname', 'sql', 'create_time', 'username', 'ins_name', ], i)) for i in
               objs]
        return {'data': res, 'msg': 'success', 'total': total, }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_sales_order(db: Session, date_time):
    try:
        if (time.time() - int(date_time)) > 604800:
            date_time = time.time() - 604800
        timeArray = time.localtime(int(date_time))
        date_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        sql = '''
        SELECT 
    DATE_FORMAT(IF(t.type = 8,
                t.order_time,
                t.payment_time),
            '%Y-%m-%d %H:%i:00') AS minutess,
 COUNT(1) AS orders,
    SUM(t.payed_amount - t.shipping_total) AS sales
FROM
    (SELECT 
        payed_amount, shipping_total, type, order_time, payment_time
    FROM
        oms.sales_order
    WHERE
        basic_status <> 'DELETED'
            AND store_id = 'S001'
            AND type <> 2
            AND type <> 9
            AND type <> 8
            AND payment_status = 1
            AND payment_time >= '{}' UNION ALL SELECT 
        payed_amount, shipping_total, type, order_time, payment_time
    FROM
        oms.sales_order
    WHERE
        basic_status <> 'DELETED'
            AND store_id = 'S001'
            AND type <> 2
            AND type <> 9
            AND type = 8
            AND order_time >= '{}') t
GROUP BY DATE_FORMAT(IF(t.type = 8,
            t.order_time,
            t.payment_time),
        '%Y-%m-%d %H:%i:00');
        '''.format(date_time, date_time)
        user, pwd, host, port = 'system', 'root123', '10.157.24.59', 3306
        if os.getenv('PYTHONENV') == 'prod':
            user, pwd, host, port = 'xxxxxxxx', 'xxxxxxx', '10.157.36.7', 3306
        data = exec_distal_sql_dict(sql, user, pwd, host, port, 'oms')
        return {'data': data, 'msg': 'success', }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def exec_shell(db: Session, que: schemas.Exec_shell):
    try:
        log_name = "/tmp/{}.log".format(time.strftime("%Y%m%d%H%M%S"))
        cmd = que.cmd
        obj = Exec_shell_log(log_name=log_name, cmd=cmd, create_time=time.strftime("%Y-%m-%d %H:%M:%S"))
        db.add(obj)
        db.commit()

        def eshell():
            os.system(""" {} > {} """.format(cmd, log_name))

        t = threading.Thread(target=eshell)
        t.start()
        return {'data': '', 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def tail_exec_shell_log(db: Session, log_name):
    try:
        log_info = os.popen("tail -100 {}".format(log_name)).read()
        return {'data': log_info, 'msg': 'success', }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_exec_shell_log_list(db: Session, ):
    try:
        objs = db.query(Exec_shell_log.log_name, Exec_shell_log.cmd, Exec_shell_log.create_time).order_by(Exec_shell_log.id.desc()).limit(5)
        res = [dict(zip(['log_name', 'cmd', 'create_time', ], i)) for i in
               objs]
        return {'data': res, 'msg': 'success', }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
