from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.config import localsession
from . import crud, schemas
from apps.user.user import valid_token
from apps.user.schemas import UserOut

que = APIRouter()


def get_db():
    try:
        db = localsession()
        yield db
    finally:
        db.close()


def valid_pri(user: UserOut = Depends(valid_token)):
    try:
        return
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@que.get('/get_ins/')
def get_ins(*, db: Session = Depends(get_db), user=Depends(valid_token)):
    return crud.get_ins(db, user)


@que.get('/get_schema/')
def get_schema(*, db: Session = Depends(get_db), id: int, user=Depends(valid_token)):
    return crud.get_schema(db, id)


@que.get('/get_table/')
def get_table(*, db: Session = Depends(get_db), id: int, dbname: str, user=Depends(valid_token)):
    return crud.get_table(db, id, dbname)


@que.get('/get_desc/')
def get_desc(*, db: Session = Depends(get_db), id: int, dbname: str, table: str, user=Depends(valid_token)):
    return crud.get_desc(db, id, dbname, table)


@que.post('/sqlscore/')
def sqlscore(*, db: Session = Depends(get_db), que: schemas.Query, user=Depends(valid_token)):
    return crud.sqlscore(db, que)


@que.post('/sqlexec/')
def sqlquery(*, db: Session = Depends(get_db), que: schemas.Query, user=Depends(valid_token)):
    return crud.sqlexec(db, que, user)


@que.post('/submit_workorder_data_export/')
def submit_workorder_data_export(*, db: Session = Depends(get_db), que: schemas.Submit_workorder_data_export, user=Depends(valid_token)):
    return crud.submit_workorder_data_export(db, que, user)


@que.get('/get_query_log')
def get_query_log(*, db: Session = Depends(get_db), user=Depends(valid_token), offset: int = 1, limit: int = 5, sponsor="", dbname="", start_time: str = '', end_time: str = ''):
    return crud.get_query_log(db, offset, limit, sponsor, dbname,start_time, end_time)


@que.get('/get_sales_order')
def get_sales_order(*, db: Session = Depends(get_db), user=Depends(valid_token), date_time):
    return crud.get_sales_order(db, date_time)


@que.post('/exec_shell/')
def exec_shell(*, db: Session = Depends(get_db), que: schemas.Exec_shell, user=Depends(valid_token)):
    return crud.exec_shell(db, que)


@que.get('/tail_exec_shell_log/')
def tail_exec_shell_log(*, db: Session = Depends(get_db), log_name, user=Depends(valid_token)):
    return crud.tail_exec_shell_log(db, log_name)


@que.get('/get_exec_shell_log_list/')
def get_exec_shell_log_list(*, db: Session = Depends(get_db), user=Depends(valid_token)):
    return crud.get_exec_shell_log_list(db, )
