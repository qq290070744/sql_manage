from fastapi import APIRouter, Depends, HTTPException
from database.config import localsession
from sqlalchemy.orm import Session
from apps.user.user import get_user_role
from . import schemas
from . import crud

role = APIRouter()


def get_db():
    try:
        db = localsession()
        yield db
    finally:
        db.close()


def validate_pri(role: str = Depends(get_user_role)):
    if role == 'admin':
        return True
    else:
        raise HTTPException(status_code=403, detail='权限拒绝')


@role.post('/role/')
def create_role(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), ins: schemas.RoleIn):
    return crud.create_role(db=db, ins=ins)


@role.get('/role/')
def get_role(pri: bool = Depends(validate_pri), db: Session = Depends(get_db), role: str = None, id: int = None, offset: int = 1, limit: int = 10000):
    return crud.get_role(db, offset, limit, role, id)


@role.delete('/role/')
def del_role(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), id: int):
    return crud.del_role(db, id)


@role.patch('/role/')
def update_role(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), ins: schemas.RoleOut):
    return crud.update_role(db, ins)


@role.get('/rights/')
def get_rights(pri: bool = Depends(validate_pri), db: Session = Depends(get_db)):
    return crud.get_pri(db)


@role.post('/rights/')
def add_pri(*, privilege: bool = Depends(validate_pri), db: Session = Depends(get_db), pri: schemas.Privilege):
    return crud.add_pri(db, pri)


@role.patch('/rights/')
def update_pri(*, privilege: bool = Depends(validate_pri), db: Session = Depends(get_db), pri_id: int, pri: str):
    return crud.update_pri(db, pri_id, pri)


@role.delete('/rights/')
def del_pri(*, privilege: bool = Depends(validate_pri), db: Session = Depends(get_db), pri_id: int):
    return crud.del_pri(db, pri_id)


@role.get('/partins/')
def get_partins(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), role_id: int):
    return crud.get_partins(db, role_id)
