from fastapi import APIRouter, Depends, Path, Query, Body
from sqlalchemy.orm import Session
from database.config import localsession
from apps.user.user import valid_token
from apps.user.schemas import UserOut
from . import schemas, crud

slowlog = APIRouter()


def get_db():
    try:
        db = localsession()
        yield db
    finally:
        db.close()


@slowlog.post('/slowlog')
def post_slowlog(db: Session = Depends(get_db), SlowLog: schemas.SlowLog = Body(..., example={"dbid": "1",
                                                                                              "db_user": " monitor",
                                                                                              "app_ip": "localhost",
                                                                                              "thread_id": 331578,
                                                                                              "exec_duration": "0.000441",
                                                                                              "rows_sent": 1,
                                                                                              "rows_examined": 154,
                                                                                              "start_time": 1583219343,
                                                                                              "orig_sql": "SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME =queries LIMIT 1;",
                                                                                              "sql_pattern": "SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME =? LIMIT ?;",
                                                                                              "fingerprint": "f97d833b6117df9487142b39b5454293"})):
    return crud.post_slowlog(db, SlowLog)


@slowlog.get('/get_slowlog')
def get_slowlog(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), offset: int = 1, limit: int = 5, dbid: int = 0,
                start_time: str = "", end_time: str = ""):
    return crud.get_slowlog(db, offset, limit, dbid, start_time, end_time)


@slowlog.get('/get_slowlog_count_top30')
def get_slowlog_count_top30(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), offset: int = 1, limit: int = 5, dbid: int = 0,
                            start_time: str = "", end_time: str = ""):
    return crud.get_slowlog_count_top30(db, offset, limit, dbid, start_time, end_time)


@slowlog.get('/get_slowlog_time_top30')
def get_slowlog_time_top30(db: Session = Depends(get_db), user: UserOut = Depends(valid_token), offset: int = 1, limit: int = 5, dbid: int = 0,
                           start_time: str = "", end_time: str = ""):
    return crud.get_slowlog_time_top30(db, offset, limit, dbid, start_time, end_time)
