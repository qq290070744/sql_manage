from database.models import Instance
from . import schemas
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Dict
from pymysql import connect
from utils.AES_ECB_pkcs7_128 import en_pwd, de_pwd
from database.config import exec_distal_sql, exec_distal_sql_dict
import pymysql, re, time
from cassandra import ConsistencyLevel
# 引入Cluster模块
from cassandra.cluster import Cluster
# 引入DCAwareRoundRobinPolicy模块，可用来自定义驱动程序的行为
# from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement


def get_instance_by_id(db: Session, id: int):
    try:
        ins = db.query(Instance).filter(Instance.id == id).first()
        return {'data': [ins], 'total': 1, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_instances_by_ins_name(db: Session, ins_name: str, offset, limit):
    try:
        inses = db.query(Instance).filter(Instance.ins_name.like('%' + ins_name + '%'))
        count = inses.count()
        ins_part = inses.offset((offset - 1) * limit).limit(limit).all()
        return {'data': ins_part, 'total': count, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_instances(db: Session, offset: int, limit: int):
    try:
        inses = db.query(Instance)
        count = inses.count()
        if limit:
            ins_part = inses.offset((offset - 1) * limit).limit(limit).all()
            return {'data': ins_part, 'total': count, 'msg': 'success'}
        else:
            ins_part = inses.all()
            return {'data': ins_part, 'total': count, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def add_instance(db: Session, ins: schemas.InsIn):
    try:
        ins.password = en_pwd(ins.password)
        obj = Instance(**ins.dict())
        db.add(obj)
        db.commit()
        return {'data': ins, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def del_instance(db: Session, id: int):
    try:
        obj = db.query(Instance).filter(Instance.id == id).first()
        db.delete(obj)
        db.commit()
        return {'data': obj, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def update_instance(db: Session, ins: schemas.InsUpdate):
    try:
        ins.password = en_pwd(ins.password)
        obj = db.query(Instance).filter(Instance.id == ins.id).update(
            {Instance.user: ins.user, Instance.password: ins.password, Instance.port: ins.port,
             Instance.host: ins.host, Instance.type: ins.type})
        # obj.update({instance.user:ins.user,instance.password:ins.password,instance.port:ins.port,instance.host:ins.host})
        db.commit()
        if obj == 1:
            return {'data': ins, 'msg': 'success'}
        return {'data': ins, 'msg': '修改失败'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def concheck(ins: schemas.InsIn):
    try:
        if ins.db_type == 'mysql':
            con = connect(user=ins.user, password=ins.password, host=ins.host, port=ins.port,
                          connect_timeout=1)
            return {'data': None, 'msg': 'success'}
        elif ins.db_type == 'cassandra':
            # 配置Cassandra集群的IP，记得改成自己的远程数据库IP哦
            contact_points = [ins.host, ]
            # 配置登陆Cassandra集群的账号和密码，记得改成自己知道的账号和密码
            auth_provider = PlainTextAuthProvider(username=ins.user, password=ins.password)
            # 创建一个Cassandra的cluster
            cluster = Cluster(contact_points=contact_points, auth_provider=auth_provider, port=ins.port)
            # 连接并创建一个会话
            session = cluster.connect()

            cluster.shutdown()
            return {'data': None, 'msg': 'success'}
    except Exception as e:
        return {'data': None, 'msg': str(e)}


def concheck2(db: Session, id: int):
    try:
        obj = db.query(Instance).filter(Instance.id == id).first()
        con = connect(user=obj.user, password=de_pwd(obj.password), host=obj.host, port=obj.port,
                      connect_timeout=0.5)
        return {'data': None, 'msg': 'success'}
    except Exception as e:
        return {'data': None, 'msg': str(e)}


def get_binlog_list(db: Session, id: int):
    try:
        ins = db.query(Instance).filter(Instance.id == id).first()
        data = exec_distal_sql("show binary logs;", ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': {"binlog_list": data, "ins": ins}, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def del_binlog(db: Session, Del_binlog: schemas.Del_binlog):
    try:
        ins = db.query(Instance).filter(Instance.id == Del_binlog.id).first()
        data = exec_distal_sql("purge master logs to '{}';".format(Del_binlog.binlog), ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def instance_monitor(db: Session, id: int):
    # try:
    ins = db.query(Instance).filter(Instance.id == id).first()

    con = pymysql.connect(host=ins.host, user=ins.user, password=de_pwd(ins.password), port=ins.port, database='', charset='utf8')
    sql = 'show global status where Variable_name in ("Com_select","Com_insert","Com_update","Com_delete","Innodb_buffer_pool_read_requests","Innodb_buffer_pool_reads","Innodb_rows_inserted","Innodb_rows_updated","Innodb_rows_deleted","Innodb_rows_read","Threads_running","Threads_connected","Threads_cached","Threads_created","Bytes_received","Bytes_sent","Innodb_buffer_pool_pages_data","Innodb_buffer_pool_pages_free","Innodb_buffer_pool_pages_dirty","Innodb_buffer_pool_pages_flushed","Innodb_data_reads","Innodb_data_writes","Innodb_data_read","Innodb_data_written","Innodb_os_log_fsyncs","Innodb_os_log_written")'
    cursor = con.cursor()
    cursor.execute(sql)
    res = cursor.fetchall()
    mystat1 = dict(res)
    time.sleep(2)
    cursor.execute(sql)
    res = cursor.fetchall()
    mystat2 = dict(res)
    interval = 1
    insert_diff = (int(mystat2['Com_insert']) - int(mystat1['Com_insert'])) / interval
    update_diff = (int(mystat2['Com_update']) - int(mystat1['Com_update'])) / interval
    delete_diff = (int(mystat2['Com_delete']) - int(mystat1['Com_delete'])) / interval
    select_diff = (int(mystat2['Com_select']) - int(mystat1['Com_select'])) / interval
    read_request = (int(mystat2['Innodb_buffer_pool_read_requests']) - int(mystat1['Innodb_buffer_pool_read_requests'])) / interval
    read = (int(mystat2['Innodb_buffer_pool_reads']) - int(mystat1['Innodb_buffer_pool_reads'])) / interval
    innodb_rows_inserted_diff = (int(mystat2['Innodb_rows_inserted']) - int(mystat1['Innodb_rows_inserted'])) / interval
    innodb_rows_updated_diff = (int(mystat2['Innodb_rows_updated']) - int(mystat1['Innodb_rows_updated'])) / interval
    innodb_rows_deleted_diff = (int(mystat2['Innodb_rows_deleted']) - int(mystat1['Innodb_rows_deleted'])) / interval
    innodb_rows_read_diff = (int(mystat2['Innodb_rows_read']) - int(mystat1['Innodb_rows_read'])) / interval
    innodb_bp_pages_flushed_diff = (int(mystat2['Innodb_buffer_pool_pages_flushed']) - int(
        mystat1['Innodb_buffer_pool_pages_flushed'])) / interval
    innodb_data_reads_diff = (int(mystat2['Innodb_data_reads']) - int(mystat1['Innodb_data_reads'])) / interval
    innodb_data_writes_diff = (int(mystat2['Innodb_data_writes']) - int(mystat1['Innodb_data_writes'])) / interval
    innodb_data_read_diff = (int(mystat2['Innodb_data_read']) - int(mystat1['Innodb_data_read'])) / interval
    innodb_data_written_diff = (int(mystat2['Innodb_data_written']) - int(mystat1['Innodb_data_written'])) / interval
    innodb_os_log_fsyncs_diff = (int(mystat2['Innodb_os_log_fsyncs']) - int(mystat1['Innodb_os_log_fsyncs'])) / interval
    innodb_os_log_written_diff = (int(mystat2['Innodb_os_log_written']) - int(mystat1['Innodb_os_log_written'])) / interval
    threads_created_diff = (int(mystat2['Threads_created']) - int(mystat1['Threads_created'])) / interval
    bytes_received_diff = (int(mystat2['Bytes_received']) - int(mystat1['Bytes_received'])) / interval
    bytes_sent_diff = (int(mystat2['Bytes_sent']) - int(mystat1['Bytes_sent'])) / interval
    data = {}
    # -QPS- -TPS-
    data['ins'] = insert_diff
    data['upd'] = update_diff
    data['del'] = delete_diff
    data['sel'] = select_diff
    data['iud'] = insert_diff + update_diff + delete_diff
    # -Hit%-
    data['lor'] = read_request
    if read_request:
        hit = (read_request - read) / read_request * 100
        data['hit'] = round(hit, 2)
    else:
        hit = 100.00
        data['hit'] = hit
    # -innodb rows status-
    data['innodb_rows_inserted_diff'] = innodb_rows_inserted_diff
    data['innodb_rows_updated_diff'] = innodb_rows_updated_diff
    data['innodb_rows_deleted_diff'] = innodb_rows_deleted_diff
    data['innodb_rows_read_diff'] = innodb_rows_read_diff
    # -innodb bp pages status-
    data['data'] = mystat2['Innodb_buffer_pool_pages_data']
    data['free'] = mystat2['Innodb_buffer_pool_pages_free']
    data['dirty'] = mystat2['Innodb_buffer_pool_pages_dirty']
    data['flush'] = innodb_bp_pages_flushed_diff
    # -innodb data status-
    data['reads'] = innodb_data_reads_diff
    data['writes'] = innodb_data_writes_diff
    if (innodb_data_read_diff / 1024 / 1024) > 1:
        data['readed'] = str(innodb_data_read_diff / 1024 / 1024) + 'm'
    elif (innodb_data_read_diff / 1024) > 1:
        data['readed'] = str((innodb_data_read_diff / 1024) + 0.5) + 'k'
    else:
        data['readed'] = str(innodb_data_read_diff)
    if (innodb_data_written_diff / 1024 / 1024) > 1:
        data['written'] = str(round(innodb_data_written_diff / 1024 / 1024, 2)) + 'm'
    elif (innodb_data_written_diff / 1024) > 1:
        data['written'] = str(round((innodb_data_written_diff / 1024) + 0.5, 2)) + 'k'
    else:
        data['written'] = str(innodb_data_written_diff)
    # --innodb log--
    data['innodb_os_log_fsyncs_diff'] = innodb_os_log_fsyncs_diff
    if (innodb_os_log_written_diff / 1024 / 1024) > 1:
        data['innodb_os_log_written_diff'] = str(round(innodb_os_log_written_diff / 1024 / 1024, 2)) + 'm'
    elif (innodb_data_written_diff / 1024) > 1:
        data['innodb_os_log_written_diff'] = str(round((innodb_os_log_written_diff / 1024) + 0.5, 2)) + 'k'
    else:
        data['innodb_os_log_written_diff'] = str(innodb_os_log_written_diff)

    # his - -log(byte) - -  read - -query - -
    def get_innodb_status(con):
        sql = 'show engine innodb status'
        cursor = con.cursor()
        cursor.execute(sql)
        res = cursor.fetchone()
        result = res[2].split('\n')
        innodb_status = {}
        for i in result:
            try:
                if i.index("History list length") == 0:
                    r = re.compile("\s+")
                    rel = r.split(i)
                    innodb_status['history_list'] = rel[-1]
                    # print  innodb_status
            except Exception as e:
                # print e
                pass
            try:
                if i.index("Log sequence number") == 0:
                    r = re.compile("\s+")
                    rel = r.split(i)
                    innodb_status['log_bytes_written'] = rel[-1]
            except Exception as e:
                pass
            try:
                if i.index("Log flushed up to") == 0:
                    r = re.compile("\s+")
                    rel = r.split(i)
                    innodb_status['log_bytes_flushed'] = rel[-1]
            except Exception as e:
                pass
            try:
                if i.index("Last checkpoint at") == 0:
                    r = re.compile("\s+")
                    rel = r.split(i)
                    innodb_status['last_checkpoint'] = rel[-1]
            except Exception as e:
                pass

            try:
                if i.index("queries inside InnoDB") == 2:
                    # print i
                    r = re.compile("\s+")
                    rel = r.split(i)
                    innodb_status['queries_inside'] = rel[0]
                    innodb_status['queries_queued'] = rel[4]
            except Exception as e:
                pass

            try:
                if i.index("read views open inside InnoDB") == 2:
                    # print i
                    r = re.compile("\s+")
                    rel = r.split(i)
                    # print rel
                    innodb_status['read_views'] = rel[0]
            except Exception as e:
                pass

        innodb_status["unflushed_log"] = int(innodb_status['log_bytes_written']) - int(innodb_status['log_bytes_flushed'])
        innodb_status["uncheckpointed_bytes"] = int(innodb_status['log_bytes_written']) - int(innodb_status['last_checkpoint'])
        return innodb_status

    innodb_status = get_innodb_status(con)
    innodb_status['history_list'] = innodb_status['history_list']
    data['list'] = innodb_status['history_list']
    if (int(innodb_status['unflushed_log']) / 1024 / 1024) > 1:
        innodb_status['unflushed_log'] = int(innodb_status['unflushed_log']) / 1024 / 1024
        data['uflush'] = str(round(innodb_status['unflushed_log'], 2)) + 'm'
    elif (int(innodb_status["unflushed_log"]) / 1024) > 1:
        innodb_status['unflushed_log'] = str(int(innodb_status['unflushed_log']) / 1024 + 0.5)
        data['uflush'] = str(innodb_status['unflushed_log']) + 'k'
    else:
        data['uflush'] = innodb_status['unflushed_log']
    if (int(innodb_status['uncheckpointed_bytes']) / 1024 / 1024) > 1:
        innodb_status['uncheckpointed_bytes'] = round(int(innodb_status['uncheckpointed_bytes']) / 1024 / 1024, 2)
        data['uckpt'] = "{}m".format(innodb_status['uncheckpointed_bytes'])
    elif (int(innodb_status['uncheckpointed_bytes']) / 1024) > 1:
        innodb_status['uncheckpointed_bytes'] = round(int(innodb_status['uncheckpointed_bytes']) / 1024 + 0.5, 2)
        data['uckpt'] = "{}k".format(innodb_status['uncheckpointed_bytes'])
    else:
        innodb_status['uncheckpointed_bytes'] = str(innodb_status['uncheckpointed_bytes'])
        data['uckpt'] = innodb_status['uncheckpointed_bytes']
    data['view'] = innodb_status.get('read_views')
    data['inside'] = innodb_status['queries_inside']
    data['que'] = innodb_status['queries_queued']
    # --threads--
    data['run'] = mystat2['Threads_running']
    data['con'] = mystat2['Threads_connected']
    data['cre'] = threads_created_diff
    data['cac'] = mystat2['Threads_cached']
    # --bytes--
    if (bytes_received_diff / 1024 / 1024) > 1:
        data['recv'] = str(round(bytes_received_diff / 1024 / 1024, 2)) + 'm'
    elif (bytes_received_diff / 1024) > 1:
        data['recv'] = str(round(bytes_received_diff / 1024 + 0.5, 2)) + 'k'
    else:
        data['recv'] = str(bytes_received_diff)
    if (bytes_sent_diff / 1024 / 1024) > 1:
        data['send'] = str(round(bytes_sent_diff / 1024 / 1024, 2)) + 'm'
    elif (bytes_sent_diff / 1024) > 1:
        data['send'] = str(round(bytes_sent_diff / 1024 + 0.5, 2)) + 'k'
    else:
        data['send'] = str(bytes_sent_diff)
    data["time"] = time.strftime("%T")
    return {'data': data, 'msg': 'success'}
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))


def processlist(db: Session, Processlist: schemas.Processlist):
    try:
        ins = db.query(Instance).filter(Instance.id == Processlist.id).first()
        base_sql = "select `id`, `user`, `host`, `db`, `command`, `time`, `state`, ifnull(info,'') as info from information_schema.processlist where 1=1 "
        command_type = Processlist.command_type
        if command_type == 'All':
            base_sql += " "
        elif command_type == 'Not Sleep':
            base_sql += " and `command`<>'Sleep' "
        else:
            base_sql += " and  `command`= '{}' ".format(command_type)
        if Processlist.database:
            base_sql += " and db='{}' ".format(Processlist.database)
        base_sql += " order by `time` desc"
        print(base_sql)
        data = exec_distal_sql_dict(base_sql, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def kill_session(db: Session, Kill_session: schemas.Kill_session):
    try:
        ins = db.query(Instance).filter(Instance.id == Kill_session.id).first()
        sql = "kill {}".format(Kill_session.threadID)
        data = exec_distal_sql(sql, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        # raise HTTPException(status_code=500, detail=str(e))
        return {'data': '', 'msg': str(e)}


def tablesapce(db: Session, Tablesapce: schemas.Dbid):
    try:
        ins = db.query(Instance).filter(Instance.id == Tablesapce.id).first()
        sql = """
        SELECT
          table_schema AS table_schema,
          table_name AS table_name,
          engine AS engine,
          TRUNCATE((data_length+index_length+data_free)/1024/1024,2) AS total_size,
          table_rows AS table_rows,
          TRUNCATE(data_length/1024/1024,2) AS data_size,
          TRUNCATE(index_length/1024/1024,2) AS index_size,
          TRUNCATE(data_free/1024/1024,2) AS data_free,
          TRUNCATE(data_free/(data_length+index_length+data_free)*100,2) AS pct_free
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'test', 'sys')
          ORDER BY total_size DESC 
        LIMIT 14;
        """
        data = exec_distal_sql_dict(sql, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def innodb_trx(db: Session, Innodb_trx: schemas.Dbid):
    try:
        ins = db.query(Instance).filter(Instance.id == Innodb_trx.id).first()
        sql = """
        select 
        trx.trx_id,
       trx.trx_started,
       trx.trx_state,
       trx.trx_operation_state,
       trx.trx_mysql_thread_id,
       trx.trx_tables_locked,
       trx.trx_rows_locked,
       trx.trx_rows_modified,
       trx.trx_is_read_only,
       trx.trx_isolation_level,
      p.user,
      p.host,
      p.db,
      TO_SECONDS(NOW()) - TO_SECONDS(trx.trx_started) trx_idle_time,
      p.time thread_time,
      IFNULL((SELECT
       GROUP_CONCAT(t1.sql_text SEPARATOR ';
      ')
    FROM performance_schema.events_statements_history t1
      INNER JOIN performance_schema.threads t2
        ON t1.thread_id = t2.thread_id
    WHERE t2.PROCESSLIST_ID = p.id), '') info
FROM information_schema.INNODB_TRX trx
  INNER JOIN information_schema.PROCESSLIST p
    ON trx.trx_mysql_thread_id = p.id
    WHERE trx.trx_state = 'RUNNING'
    AND p.COMMAND = 'Sleep'
    /*AND P.time > 3 */
    ORDER BY trx.trx_started ASC;
        """
        data = exec_distal_sql_dict(sql, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def trxandlocks(db: Session, Trxandlocks: schemas.Dbid):
    try:
        ins = db.query(Instance).filter(Instance.id == Trxandlocks.id).first()
        sql = """
 SELECT
              rtrx.`trx_state`                                                        AS "等待的状态",
              rtrx.`trx_started`                                                      AS "等待事务开始时间",
              rtrx.`trx_wait_started`                                                 AS "等待事务等待开始时间",
              lw.`requesting_trx_id`                                                  AS "等待事务ID",
              rtrx.trx_mysql_thread_id                                                AS "等待事务线程ID",
              rtrx.`trx_query`                                                        AS "等待事务的sql",
              CONCAT(rl.`lock_mode`, '-', rl.`lock_table`, '(', rl.`lock_index`, ')') AS "等待的表信息",
              rl.`lock_id`                                                            AS "等待的锁id",
              lw.`blocking_trx_id`                                                    AS "运行的事务id",
              trx.trx_mysql_thread_id                                                 AS "运行的事务线程id",
              CONCAT(l.`lock_mode`, '-', l.`lock_table`, '(', l.`lock_index`, ')')    AS "运行的表信息",
              l.lock_id                                                               AS "运行的锁id",
              trx.`trx_state`                                                         AS "运行事务的状态",
              trx.`trx_started`                                                       AS "运行事务的时间",
              trx.`trx_wait_started`                                                  AS "运行事务的等待开始时间",
              trx.`trx_query`                                                         AS "运行事务的sql"
            FROM information_schema.`INNODB_LOCKS` rl
              , information_schema.`INNODB_LOCKS` l
              , information_schema.`INNODB_LOCK_WAITS` lw
              , information_schema.`INNODB_TRX` rtrx
              , information_schema.`INNODB_TRX` trx
            WHERE rl.`lock_id` = lw.`requested_lock_id`
                  AND l.`lock_id` = lw.`blocking_lock_id`
                  AND lw.requesting_trx_id = rtrx.trx_id
                  AND lw.blocking_trx_id = trx.trx_id;
        """
        data = exec_distal_sql_dict(sql, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def instance_user_list(db: Session, Instance_user_list: schemas.Dbid):
    try:
        ins = db.query(Instance).filter(Instance.id == Instance_user_list.id).first()
        sql = "select concat('`', user, '`', '@', '`', host,'`') as query,user,host from mysql.user;"
        conn = pymysql.connect(user=ins.user, password=de_pwd(ins.password), host=ins.host, port=ins.port, database='mysql')
        cursor = conn.cursor()  # 拿到游标，即mysql >
        cursor.execute(sql)
        data = cursor.fetchall()
        # data = exec_distal_sql_dict(sql, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        datali = []
        for i in data:
            query = i[0]
            sql1 = "show grants for {};".format(query)
            cursor.execute(sql1)
            data1 = cursor.fetchall()
            # data1 = exec_distal_sql(sql1, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
            datali.append({"user_host": query, "privileges": data1})
        cursor.close()
        conn.close()
        return {'data': datali, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def grant(db: Session, Grant: schemas.Grant):
    try:
        instance_id = Grant.instance_id
        user_host = Grant.user_host
        priv_type = Grant.priv_type
        privs = Grant.privs
        grant_sql = ''
        ins = db.query(Instance).filter(Instance.id == instance_id).first()
        # 全局权限
        if priv_type == 0:
            global_privs = privs['global_privs']
            if not all([global_privs]):
                return {'msg': '信息不完整，请确认后提交', 'data': []}
            if 'GRANT' in global_privs:
                global_privs.remove('GRANT')
                grant_sql = f"GRANT {','.join(global_privs)} ON *.* TO {user_host} WITH GRANT OPTION;"
            else:
                grant_sql = f"GRANT {','.join(global_privs)} ON *.* TO {user_host};"
        # 库权限
        elif priv_type == 1:
            db_privs = privs['db_privs']
            db_name = Grant.db_name
            if not all([db_privs, db_name]):
                return {'msg': '信息不完整，请确认后提交', 'data': []}
            for db in db_name:
                if 'GRANT' in db_privs:
                    db_privs.remove('GRANT')
                    grant_sql += f"GRANT {','.join(db_privs)} ON `{db}`.* TO {user_host} WITH GRANT OPTION;"
                else:
                    grant_sql += f"GRANT {','.join(db_privs)} ON `{db}`.* TO {user_host};"
            # 表权限
        elif priv_type == 2:
            tb_privs = privs['tb_privs']
            db_name = Grant.db_name[0]
            tb_name = Grant.tb_name
            if not all([tb_privs, db_name, tb_name]):
                return {'msg': '信息不完整，请确认后提交', 'data': []}
            for tb in tb_name:
                if 'GRANT' in tb_privs:
                    tb_privs.remove('GRANT')
                    grant_sql += f"GRANT {','.join(tb_privs)} ON `{db_name}`.`{tb}` TO {user_host} WITH GRANT OPTION;"
                else:
                    grant_sql += f"GRANT {','.join(tb_privs)} ON `{db_name}`.`{tb}` TO {user_host};"
        data = ''
        for isql in grant_sql.split(';'):
            if isql.strip():
                data = exec_distal_sql(isql, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        return {'data': None, 'msg': str(e)}
        # raise HTTPException(status_code=500, detail=str(e))


def revoke(db: Session, Revoke: schemas.Revoke):
    try:
        ins = db.query(Instance).filter(Instance.id == Revoke.instance_id).first()
        sql = Revoke.grant_sql.replace("GRANT", " revoke ", 1).replace("TO", " from ", 1)
        if "WITH GRANT OPTION" in sql:
            sql = sql.replace("WITH GRANT OPTION", '')
            sqlli = sql.split()
            sql1 = "revoke  GRANT OPTION ON {}  from  {}  ;".format(sqlli[-3], sqlli[-1])
            data = exec_distal_sql(sql1, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        data = exec_distal_sql(sql, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        return {'data': '', 'msg': str(e)}
        # raise HTTPException(status_code=500, detail=str(e))


def instance_user_delete(db: Session, Instance_user_delete: schemas.Instance_user_delete):
    try:
        ins = db.query(Instance).filter(Instance.id == Instance_user_delete.instance_id).first()
        sql = "DROP USER {};".format(Instance_user_delete.user_host)
        data = exec_distal_sql(sql, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        return {'data': '', 'msg': str(e)}
        # raise HTTPException(status_code=500, detail=str(e))


def instance_user_create(db: Session, Instance_user_create: schemas.Instance_user_create):
    try:
        if Instance_user_create.password1 != Instance_user_create.password2:
            return {'msg': '两次输入密码不一致', 'data': []}
        ins = db.query(Instance).filter(Instance.id == Instance_user_create.instance_id).first()
        hosts = Instance_user_create.host.split("|")
        create_user_cmd = ''
        data = ''
        for host in hosts:
            create_user_cmd += f"create user '{Instance_user_create.user}'@'{host}' identified by '{Instance_user_create.password1}';"
            data = exec_distal_sql(create_user_cmd, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        return {'data': '', 'msg': str(e)}
        # raise HTTPException(status_code=500, detail=str(e))


def instance_user_reset_pwd(db: Session, Instance_user_reset_pwd: schemas.Instance_user_reset_pwd):
    try:
        ins = db.query(Instance).filter(Instance.id == Instance_user_reset_pwd.instance_id).first()
        user_host = Instance_user_reset_pwd.user_host
        reset_pwd1 = Instance_user_reset_pwd.password1
        reset_pwd2 = Instance_user_reset_pwd.password2
        if reset_pwd1 != reset_pwd2:
            return {'msg': '两次输入密码不一致', 'data': []}
        sql = f"ALTER USER {user_host} IDENTIFIED BY '{reset_pwd1}';"
        data = exec_distal_sql(sql, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        return {'data': '', 'msg': str(e)}


def show_variables(db: Session, Show_variables: schemas.Show_variables):
    try:
        ins = db.query(Instance).filter(Instance.id == Show_variables.instance_id).first()
        sql = """show variables like "%{}%" ;""".format(Show_variables.value)
        data = exec_distal_sql_dict(sql, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        return {'data': '', 'msg': str(e)}


def set_global(db: Session, Set_global: schemas.Set_global):
    try:
        ins = db.query(Instance).filter(Instance.id == Set_global.instance_id).first()
        try:
            int(Set_global.value)
            sql = "SET GLOBAL {} = {} ;".format(Set_global.variable_name, Set_global.value)
        except:
            sql = "SET GLOBAL {} = '{}' ;".format(Set_global.variable_name, Set_global.value)
        data = exec_distal_sql(sql, ins.user, de_pwd(ins.password), ins.host, ins.port, 'mysql')
        return {'data': data, 'msg': 'success'}
    except Exception as e:
        return {'data': '', 'msg': str(e)}
