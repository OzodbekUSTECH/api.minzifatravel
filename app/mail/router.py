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

import fastapi_mail

@router.post("/send/message/mail", name = 'send message to a person via email address')
async def simple_send(background_tasks: BackgroundTasks, email: str, msg: str, file: list[UploadFile] = File(None), current_user= Depends(get_current_user),db: Session = Depends(get_db)):
    
    html = msg
    
    if file is not None:
        message = fastapi_mail.MessageSchema(
        subject="Fastapi-Mail module",
        recipients=[email],
        body=html,
        subtype=MessageType.html,
        attachments=file)
    else:
        message = fastapi_mail.MessageSchema(
            subject="Fastapi-Mail module",
            recipients=[email],
            body=html,
            subtype=MessageType.html)
        
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)
    
    
    response = {
        'status': 200,
        'content': "zaebis"        
    }
    return response


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
    

import imaplib
import email
from email.header import decode_header
import json
from email.utils import parseaddr

@router.get("/messages")
def get_messages():
    # Параметры для подключения к почтовому серверу
    server = "imap.gmail.com"
    username = "naimovozod81@gmail.com"
    password = "nqddzknaqybrdojn"

    # Установка соединения с почтовым сервером
    mail = imaplib.IMAP4_SSL(server)
    mail.login(username, password)

    # Выбор почтового ящика (inbox)
    mail.select('INBOX')


    status, data = mail.search(None, '(FROM "ozod.naimov@mail.ru")')
    message_ids = data[0].split()


    messages = []

    for msg_id in message_ids:
        # Получение данных сообщения
        status, data = mail.fetch(msg_id, '(RFC822)')
        raw_email = data[0][1]

        msg = email.message_from_bytes(raw_email)

        sender_name, sender_email = parseaddr(msg['From'])
        sender = sender_email
        subject = decode_header(msg['Subject'])[0][0] if msg['Subject'] is not None else ''
        date = msg['Date']

        # Обработка тела сообщения
        if msg.is_multipart():
            # Если сообщение состоит из нескольких частей, перебираем их
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode("UTF-8")
                    break
        else:
            # Если сообщение состоит из одной части
            body = msg.get_payload(decode=True).decode("UTF-8")

        message = {
            "От": sender,
            "Тема": subject,
            "Дата": date,
            "Сообщение": body
        }

        messages.append(message)

    # Закрытие соединения с почтовым сервером

    return messages