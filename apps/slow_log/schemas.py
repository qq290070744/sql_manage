from pydantic import BaseModel


class SlowLog(BaseModel):
    dbid: int
    db_user: str
    app_ip: str
    thread_id: int
    exec_duration: float
    rows_sent: int
    rows_examined: int
    start_time: str
    sql_pattern: str
    orig_sql: str
    fingerprint: str
