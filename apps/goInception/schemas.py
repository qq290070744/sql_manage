from pydantic import BaseModel


class Set_inception_show_variables(BaseModel):
    Variable_name: str
    Value: str


class Set_inception_show_levels(BaseModel):
    Name: str
    Value: str
