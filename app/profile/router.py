from app.Administrator.schema import *
from app.manager.schema import *
from fastapi import APIRouter, Depends, UploadFile, File
from database.db import get_db
from app.utils import *

from telegram.telegram import tgclient
import os
import io
from pyrogram import types
from fastapi import File, UploadFile
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image
from fastapi.responses import FileResponse
from fastapi import File, UploadFile
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image
from fastapi.responses import FileResponse

router = APIRouter(
    prefix='/api/v1/profile',
    tags = ['Profile'],
    dependencies=[Depends(get_current_user)]
)

@router.get('/me', name="get own data", response_model=UserSchema)
async def get_all_staff(current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    return current_user



@router.put('/edit', name='update user data', response_model=RegUserSchemaResponse)
async def change_user_data(user: UserUpdateSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    user_update = db.query(models.User).filter(models.User.id == current_user.id).first()

    if user.full_name is not None:
        user_update.full_name = user.full_name
    if user.email is not None:
        user_update.email = user.email
    if user.department is not None:
        user_update.department = user.department
    if user.role is not None:
        user_update.role = user.role
    if user.language is not None:
        user_update.language = user.language


    db.commit()
    db.refresh(user_update)
    return user_update
@router.put('/edit/password', name="change own password")
async def change_own_password(old_password: str, new_password: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if verify_password(old_password, current_user.password):
        new_hashed_password = pwd_context.hash(new_password)
        current_user.password = new_hashed_password
        db.commit()
        return {"message": "Пароль был успешно изменен"}
    else:
        raise HTTPException(status_code=400, detail="Неверный пароль")



router.mount('/static', StaticFiles(directory='static'), name='static')
FILEPATH = "./static/images/"
@router.put('/edit/image')
async def create_profile_image(file: UploadFile = File(...), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    
    filename = file.filename

    extension = filename.split('.')[1]

    if extension not in ['jpg', 'jpeg', 'png']:
        raise HTTPException(status_code=400, detail="Неверный формат файла")
    token_name = secrets.token_hex(10)+"."+extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()

    with open(generated_name, 'wb') as file:
        file.write(file_content)

    img = Image.open(generated_name)
    img = img.resize(size=(45, 45))
    img.save(generated_name)

    file.close()

    file_url = "crm-ut.com" + generated_name[1:]
    current_user.avatar = file_url
    db.commit()

    return {"message": 'Аватар успешно изменен'}


