from fastapi import APIRouter, Depends, UploadFile, File
from database.db import get_db
from app.utils import *
from .schema import *
from telegram.telegram import tgclient
import os
import io
from pyrogram import types
router = APIRouter(
    prefix='/manager',
    tags = ['Manager'],
    dependencies=[Depends(get_current_user)]
)


@router.get('/own_clients', name='get own clients with a full chat', response_model=list[ClientSchema])
async def get_own_clients(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    clients = db.query(models.Lead).filter(models.Lead.manager == current_user).all()

    response = []
    for client in clients:
        messages = db.query(models.Message).filter(models.Message.lead == client).order_by('id').all()
        message_data = []
        for message in messages:
            file_data = None
            if message.file:
                file_data = FileSchema(
                    id=message.file.id,
                    file_name=message.file.filename,
                    file_path=message.file.filepath
                )
            message_item = MessageSchema(
                id=message.id,
                text=message.text,
                is_manager_message=message.is_manager_message,
                time=message.timestamp,
                file = file_data
            )
            message_data.append(message_item)
        client_data = ClientSchema(
            id=client.id,
            chat_id=client.chat_id,
            full_name=client.full_name,
            last_manager_update=client.last_manager_update,
            status = client.status,
            language=client.language,
            source=client.source,
            description = client.description,
            chat = message_data
        )
        response.append(client_data)

    return response


@router.put("/{client_id}/update/status", name="update client status", response_model=ClientStatusChange)
async def update_client_status(client_id: int, new_status: str, current_user=Depends(get_current_user),db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.id == client_id, models.Lead.manager == current_user).first()

    if client.manager != current_user or not client:
        raise HTTPException(status_code=404, detail="Client not found or not your client")

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


@router.post('/send_message/{client_id}')
async def send_message(client_id: int, msg: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.manager == current_user, models.Lead.id == client_id).first()


    await tgclient.send_message(chat_id=client.chat_id, text=msg)
    
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


@router.post('/send_files/{client_id}', name='send files/photos/videos with/without caption(text)')
async def send_message(client_id: int, msg: str = None, files: list[UploadFile] = File(...), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.manager == current_user, models.Lead.id == client_id).first()
    
    media = []
    
    for i, file in enumerate(files):
        file_data = await file.read()
        file_stream = io.BytesIO(file_data)
        file_stream.name = file.filename

        #############################unique filenmaes #################
        # unique_filename = str(uuid.uuid4())
        # file_extension = os.path.splitext(file.filename)[1]
        # media_path = os.path.join('D:\\ozod\\tgProject\\files', unique_filename + file_extension)
        
        # with open(media_path, 'wb') as f:
        #     f.write(file_data)
        # media.append(types.InputMediaDocument(media_path))
        ################################################


        media_path = os.path.join('D:\\ozod\\tgProject\\files', file.filename)
        with open(media_path, 'wb') as f:
            f.write(file_data)
        media.append(types.InputMediaDocument(media_path))

        db_file = models.File(
            filename=file.filename,
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

    media[-1].caption = msg

    await tgclient.send_media_group(chat_id=client.chat_id, media=media)

    return {"message": "Сообщение отправлено успешно"}


@router.post('/send_only_files/{client_id}', name='send only photos/videos/files')
async def send_message(client_id: int, files: list[UploadFile] = File(...), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(models.Lead).filter(models.Lead.manager == current_user, models.Lead.id == client_id).first()

    media = []

    for file in files:
        file_data = await file.read()
        file_stream = io.BytesIO(file_data)
        file_stream.name = file.filename

        media_path = os.path.join('D:\\ozod\\tgProject\\files', file.filename) #apiminzifa #files
        with open(media_path, 'wb') as f:
            f.write(file_data)
        media.append(types.InputMediaDocument(media_path))

        db_file = models.File(
            filename=file.filename,
            filepath=media_path,
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
    
    await tgclient.send_media_group(chat_id=client.chat_id, media=media)

    return {"message": "Все файлы были успешно отправлены"}


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


@router.put('/change/task/status/done')
async def change_task_status(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    task.is_done = True
    db.commit()
    #условие если это assoigned_task то логика с статистикой
    return {"message": "Задача успешно сделана!"}



