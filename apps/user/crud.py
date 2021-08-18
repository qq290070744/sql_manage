from database.models import User, Role
from apps.user import schemas
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_users(db: Session, offset: int, limit: int, user: str = None, ):
    try:
        if user:
            users = db.query(User, Role).filter(User.role_id == Role.id, User.username.like('%' + user + '%'))
        else:
            users = db.query(User, Role).filter(User.role_id == Role.id)
        total = users.count()
        users = jsonable_encoder(users.offset((offset - 1) * limit).limit(limit).all())
        users = [i[0] for i in users if not i[1].update(i[0]) and i.pop(0)]
        return {'data': users, 'total': total, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_user(db: Session, name: str):
    try:
        user = db.query(User).filter(User.username == name, User.status == '正常').first()
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def add_user(db: Session, user: schemas.UserIn):
    try:
        user_ins = User(**user.dict())
        user_ins.password = pwd_context.hash(user_ins.password)
        db.add(user_ins)
        db.commit()
        return {'data': user, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def update_user(db: Session, user: schemas.UserUpdate):
    try:
        obj = db.query(User).filter(User.id == user.id)
        if user.password:
            obj.update(
                {User.password: pwd_context.hash(user.password), User.role_id: user.role_id, User.status: user.status, User.email: user.email})
        else:
            obj.update({User.role_id: user.role_id, User.status: user.status, User.email: user.email})
        db.commit()
        return {'data': None, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def delete_user(db: Session, id: int):
    try:
        obj = db.query(User).filter(User.id == id).first()
        db.delete(obj)
        db.commit()
        return {'data': None, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_user_role(db: Session, user: schemas.UserOut):
    try:
        userrole = db.query(Role.role).filter(Role.id == user.role_id).first()
        return userrole[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def mod_password(db: Session, user: schemas.UserOut, user_update: schemas.Mod_password):
    try:
        obj = db.query(User).filter(User.id == user.id)
        obj.update(
            {User.password: pwd_context.hash(user_update.password), })
        db.commit()
        return {'data': None, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
