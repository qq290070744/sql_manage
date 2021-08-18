from pydantic import BaseModel
from typing import List
from apps.instance.schemas import InsOut


class Privilege(BaseModel):
    role_id:int
    instance_id:int
    privileges:str
    class Config:
        orm_mode =True

class PrivilegeOut(Privilege):
    id:int
    class Config:
        orm_mode = True

class RoleIn(BaseModel):
    role:str
    department:str
    class Config:
        orm_mode =True

class RoleOut(BaseModel):
    id:int
    role:str
    department:str
    class Config:
        orm_mode =True

