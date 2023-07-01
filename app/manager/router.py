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
    prefix='/api/v1/manager',
    tags = ['Manager'],
    dependencies=[Depends(get_current_user)]
)
router.mount('/static', StaticFiles(directory='static'), name='static')

@router.get('/leads', name='get own leads(clients) with a full chat', response_model=list[ClientSchema])
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

@router.post('/lead', response_model = ClientSchema)
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

@router.put('/lead/{lead_id}')
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


@router.put("/lead/{lead_id}/status", name="update lead status", response_model=ClientStatusChange)
async def update_client_status(lead_id: int, new_status: str, current_user=Depends(get_current_user),db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.manager == current_user).first()

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

@router.put('/status/free', name="Update manager status into free")
async def update_manager_status_free(current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    current_user.is_busy = False
    current_user.has_additional_client = False
    db.commit()

    return {"message": "Статус поменян на работаю"}

@router.put('/status/busy', name="Update manager status into busy")
async def update_manager_status_free(current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    current_user.is_busy = True
    db.commit()

    return {"message": "Статус поменян на занят и что-то еще"}


@router.post('/send_message/{lead_id}', name="Send message to a lead")
async def send_message_msg(lead_id: int, msg: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.manager == current_user, models.Lead.id == lead_id).first()
    # try:
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
    # except Exception:
    #     return {"message": "Личка у пользователя закрыта"}



@router.post('/send_multiple_files/{lead_id}', name='send multiple files /videos/files at once')
async def send_files(lead_id: int, files: List[UploadFile] = File(...), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.manager == current_user, models.Lead.id == lead_id).first()
    FILEPATH = "./static/files/"
    for file in files:
        filename = file.filename
        base_name, extension = os.path.splitext(filename)
        generated_name = FILEPATH + filename

        counter = 1
        while os.path.exists(generated_name):
            new_filename = f"{base_name}_{counter}{extension}"
            generated_name = FILEPATH + new_filename
            counter += 1

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
    
    return {"message": "Сообщение отправлено успешно"}


import os

router.mount('/static', StaticFiles(directory='static'), name='static')
@router.post('/send_one_file/{client_id}', name='send one /videos/files')
async def send_file(client_id: int, file: UploadFile = File(...),  current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.manager == current_user, models.Lead.id == client_id).first()

    FILEPATH = "./static/files/"
    filename = file.filename
    generated_name = FILEPATH + filename

    extension = filename.split('.')[1]
    filename_without_extension = filename.split('.')[0]
    

    counter = 1
    while os.path.exists(generated_name):
        new_filename = filename_without_extension+"-"+str(counter)+"."+extension
        generated_name = FILEPATH + new_filename
        counter += 1

    file_content = await file.read()

    with open(generated_name, 'wb') as f:
        f.write(file_content)

    file.close()
    file_url = "crm-ut.com" + generated_name[1:]
    db_file = models.File(
        filename=file.filename,
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
@router.get('/workingtime/dates', name='get own working times', response_model=list[OwnWorkTime])
async def get_own_worktimes(current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    records = db.query(models.WorkTime).filter(models.WorkTime.staff == current_user).all()
    
    return records

@router.get('/workingtime/dates/{date}', name='get own working times ', response_model=list[OwnWorkTime])
async def get_own_worktimes_by_date(date: date, current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    records = db.query(models.WorkTime).filter(models.WorkTime.staff == current_user, models.WorkTime.date == date).all()
    
    return records



@router.get('/workingtime/range/dates', name='get own working times by a range', response_model=List[OwnWorkTime])
async def get_own_worktimes_by_range_date(start_date: date, end_date: Optional[date] = None, current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    records = db.query(models.WorkTime).filter(models.WorkTime.staff == current_user, models.WorkTime.date >= start_date)
    if end_date:
        records = records.filter(models.WorkTime.date <= end_date)
    
    records = records.all()
    return records
    

##########


from sqlalchemy import or_
@router.get('/tasks', response_model=list[TaskSchema])
async def get_own_tasks(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    all_tasks = db.query(models.Task).filter(
        or_(
            models.Task.created_by == current_user,
            models.Task.assigned_staff == current_user
        )
    ).order_by('id').all()
    return all_tasks