from fastapi import APIRouter, Depends, Query, HTTPException
from database.config import localsession
from sqlalchemy.orm import Session
from apps.user.user import get_user_role
from . import crud, schemas
from apps.user.user import valid_token
from apps.user.schemas import UserOut

ins = APIRouter()


def get_db():
    try:
        db = localsession()
        yield db
    finally:
        db.close()


# 权限验证
def validate_pri(role: str = Depends(get_user_role)):
    if role in ('admin', 'DBA'):
        return True
    else:
        raise HTTPException(status_code=403, detail='权限拒绝')


def valid_pri(user: UserOut = Depends(valid_token)):
    try:
        return
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@ins.get('/instance/', response_model=schemas.DataOut)
def get_instance(user: UserOut = Depends(valid_token), db: Session = Depends(get_db), id: int = None, ins_name: str = None,
                 page: int = 1, limit: int = None):
    if id:
        return crud.get_instance_by_id(db, id)
    if ins_name:
        return crud.get_instances_by_ins_name(db, ins_name, offset=page, limit=limit)
    return crud.get_instances(db=db, offset=page, limit=limit)


@ins.post('/instance/')
def add_instance(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), ins: schemas.InsIn):
    return crud.add_instance(db, ins)


@ins.delete('/instance/')
def del_instance(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), id: int = Query(...)):
    return crud.del_instance(db, id)


@ins.patch('/instance/')
def update_instance(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), ins: schemas.InsUpdate):
    return crud.update_instance(db, ins)


@ins.post('/concheck/')
def concheck(*, pri: bool = Depends(validate_pri), ins: schemas.InsIn):
    return crud.concheck(ins)


@ins.post('/concheck2/')
def concheck2(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), id: int):
    return crud.concheck2(db, id)


@ins.get('/binlog_list/')
def get_binlog_list(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), id: int):
    return crud.get_binlog_list(db, id)


@ins.post('/del_binlog/')
def del_binlog(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Del_binlog: schemas.Del_binlog):
    return crud.del_binlog(db, Del_binlog)


@ins.get('/instance_monitor/')
def instance_monitor(*, pri: bool = Depends(valid_token), db: Session = Depends(get_db), id: int = Query(...)):
    return crud.instance_monitor(db, id)


@ins.post('/processlist/')
def processlist(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Processlist: schemas.Processlist):
    return crud.processlist(db, Processlist)


@ins.post('/kill_session/')
def kill_session(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Kill_session: schemas.Kill_session):
    return crud.kill_session(db, Kill_session)


# top表空间
@ins.post('/tablesapce/')
def tablesapce(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Tablesapce: schemas.Dbid):
    return crud.tablesapce(db, Tablesapce)


# 事务信息
@ins.post('/innodb_trx/')
def innodb_trx(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Innodb_trx: schemas.Dbid):
    return crud.innodb_trx(db, Innodb_trx)


# 锁信息
@ins.post('/trxandlocks/')
def trxandlocks(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Trxandlocks: schemas.Dbid):
    return crud.trxandlocks(db, Trxandlocks)


# instance/user/list  实例用户列表
@ins.post('/instance_user_list/')
def instance_user_list(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Instance_user_list: schemas.Dbid):
    return crud.instance_user_list(db, Instance_user_list)


# 授权变更
@ins.post('/grant/')
def grant(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Grant: schemas.Grant):
    return crud.grant(db, Grant)


# revoke
@ins.post('/revoke/')
def revoke(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Revoke: schemas.Revoke):
    return crud.revoke(db, Revoke)


# instance/user/delete/ 实例用户删除
@ins.post('/instance_user_delete/')
def instance_user_delete(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Instance_user_delete: schemas.Instance_user_delete):
    return crud.instance_user_delete(db, Instance_user_delete)


# instance/user/create/ 实例用户创建
@ins.post('/instance_user_create/')
def instance_user_create(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Instance_user_create: schemas.Instance_user_create):
    return crud.instance_user_create(db, Instance_user_create)


# instance/user/reset_pwd/ 实例用户改密
@ins.post('/instance_user_reset_pwd/')
def instance_user_reset_pwd(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db),
                            Instance_user_reset_pwd: schemas.Instance_user_reset_pwd):
    return crud.instance_user_reset_pwd(db, Instance_user_reset_pwd)


# show_variables
@ins.post('/show_variables/')
def show_variables(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Show_variables: schemas.Show_variables):
    return crud.show_variables(db, Show_variables)


# set_global_variables
@ins.post('/set_global/')
def set_global(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), Set_global: schemas.Set_global):
    return crud.set_global(db, Set_global)
