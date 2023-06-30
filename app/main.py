from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
import multiprocessing
from telegram.telegram import tgclient
from .Administrator.router import router as admin_router
from .manager.router import router as manager_router
from .login import router as login_router
from .workingtime.router import router as working_time_router
app = FastAPI(title='Minzifa travel api')

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 


app.include_router(login_router)
app.include_router(admin_router)
app.include_router(manager_router)
app.include_router(working_time_router)

@app.on_event("startup")
async def startup_event():
    await tgclient.start()

 
    
@app.on_event("shutdown")
async def shutdown_event():
    await tgclient.stop()

from app import models
from .utils import *
from sqlalchemy import desc
import asyncio


@app.put('/{client_id}/change/manager/', name="Change Client's manager when time is over", tags=['Logic'])
async def change_client_manager(client_id: int, db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    current_manager = client.manager

    new_manager =  db.query(models.User).filter_by(role="manager", language=client.language, status="Free").filter(models.User.id != current_manager.id).first()
    better_manager = db.query(models.User).filter_by(role="manager", language=client.language, has_additional_client=False).order_by(desc(models.User.amount_finished_clients)).filter(models.User.id != current_manager.id).first()

    if new_manager:                # Присоединение пользователя к свободному менеджеру
        client.manager = new_manager

        for message in client.messages:
            message.manager = new_manager

        new_manager.status = "Busy"
        db.commit()
    elif better_manager:
        client.manager = better_manager

        for message in client.messages:
            message.manager = better_manager

        better_manager.has_additional_client = True
        db.commit()
    else:    
        while True:
            await asyncio.sleep(5)
            available_manager = db.query(models.User).filter_by(role="manager", language=client.language, status="Free").filter(models.User.id != current_manager.id).first()
            if available_manager:
                # Присоединение пользователя к свободному менеджеру
                client.manager_id = available_manager.id
                for message in client.messages:
                    message.manager = available_manager
                available_manager.status = "Busy"
                db.commit()
                break

    return {"message": 'Менеджер у клиента поменян'}


from sqlalchemy.exc import IntegrityError
@app.post('/registration/any', summary="Create a new user", response_model=RegUserSchemaResponse)
async def register(user: UserCreateSchema, db: Session = Depends(get_db)):


    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        full_name=user.full_name,
        email=user.email,
        department=user.department,
        role=user.role,
        language=user.language
    )
    db_user.password = hashed_password
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует.")

    return db_user





############avatar
from fastapi import File, UploadFile
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image
from fastapi.responses import FileResponse

app.mount('/static', StaticFiles(directory='static'), name='static')
FILEPATH = "./static/images/"
@app.post('/upload/profile/image')
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