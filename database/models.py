from sqlalchemy import Column, String, Enum, Integer, DateTime, ForeignKey, UniqueConstraint, TEXT, BIGINT
import datetime
from .config import Base
import pytz


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, autoincrement=True, primary_key=True)
    username = Column(String(32), unique=True, index=True)
    email = Column(String(100))
    password = Column(String(64))
    status = Column(Enum('正常', '锁定'))
    role_id = Column(Integer)


class Role(Base):
    __tablename__ = 'roles'
    __table_args__ = (
        UniqueConstraint('role', 'department'),
    )
    id = Column(Integer, autoincrement=True, primary_key=True)
    role = Column(Enum('admin', 'DBA', '主管', '员工'))
    department = Column(String(32))

    # role_priv            =relationship('Privilege',back_populates='role')


class Privilege(Base):
    __tablename__ = 'privilege'
    id = Column(Integer, autoincrement=True, primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'))
    instance_id = Column(Integer, ForeignKey('instance.id'))
    privileges = Column(String(64))

    # role            =relationship('Role',back_populates='role_priv')
    # instance        =relationship('instance',back_populates='ins_priv')


class Instance(Base):
    __tablename__ = 'instance'
    id = Column(Integer, autoincrement=True, primary_key=True)
    ins_name = Column(String(32), unique=True)
    type = Column(Enum('master', 'slave'))
    host = Column(String(16))
    port = Column(Integer)
    user = Column(String(32))
    password = Column(String(32))
    db_type = Column(Enum('mysql', 'cassandra', 'pgsql', 'mongodb', 'redis'))
    # ins_priv            =relationship('Privilege',back_populates='instance')


class Workorder(Base):
    __tablename__ = 'workorder'
    id = Column(Integer, autoincrement=True, primary_key=True)
    sponsor = Column(Integer, ForeignKey('users.id'))
    approver_manager = Column(Integer, ForeignKey('users.id'))
    approver_dba = Column(Integer, ForeignKey('users.id'))
    instance_id = Column(Integer, ForeignKey('instance.id'))
    dbname = Column(String(32))
    remark = Column(String(255))
    is_check = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")))
    end_time = Column(DateTime, default=datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")))


class Sqlrecord(Base):
    __tablename__ = 'sqlrecord'
    id = Column(Integer, autoincrement=True, primary_key=True)
    content = Column(TEXT)
    status_code = Column(Integer)
    approved = Column(Integer)
    remark = Column(TEXT)
    sequence = Column(String(50))
    affected_rows = Column(String(50))
    execute_time = Column(String(50))
    backup_dbname = Column(String(50))
    wkodid = Column(Integer, ForeignKey('workorder.id'))


class Workorder_data_export(Base):
    __tablename__ = 'workorder_data_export'
    id = Column(Integer, autoincrement=True, primary_key=True)
    sponsor = Column(Integer, ForeignKey('users.id'))
    approver_manager = Column(Integer, ForeignKey('users.id'))
    approver_dba = Column(Integer, ForeignKey('users.id'))
    instance_id = Column(Integer, ForeignKey('instance.id'))
    dbname = Column(String(32))
    sql = Column(TEXT)
    status = Column(Integer)
    path = Column(String(255))
    remark = Column(String(255))
    is_check = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")))
    approve_time = Column(DateTime, default=datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")))
    download_time = Column(DateTime, default=datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")))
    end_time = Column(DateTime, default=datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")))


class Desensitization_info(Base):
    __tablename__ = 'desensitization_info'
    id = Column(Integer, autoincrement=True, primary_key=True)
    instance_id = Column(Integer, ForeignKey('instance.id'))
    dbname = Column(String(32))
    field = Column(String(32))


class Slowlogs(Base):
    __tablename__ = 'slowlogs'
    id = Column(BIGINT, autoincrement=True, primary_key=True)
    dbid = Column(Integer, nullable=False)
    db_user = Column(String(30), nullable=False)
    app_ip = Column(String(30), nullable=False)
    thread_id = Column(Integer, nullable=False)
    exec_duration = Column(String(30), nullable=False)
    rows_sent = Column(Integer, nullable=False)
    rows_examined = Column(Integer, nullable=False)
    start_time = Column(Integer, nullable=False)
    sql_pattern = Column(TEXT, nullable=False)
    orig_sql = Column(TEXT, nullable=False)
    fingerprint = Column(String(50), nullable=False)
    create_time = Column(DateTime, default=datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")))


class Query_log(Base):
    __tablename__ = 'query_log'
    id = Column(BIGINT, autoincrement=True, primary_key=True)
    sponsor = Column(Integer, ForeignKey('users.id'))
    instance_id = Column(Integer, ForeignKey('instance.id'))
    dbname = Column(String(32))
    sql = Column(TEXT)
    create_time = Column(DateTime, default=datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")))


class Exec_shell_log(Base):
    __tablename__ = 'exec_shell_log'
    id = Column(BIGINT, autoincrement=True, primary_key=True)
    log_name = Column(String(32))
    cmd = Column(TEXT)
    create_time = Column(DateTime, default=datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")))
