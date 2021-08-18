from pydantic import BaseModel


class Osc(BaseModel):
    SQLSHA1: str


class Mod_data_export_status(BaseModel):
    id: int
    status: int
