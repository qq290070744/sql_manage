from fastapi import APIRouter
from . import crud

dash = APIRouter()


@dash.get('/sqlcount/')
def sql_count():
    return crud.get_sqlcount()
