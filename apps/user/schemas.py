from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    type: str


class BaseUser(BaseModel):
    username: str
    email: str
    status: str
    role_id: int


class UserIn(BaseUser):
    password: str

    class Config:
        orm_mode = True


class UserOut(BaseUser):
    id: int

    class Config:
        orm_mode = True


class UserUpdate(BaseUser):
    password: str = None
    id: int

    class Config:
        orm_mode = True


class Mod_password(BaseModel):
    password: str
    oldpassword: str
