from app.Administrator.schema import *
from app.manager.schema import *
from fastapi import APIRouter, Depends, UploadFile, File
from database.db import get_db
from app.utils import *

from telegram.telegram import tgclient
import os
import io

from fastapi import FastAPI
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List
from .schema import *
from fastapi import BackgroundTasks

conf = ConnectionConfig(
    MAIL_USERNAME = "naimovozod81@gmail.com",
    MAIL_PASSWORD = "nqddzknaqybrdojn",
    MAIL_FROM = "naimovozod81@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_FROM_NAME = "Desired Name",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)


router = APIRouter(
    prefix='/api/v1/mail',
    tags = ['Sender'],
    dependencies=[Depends(get_current_user)]
)

@router.post("/send/message/mail")
async def simple_send(background_tasks: BackgroundTasks, email: EmailSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)) -> JSONResponse:
    db_leads = db.query(models.Lead).filter(models.Lead.email != None).all()
    
    html = email.message

    for recipient in db_leads:
        message = MessageSchema(
            subject="Fastapi-Mail module",
            recipients=[recipient.email],
            body=html,
            subtype=MessageType.html)

        fm = FastMail(conf)
        background_tasks.add_task(fm.send_message, message)

    return JSONResponse(status_code=200, content={"message": "Email has been sent to multiple recipients."})

from pyrogram.errors import PeerIdInvalid
@router.post('/send_message/telegram', name="Send message to everyone")
async def send_message_msg(msg: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    clients = db.query(models.Lead).all()
    failed_clients = []  # список для хранения неудачных отправок

    for client in clients:
        try:
            if client.chat_id:
                result = await tgclient.send_message(chat_id=client.chat_id, text=msg)
                if not result:
                    failed_clients.append(client.id)  # добавляем ID клиента в список неудачных отправок
            elif client.phone_number:
                result = await tgclient.send_message(chat_id=client.phone_number, text=msg)
                if not result:
                    failed_clients.append(client.id)  # добавляем ID клиента в список неудачных отправок
            else:
                failed_clients.append(client.id)  # добавляем ID клиента в список неудачных отправок
        except PeerIdInvalid:
            failed_clients.append(client.id)  # добавляем ID клиента в список неудачных отправок

    if failed_clients:
        return {"message": "Сообщение отправлено, но не удалось доставить некоторым пользователям", "failed_clients": failed_clients}
    else:
        return {"message": "Сообщение успешно отправлено"}