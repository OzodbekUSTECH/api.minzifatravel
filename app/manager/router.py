from fastapi import APIRouter, Depends, UploadFile, File
from database.db import get_db
from app.utils import *
from .schema import *
from telegram.telegram import tgclient
import os
import io
from pyrogram import types
from fastapi import File, UploadFile
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image
from fastapi.responses import FileResponse


router = APIRouter(
    prefix='/manager',
    tags = ['Manager'],
    dependencies=[Depends(get_current_user)]
)
router.mount('/static', StaticFiles(directory='static'), name='static')

@router.get('/own_clients', name='get own clients with a full chat', response_model=list[ClientSchema])
async def get_own_clients(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    clients = db.query(models.Lead).filter(models.Lead.manager == current_user).all()

    response = []
    for client in clients:
       
        messages_response = []
        for message in client.messages:
            file_data = None
            if message.file:
                file_data = FileSchema(
                    id=message.file.id,
                    file_name=message.file.filename,
                    file_path=message.file.filepath
                )
            message_data = MessageSchema(
                id=message.id,
                text=message.text,
                is_manager_message=message.is_manager_message,
                time=message.timestamp,
                file = file_data
            )
            messages_response.append(message_data)
        client_data = ClientSchema(
           id=client.id,
            full_name=client.full_name,
            phone_number=client.phone_number,
            email=client.email,
            language=client.language,
            source=client.source,
            created_at=client.created_at,
            status=client.status,
            last_update=client.last_manager_update,
            description=client.description,
            chat = messages_response
        )
        response.append(client_data)

    return response

@router.post('/create/lead', response_model = ClientSchema)
async def create_lead(lead: CreateClientSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_lead = models.Lead(
        full_name=lead.full_name,
        phone_number=lead.phone_number,
        email=lead.email,
        language=lead.language,
        source=lead.source,
    )
    db_lead.manager = current_user
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

@router.put('/update/{lead_id}/data')
async def update_lead_data(lead_id: int, lead: UpdateClientSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if db_lead.manager != current_user:
        raise HTTPException(status_code=403, detail="You are not the manager of this lead")
    if lead.full_name is not None:
        db_lead.full_name = lead.full_name
    if lead.phone_number is not None:
        db_lead.phone_number = lead.phone_number
    if lead.email is not None:
        db_lead.email = lead.email
    if lead.language is not None:
        db_lead.language = lead.language
    if lead.source is not None:
        db_lead.source = lead.source
    db.commit()
    db.refresh(db_lead)
    return db_lead


@router.put("/{client_id}/update/status", name="update client status", response_model=ClientStatusChange)
async def update_client_status(client_id: int, new_status: str, current_user=Depends(get_current_user),db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.id == client_id, models.Lead.manager == current_user).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.status != new_status: #обработан != Квалификация
        if client.status == "Обработан":
            manager = client.manager
            manager.amount_finished_clients -= 1

        client.status = new_status
        

        if new_status == "Обработан":
            manager = client.manager
            manager.amount_finished_clients += 1
            
        db.commit()

    response = ClientStatusChange(
        message="Статус поменян",
        details = {
            "id": client.id,
            "full_name": client.full_name,
            "status": client.status
        }
    )
    return response

@router.put('/status/update/free', name="Update manager status into free")
async def update_manager_status_free(current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    current_user.is_busy = False
    current_user.has_additional_client = False
    db.commit()

    return {"message": "Статус поменян на работаю"}

@router.put('/status/update/busy', name="Update manager status into busy")
async def update_manager_status_free(current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    current_user.is_busy = True
    db.commit()

    return {"message": "Статус поменян на занят и что-то еще"}


@router.post('/send_message/{client_id}', name="Send message to a client")
async def send_message_msg(client_id: int, msg: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.manager == current_user, models.Lead.id == client_id).first()
    try:
        if client.chat_id:
            await tgclient.send_message(chat_id=client.chat_id, text=msg)
        else:
            await tgclient.send_message(chat_id=client.phone_number, text=msg)

        db_message = models.Message(
            text=msg,
            lead=client,
            manager=current_user,
            is_manager_message = True
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
    
        return {"message": "Сообщение отправлено успешно"}
    except Exception:
        return {"message": "Личка у пользователя закрыта"}


@router.post('/send_files_wtf/{client_id}', name='send files/photos/videos with/without caption(text)')
async def send_message(client_id: int, msg: str = None, files: list[UploadFile] = File(...), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.manager == current_user, models.Lead.id == client_id).first()
    
    media = []
    
    for i, file in enumerate(files):
        
        filename = file.filename
        extension = filename.split('.')[1]
        token_name = secrets.token_hex(10)+"."+extension
        file_path = os.path.join("/home/api.minzifatravel/static/files", token_name)
        file_content = await file.read()
        
        with open(file_path, 'wb') as file:
            file.write(file_content)

        file.close()
        media_path = f"crm-ut.com/static/files/{token_name}"
        
        
        db_file = models.File(
            filename=filename,
            filepath=media_path,
            lead=client,
            manager=current_user,
        )

        if i == len(files) - 1:
            db_message = models.Message(
                text=msg,
                lead=client,
                manager=current_user,
                is_manager_message=True,
                file=db_file  
            )
           
        else:
            db_message = models.Message(
                text=None,
                lead=client,
                manager=current_user,
                is_manager_message=True,
                file=db_file  
            )

        db.add(db_message)
        db.commit()
        media.append(types.InputMediaDocument(media_path))
    media[-1].caption = msg

    await tgclient.send_media_group(chat_id=client.chat_id, media=media)

    return {"message": "Сообщение отправлено успешно"}


@router.post('/send_multiple_files/{client_id}', name='send multiple files /videos/files')
async def send_files(client_id: int, files: List[UploadFile] = File(...), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.manager == current_user, models.Lead.id == client_id).first()
    FILEPATH = "./static/files/"
    for file in files:
        filename = file.filename
        extension = filename.split('.')[1]
        token_name = secrets.token_hex(10)+"."+extension
        generated_name = FILEPATH + token_name
        file_content = await file.read()

        with open(generated_name, 'wb') as file_obj:
            file_obj.write(file_content)

        file_obj.close()
        file_url = "crm-ut.com" + generated_name[1:]
        db_file = models.File(
            filename=filename,
            filepath=file_url,
            lead=client,
            manager=current_user
        )
        db_message = models.Message(
            text=None,
            lead=client,
            manager=current_user,
            is_manager_message=True,
            file=db_file
        )

        db.add(db_message)
        db.commit()
        file_url = "https://crm-ut.com" + generated_name[1:]
        # Отправка документа с использованием Pyrogram
        await tgclient.send_document(
            chat_id=client.chat_id,
            document=file_url
        )
    
    return {"message": "Сообщение отправлено успешно"}


@router.post('/send_one_file/{client_id}', name='send one /videos/files')
async def send_file(client_id: int, file: UploadFile = File(...),  current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.manager == current_user, models.Lead.id == client_id).first()
    
    FILEPATH = "./static/files/"
    filename = file.filename
    extension = filename.split('.')[1]
    token_name = secrets.token_hex(10)+"."+extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()

    with open(generated_name, 'wb') as file:
        file.write(file_content)

    file.close()
    file_url = "crm-ut.com" + generated_name[1:]
    db_file = models.File(
        filename=filename,
        filepath=file_url,
        lead=client,
        manager=current_user
    )
    db_message = models.Message(
        text=None,
        lead=client,
        manager=current_user,
        is_manager_message=True,
        file=db_file
    )

    db.add(db_message)
    db.commit()
    file_url = "https://crm-ut.com" + generated_name[1:]
    # Отправка документа с использованием Pyrogram
    await tgclient.send_document(
        chat_id=client.chat_id,
        document=file_url
    )

    # Возвращаем успешный ответ
    return {"message": "File sent successfully"}



##########
from app.workingtime.schema import *
@router.get('/get_own_worktimes', name='get own working times', response_model=list[OwnWorkTime])
async def get_own_worktimes(current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    records = db.query(models.WorkTime).filter(models.WorkTime.staff == current_user).all()
    
    return records

@router.get('/get_own_worktimes/{date}', name='get own working times ', response_model=list[OwnWorkTime])
async def get_own_worktimes_by_date(date: date, current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    records = db.query(models.WorkTime).filter(models.WorkTime.staff == current_user, models.WorkTime.date == date).all()
    
    return records



@router.get('/get_own_worktimes/range/', name='get own working times by a range', response_model=List[OwnWorkTime])
async def get_own_worktimes_by_range_date(start_date: date, end_date: Optional[date] = None, current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    records = db.query(models.WorkTime).filter(models.WorkTime.staff == current_user, models.WorkTime.date >= start_date)
    if end_date:
        records = records.filter(models.WorkTime.date <= end_date)
    
    records = records.all()
    return records
    

##########
from sqlalchemy import or_

@router.get('/get_tasks', response_model=list[TaskSchema])
async def get_own_tasks(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    all_tasks = db.query(models.Task).filter(
        or_(
            models.Task.created_by == current_user,
            models.Task.assigned_staff == current_user
        )
    ).order_by('id').all()
    return all_tasks

@router.post('/create_own_task', response_model=OwnTaskSchema)
async def create_own_task(task: CreateOwnTask, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_task = models.Task(
        title=task.title,
        description=task.description,
        time_deadline=task.time_deadline,
        date_deadline=task.date_deadline,
        priority=task.priority,
        created_by=current_user
    )
    db.add(db_task)
    db.commit()
    return db_task

@router.put('/change/{task_id}/data')
async def change_own_task(task_id: int, task: ChangeOwnTaskSchema,  db: Session = Depends(get_db)):
    task_update = db.query(models.Task).filter(models.Task.id == task_id).first()

    if task.title is not None:
        task_update.title = task.title
    if task.description is not None:
        task_update.description = task.description
    if task.time_deadline is not None:
        task_update.time_deadline = task.time_deadline
    if task.date_deadline is not None:
        task_update.date_deadline = task.date_deadline
    if task.priority is not None:
        task_update.priority = task.priority
    
    db.commit()
    return {"message": "Задача бела изменена"}



@router.put('/change/task/status/done')
async def change_task_status(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    task.is_done = True
    db.commit()
    #условие если это assoigned_task то логика с статистикой
    return {"message": "Задача успешно сделана!"}

@router.delete('/delete/task', name='delete only own task')
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    own_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not own_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена!")
    db.delete(own_task)
    db.commit()
    return {"message": "Задача удалена"}

