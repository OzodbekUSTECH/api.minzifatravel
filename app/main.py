from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
import multiprocessing
from telegram.telegram import tgclient
from .Administrator.router import router as admin_router
from .manager.router import router as manager_router
from .login import router as login_router
from .workingtime.router import router as working_time_router
from .task.router import router as task_router
from .profile.router import router as profile_router
from .mail.router import router as mail_router
from .lead.router import router as lead_router
import os
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
app.include_router(lead_router)
app.include_router(profile_router)
app.include_router(admin_router)
app.include_router(manager_router)
app.include_router(working_time_router)
app.include_router(task_router)
app.include_router(mail_router)


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


@app.put('/api/v1/change/manager/lead/{lead_id}', name="Change lead(client) manager when time is over", tags=['Logic'])
async def change_client_manager(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Client not found")

    current_manager = lead.manager

    if lead.language == 'ru':
        available_manager = db.query(models.User).filter_by(department="Отдел продаж", language=lead.language, is_busy=False).first()
        better_manager = db.query(models.User).filter_by(department="Отдел продаж", language=lead.language, has_additional_client=False).order_by(desc(models.User.amount_finished_clients)).first()
        if not available_manager:
            available_manager = db.query(models.User).filter_by(department="Отдел продаж", language="en", is_busy=False).first()
        if not better_manager and not available_manager:
            better_manager = db.query(models.User).filter_by(department="Отдел продаж", language="en", has_additional_client=False).order_by(desc(models.User.amount_finished_clients)).first()
    else:
        available_manager = db.query(models.User).filter_by(department="Отдел продаж", language=lead.language, is_busy=False).first()
        better_manager = db.query(models.User).filter_by(department="Отдел продаж", language=lead.language, has_additional_client=False).order_by(desc(models.User.amount_finished_clients)).first()
    if available_manager:
        # Присоединение пользователя к свободному менеджеру
        lead.manager_id = available_manager.id
        available_manager.is_busy = True
        db.commit()

    elif better_manager:
        
        lead.manager_id = better_manager.id
        better_manager.has_additional_client = True
        db.commit()

    else:
        while True:
            await asyncio.sleep(5)
            available_manager = db.query(models.User).filter(models.User.id != current_manager.id).filter_by(department="Отдел продаж", language=lead.language, is_busy=False).first()
            if available_manager:
                # Присоединение пользователя к свободному менеджеру
                lead.manager_id = available_manager.id

                for message in lead.messages:
                        message.manager = available_manager

                for file in lead.files:
                    file.manager = available_manager

                available_manager.is_busy = True
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

