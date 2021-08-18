from pydantic import BaseModel


class Add_desensitization_info(BaseModel):
    id: int
    dbname: str
    field: str
