from pydantic import BaseModel
from apps.user.schemas import UserOut
from typing import List, Dict


class Query(BaseModel):
    selectHost: int
    selectDb: str
    sql: str
    manager: int
    dba: int
    remark: str


class resOut(BaseModel):
    data: Dict[str, List[UserOut]]
    msg: str


class alter_merge_sql(BaseModel):
    sql: str
