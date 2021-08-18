from fastapi import APIRouter, Depends, HTTPException, Header
from database.config import localsession
from sqlalchemy.orm import Session
from . import crud, schemas

from utils.make_pwd import make_pwd

from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jwt import encode, decode, PyJWTError
from database import models, config

# models.Base.metadata.create_all(bind=config.engine)

usr = APIRouter()

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oa2_auth = OAuth2PasswordBearer(tokenUrl='/token/')

SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 * 30  # 1440分钟等于一天


def get_db():
    try:
        db = localsession()
        yield db
    finally:
        db.close()


# 验证token
def valid_token(Authorization: str = Header(...), db: Session = Depends(get_db)):
    try:
        jwt_de = decode(Authorization, SECRET_KEY, ALGORITHM)
        username = jwt_de.get('sub')
        user = crud.get_user(db, username)
        if not user:
            raise HTTPException(status_code=401, detail='用户不存在')
        return user
    except PyJWTError:
        raise HTTPException(status_code=401, detail='token无效')


# 获取用户角色
def get_user_role(db: Session = Depends(get_db), user: schemas.UserOut = Depends(valid_token)):
    return crud.get_user_role(db=db, user=user)


# 验证权限
def validate_pri(role: str = Depends(get_user_role)):
    if role in ['admin', 'DBA']:
        return True
    else:
        raise HTTPException(status_code=403, detail='权限拒绝')


# 验证用户名、密码
def auth_user(db: Session, username: str, password: str, ):
    try:
        user = crud.get_user(db, username)
        if user and pwd_context.verify(password, user.password):
            return True
        return False
    except Exception as e:
        raise HTTPException(status_code=405, detail=str(e))


@usr.post('/token/', response_model=schemas.Token)
def create_token(username: str, form: OAuth2PasswordRequestForm = Depends()):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data = {'sub': username, 'exp': expire}
    token = encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return {'access_token': token, 'token_type': 'bearer'}


@usr.get('/user/')
def get_user(pri: bool = Depends(validate_pri), db: Session = Depends(get_db), user: str = None, offset: int = 1, limit: int = 5):
    return crud.get_users(db, offset, limit, user)


@usr.post('/user/')
def add_user(pri: bool = Depends(validate_pri), db: Session = Depends(get_db), user: schemas.UserIn = (...)):
    return crud.add_user(db=db, user=user)


@usr.patch('/user/')
def update_user(pri: bool = Depends(validate_pri), db: Session = Depends(get_db), user: schemas.UserUpdate = (...)):
    return crud.update_user(db=db, user=user)


@usr.delete('/user/')
def delete_user(*, pri: bool = Depends(validate_pri), db: Session = Depends(get_db), id: int):
    return crud.delete_user(db, id)


@usr.post('/pwd/')
def make_password():
    return {'data': make_pwd(), 'msg': 'success'}


@usr.post('/login/')
def login(db: Session = Depends(get_db), form: OAuth2PasswordRequestForm = Depends()):
    if auth_user(db, form.username, form.password):
        return create_token(form.username)
    return {'data': None, 'msg': 'error'}


@usr.post('/mod_password/')
def mod_password(db: Session = Depends(get_db), user: schemas.UserOut = Depends(valid_token),
                 user_update: schemas.Mod_password = ...):
    if not auth_user(db, user.username, user_update.oldpassword):
        return {'data': None, 'msg': '旧密码错误'}
    return crud.mod_password(db=db, user=user, user_update=user_update)
