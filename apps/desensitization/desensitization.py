from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.config import localsession
from . import crud, schemas
from apps.user.user import valid_token
from apps.user.schemas import UserOut

desensitization = APIRouter()


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


@desensitization.get('/get_desensitization_info_list/')
def get_desensitization_info_list(*, db: Session = Depends(get_db), user=Depends(valid_token), offset: int = 1, limit: int = None):
    return crud.get_desensitization_info_list(db, offset=offset, limit=limit)


@desensitization.post('/add_desensitization_info/')
def add_desensitization_info(*, db: Session = Depends(get_db), user=Depends(valid_token), desensitization_info: schemas.Add_desensitization_info):
    return crud.add_desensitization_info(db, desensitization_info, user, )


@desensitization.delete('/del_desensitization_info/{id}')
def del_desensitization_info(*, db: Session = Depends(get_db), user=Depends(valid_token), id: int):
    return crud.del_desensitization_info(db, id, user)
