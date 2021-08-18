from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.config import localsession
from . import schemas, crud
from apps.user.schemas import UserOut
from apps.user.user import valid_token
from apps.instance.schemas import DataOut

insp = APIRouter()


def get_db():
    try:
        db = localsession()
        yield (db)
    finally:
        db.close()


@insp.post('/inspect/')
def inspect(db: Session = Depends(get_db), query: schemas.Query = (...), user=Depends(valid_token)):
    return crud.inspect(db, query, user)


@insp.get('/get_master_ins/', response_model=DataOut)
def get_master_ins(db: Session = Depends(get_db), user=Depends(valid_token)):
    return crud.get_master_ins(db, user)


@insp.get('/get_approver/', response_model=schemas.resOut)
def get_approver(db: Session = Depends(get_db), user: UserOut = Depends(valid_token)):
    return crud.get_approver(db, user)


@insp.get('/get_approver_data_export/', response_model=schemas.resOut)
def get_approver_data_export(db: Session = Depends(get_db), user: UserOut = Depends(valid_token)):
    return crud.get_approver_data_export(db, user)


@insp.post('/alter_merge/')
def alter_merge(db: Session = Depends(get_db), query: schemas.alter_merge_sql = ...):
    return crud.alter_merge(db, query)
