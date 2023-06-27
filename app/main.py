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



# def run_tgclient():
#     # Запустите клиента Pyrogram
#     tgclient.run()
# @app.on_event("startup")
# async def startup_event():
#     fastapi_process = multiprocessing.Process(target=tgclient)
#     tgclient_process = multiprocessing.Process(target=run_tgclient)

#     # Start both processes
#     fastapi_process.start()
#     tgclient_process.start()

#     # Wait for both processes to finish
#     fastapi_process.join()
#     tgclient_process.join()


 
    
# @app.on_event("shutdown")
# async def shutdown_event():
#     tgclient_process.join()

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


    # response = RegUserSchemaResponse(
    #     id=db_user.id,
    #     full_name=db_user.full_name,
    #     email=db_user.email,
    #     department=db_user.department,
    #     role=db_user.role,
    #     language=db_user.language
    # )
    return db_user



# def main():
#     # Запустить функцию run_tgclient() в отдельном процессе
#     tgclient_process = multiprocessing.Process(target=run_tgclient)
#     tgclient_process.start()

#     # Основная логика вашего FastAPI приложения
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

#     # Дождитесь завершения процесса tgclient
#     tgclient_process.join()

# if __name__ == '__main__':
#     main()