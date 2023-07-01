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
    tags = ['Gmail'],
    dependencies=[Depends(get_current_user)]
)

@router.post("/send/message")
async def simple_send(email: EmailSchema, current_user= Depends(get_current_user),db: Session = Depends(get_db) ) -> JSONResponse:
    db_leads = db.query(models.Lead).filter(models.Lead.email != None).all()
    
    html = email.message

    for recipient in db_leads:
        message = MessageSchema(
            subject="Fastapi-Mail module",
            recipients=[recipient.email],
            body=html,
            subtype=MessageType.html)

        fm = FastMail(conf)
        await fm.send_message(message)

    return JSONResponse(status_code=200, content={"message": "Email has been sent to multiple recipients."})

from fastapi import BackgroundTasks
from pyrogram.errors import PeerIdInvalid
@router.post('/send_message/everyone', name="Send message to everyone")
async def send_message_msg(background_tasks: BackgroundTasks, msg: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    clients = db.query(models.Lead).all()
    for client in clients:
        try:
            if client.chat_id:
                background_tasks.add_task(tgclient.send_message, chat_id=client.chat_id, text=msg)
            else:
                background_tasks.add_task(tgclient.send_message, chat_id=client.phone_number, text=msg)
        except:
            continue

    return {"message": "Сообщение отправлено"}