from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from database.config import localsession
from apps.user.user import valid_token
from apps.user.schemas import UserOut
from . import schemas, crud

wkod = APIRouter()


def get_db():
    try:
        db = localsession()
        yield db
    finally:
        db.close()


@wkod.get('/workorder/')
def workorder(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), offset: int = Query(...), limit: int = Query(...)):
    return crud.workorder(db, user, offset, limit)


@wkod.get('/sql_list/{id}/')
def sql_list(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), offset: int = Query(...), limit: int = Query(...),
             id: int = Path(...)):
    return crud.sql_list(db, user, offset, limit, id)


@wkod.get('/pending/')
def pending_wo(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), offset: int = Query(...), limit: int = Query(...)):
    return crud.pending_wo(db, user, offset, limit)


@wkod.post('/sqlrecord/{id}/')
def update_sqlrecord(*, db: Session = Depends(get_db), id: int = Path(...), user: UserOut = Depends(valid_token), remark: str):
    return crud.update_sqlrecord(db, id, user, remark)


@wkod.post('/execsql/{id}/')
def execsql(db: Session = Depends(get_db), id: int = Path(...), user: UserOut = Depends(valid_token)):
    return crud.commit_workorder(db, id, user)


@wkod.post('/execsql_all/{id}/')
def execsql(db: Session = Depends(get_db), id: int = Path(...), user: UserOut = Depends(valid_token)):
    return crud.commit_workorder_all(db, id, user)


@wkod.get('/historyorder/')
def historyorder(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), offset: int = Query(...), limit: int = Query(...),
                 start_time: str = '', end_time: str = '', is_check: int = 0, sponsor: str = '', host: str = '', dbname: str = ''):
    return crud.history_order(db, user, offset, limit, start_time, end_time, is_check, sponsor, host, dbname)


@wkod.post('/order_mark_check/{id}/')
def order_mark_check(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), id: int = Path(...)):
    return crud.order_mark_check(db, user, id)


@wkod.post('/data_export_order_mark_check/{id}/')
def data_export_order_mark_check(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), id: int = Path(...)):
    return crud.data_export_order_mark_check(db, user, id)


@wkod.post('/rollbacksql/{id}/')
def rollback_sql(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), id: int = Path(...)):
    return crud.rollback_sql(db, user, id)


@wkod.post('/get_rollbacksql/{id}/')
def get_rollbacksql(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), id: int = Path(...)):
    return crud.get_rollbacksql(db, user, id)


@wkod.get('/download_rollbacksql/{id}/')
def download_rollbacksql(db: Session = Depends(get_db), id: int = Path(...)):
    return crud.download_rollbacksql(db, id)


@wkod.get('/get_osc/')
def get_osc(db: Session = Depends(get_db), user: UserOut = Depends(valid_token)):
    return crud.get_osc(db, user)


@wkod.post('/pause_osc/')
def pause_osc(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), osc: schemas.Osc = (...)):
    return crud.pause_osc(db, user, osc)


@wkod.post('/resume_osc/')
def resume_osc(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), osc: schemas.Osc = (...)):
    return crud.resume_osc(db, user, osc)


@wkod.post('/kill_osc/')
def kill_osc(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), osc: schemas.Osc = (...)):
    return crud.kill_osc(db, user, osc)


@wkod.get('/data_export_pending/')
def data_export_pending(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), offset: int = Query(...), limit: int = Query(...)):
    return crud.data_export_pending(db, user, offset, limit)


@wkod.post('/mod_data_export_status/')
def mod_data_export_status(db: Session = Depends(get_db), user: UserOut = Depends(valid_token),
                           data_export_status: schemas.Mod_data_export_status = ...):
    return crud.mod_data_export_status(db, user, data_export_status)


@wkod.get('/workorder_data_export/')
def workorder_data_export(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), offset: int = Query(...), limit: int = Query(...)):
    return crud.workorder_data_export(db, user, offset, limit)


@wkod.get('/historyorder_data_export/')
def historyorder_data_export(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), offset: int = Query(...), limit: int = Query(...),
                             start_time: str = '', end_time: str = '', is_check: int = 0, sponsor: str = '', host: str = '', dbname: str = ''):
    return crud.historyorder_data_export(db, user, offset, limit, start_time, end_time, is_check, sponsor, host, dbname)
