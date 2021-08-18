from pydantic import BaseModel
from typing import Optional, List


class instance(BaseModel):
    ins_name: str
    host: str
    port: int
    user: str
    type: str
    db_type: str


class InsIn(instance):
    password: str

    class Config:
        orm_mode = True


class InsUpdate(instance):
    id: int
    password: str


class InsOut(instance):
    id: int

    class Config:
        orm_mode = True


class DataOut(BaseModel):
    data: List[InsOut]
    msg: str
    total: int


class Del_binlog(BaseModel):
    id: int
    binlog: str


class Processlist(BaseModel):
    id: int
    command_type: str
    database: str


class Kill_session(BaseModel):
    id: int
    threadID: int


class Dbid(BaseModel):
    id: int


class Grant(BaseModel):
    instance_id: int
    user_host: str
    priv_type: int
    privs: dict
    db_name: list
    tb_name: list


class Revoke(BaseModel):
    instance_id: int
    grant_sql: str


class Instance_user_delete(BaseModel):
    instance_id: int
    user_host: str


class Instance_user_create(BaseModel):
    instance_id: int
    user: str
    host: str
    password1: str
    password2: str


class Instance_user_reset_pwd(BaseModel):
    instance_id: int
    user_host: str
    password1: str
    password2: str


class Show_variables(BaseModel):
    instance_id: int
    value: str


class Set_global(BaseModel):
    instance_id: int
    variable_name: str
    value: str
