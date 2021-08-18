from fastapi import APIRouter, Depends
from . import crud, schemas
from apps.user.user import validate_pri, valid_token

go_inception = APIRouter()


@go_inception.get('/get_inception_show_variables/')
def inception_show_variables():
    return crud.inception_show_variables()


@go_inception.post('/set_inception_show_variables/')
def set_inception_show_variables(inception_variables: schemas.Set_inception_show_variables = (...), pri: bool = Depends(valid_token), ):
    return crud.set_inception_show_variables(inception_variables)


@go_inception.get('/get_inception_show_levels/')
def get_inception_show_levels():
    return crud.get_inception_show_levels()


@go_inception.post('/set_inception_show_levels/')
def set_inception_show_levels(inception_levels: schemas.Set_inception_show_levels = (...), pri: bool = Depends(valid_token), ):
    return crud.set_inception_show_levels(inception_levels)
