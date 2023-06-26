from fastapi import APIRouter, HTTPException, Depends, status
from database.db import get_db
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from .utils import *
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix='/login',
    tags = ['Login']
)



@router.post("/", response_model=TokenSchema)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"id": user.id, "full_name": user.full_name, "email": user.email}
    )
    response = TokenSchema( access_token=access_token, token_type="bearer")
    return response

