from pydantic import BaseModel


class Query(BaseModel):
    selectHost: int
    selectDb: str
    sql: str
    offset: int
    limit: int
    limit2: int


class Submit_workorder_data_export(BaseModel):
    selectHost: int
    selectDb: str
    sql: str
    manager: int
    dba: int
    limit2: int
    remark: str


class Exec_shell(BaseModel):
    cmd: str

