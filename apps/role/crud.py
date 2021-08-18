from database.models import Role, Privilege, Instance, User
from sqlalchemy.orm import Session, load_only
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from . import schemas


def create_role(db: Session, ins: schemas.RoleIn):
    try:
        obj = Role(**ins.dict())
        db.add(obj)
        db.commit()
        return {'data': obj, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_role(db: Session, offset: int, limit: int, role: str = None, id: int = None):
    if role:
        objs = db.query(Role).filter(Role.role.like('%' + role + '%'))
    elif id:
        obj = db.query(Role).filter(Role.id == id).first()
        return {'data': jsonable_encoder(obj), 'msg': 'success'}
    else:
        objs = db.query(Role)
    count = objs.count()
    jsen = jsonable_encoder(objs.offset((offset - 1) * limit).limit(limit).all())
    [i.update(ins=[dict(zip(['privilege_id', 'privileges', 'instance_id', 'ins_name', 'type'], j)) for j in
                   db.query(Instance, Privilege).with_entities(Privilege.id, Privilege.privileges, Instance.id,
                                                               Instance.ins_name, Instance.type).filter(
                       Privilege.instance_id == Instance.id, Privilege.role_id == i['id']).all()]) for i in jsen]

    return {'data': jsen, 'total': count, 'msg': 'success'}


def del_role(db: Session, id: int):
    try:
        obj_role = db.query(Role).filter(Role.id == id).first()
        obj_pri = db.query(Privilege).filter(Privilege.role_id == id).all()
        obj_usr = db.query(User).filter(User.role_id == id).all()
        if obj_pri:
            for i in obj_pri:
                db.delete(i)
        if obj_usr:
            for j in obj_usr:
                j.status = '锁定'
        db.delete(obj_role)
        db.commit()
        return {'data': obj_role, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def update_role(db: Session, ins: schemas.RoleOut):
    try:
        role = db.query(Role).filter(Role.id == ins.id).update({Role.role: ins.role, Role.department: ins.department})
        db.commit()
        if role == 1:
            return {'data': ins, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_pri(db: Session):
    objs = db.query(Privilege).all()
    print(jsonable_encoder(objs))
    return objs


def add_pri(db: Session, pri: schemas.Privilege):
    try:
        obj = Privilege(**pri.dict())
        db.add(obj)
        db.commit()
        return {'data': obj, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def update_pri(db: Session, pri_id: int, pri: str):
    try:
        db.query(Privilege).filter(Privilege.id == pri_id).update({Privilege.privileges: pri})
        db.commit()
        return {'data': None, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def del_pri(db: Session, pri_id: int):
    try:
        obj = db.query(Privilege).filter(Privilege.id == pri_id).first()
        db.delete(obj)
        db.commit()
        return {'data': obj, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_partins(db: Session, role_id: int):
    try:
        ins_id = db.query(Privilege).with_entities(Privilege.instance_id).filter(Privilege.role_id == role_id).all()
        ins_id = [i[0] for i in ins_id]
        ins = db.query(Instance).options(load_only('id', 'ins_name', 'type')).filter(Instance.id.notin_(ins_id)).all()
        return {'data': ins, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
