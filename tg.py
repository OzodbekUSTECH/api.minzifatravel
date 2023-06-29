from pyrogram import Client, filters
from app.models import *
from pyrogram.types import Message as TelegramMessage
import os
from sqlalchemy import desc
import asyncio
from database.db import Session
from datetime import datetime
#lamguages
import codecs


def detect_user_language(message):
    ru_alphabet = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    en_alphabet = set('abcdefghijklmnopqrstuvwxyz')

   
    if any(char in ru_alphabet for char in message.lower()):
        return 'ru'
    elif any(char in en_alphabet for char in message.lower()):
        return 'en'
    else:
        return 'en'
# Введите ваш API ID и API Hash
api_id = '20122546'
api_hash = 'c3ca5ae4e368b18eccd06a5edcd7eec0'

# Создайте экземпляр клиента Pyrogram
tgclient = Client("minzifaapi", api_id=api_id, api_hash=api_hash)

db = Session()
@tgclient.on_message(filters.private & filters.incoming) 
async def handle_private_message(client: Client, message: TelegramMessage):
    # Проверка, является ли отправитель пользователем
    if message.from_user:
        lead_id = message.from_user.id
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        message_text = message.text or ""
        
        language = detect_user_language(message_text)
        

        lead = db.query(Lead).filter_by(chat_id=lead_id).first()

        if not lead:
            # Создание нового пользователя
            lead = Lead(chat_id=lead_id, full_name=f"{first_name} {last_name}", language=language, source="Telegram")
            db.add(lead)
            db.commit()

            # Поиск свободного менеджера
            if lead.language == 'ru':
                available_manager = db.query(User).filter_by(department="Отдел продаж", language=lead.language, is_busy=False).first()
                better_manager = db.query(User).filter_by(department="Отдел продаж", language=lead.language, has_additional_client=False).order_by(desc(User.amount_finished_clients)).first()
                if not available_manager:
                    available_manager = db.query(User).filter_by(department="Отдел продаж", language="en", is_busy=False).first()
                if not better_manager and not available_manager:
                    better_manager = db.query(User).filter_by(department="Отдел продаж", language="en", has_additional_client=False).order_by(desc(User.amount_finished_clients)).first()
            else:
                available_manager = db.query(User).filter_by(department="Отдел продаж", language=lead.language, is_busy=False).first()
                better_manager = db.query(User).filter_by(department="Отдел продаж", language=lead.language, has_additional_client=False).order_by(desc(User.amount_finished_clients)).first()
            if available_manager:
                # Присоединение пользователя к свободному менеджеру
                lead.manager_id = available_manager.id
                available_manager.is_busy = True
                db.commit()

                if lead.language == "ru":
                    await client.send_message(lead.chat_id, "Добро пожаловать в MINZIFA TRAVEL!")
                else:
                    await client.send_message(lead.chat_id, "Welcome to MINZIFA TRAVEL!")
  
            elif better_manager:
                better_manager.has_additional_client = True
                lead.manager_id = better_manager.id
                db.commit()
                if lead.language == "ru":
                    await client.send_message(lead.chat_id, "Добро пожаловать в MINZIFA TRAVEL!")
                else:
                    await client.send_message(lead.chat_id, "Welcome to MINZIFA TRAVEL!")
            else:
                if lead.language == 'ru':
                    await client.send_message(lead.chat_id, "<b><em>Добро пожаловать в MINZIFA TRAVEL!</em></b>\n\nИзвините, в данный момент все менеджеры заняты. Пожалуйста, ожидайте.")
                else:
                    await client.send_message(lead.chat_id, "<b><em>Welcome to MINZIFA TRAVEL!</em></b>\n\nSorry, all managers are busy at the moment. Please wait.")
                
                content = None
                filename = None
                filepath = None

                if message.document:
                    filename = message.document.file_name
                    file_path = os.path.join("/home/api.minzifatravel/static/files", filename)  # Полный путь для сохранения файла
                    await message.download(file_path)
                    filepath = f"crm-ut.com/static/files/{filename}"
                    content = message.caption or None
                elif message.photo:
                    # Генерация уникального имени файла
                    filename = f"photo_{message.photo.file_unique_id}.jpg"
                    file_path = os.path.join("/home/api.minzifatravel/static/files", filename)  # Полный путь для сохранения фото
                    await message.download(file_path)
                    filepath = f"crm-ut.com/static/files/{filename}"
                    content = message.caption or None
                elif message.video:
                    filename = f"video_{message.video.file_unique_id}.mp4"  # Use .mp4 extension for video files
                    file_path = os.path.join("/home/api.minzifatravel/static/files", filename)  # Полный путь для сохранения видео
                    await message.download(file_path)
                    filepath = f"crm-ut.com/static/files/{filename}"
                    content = message.caption or None
                elif message.voice:
                # Генерация уникального имени файла
                    filename = f"voice_{message.voice.file_unique_id}.ogg"
                    file_path = os.path.join("/home/api.minzifatravel/static/files", filename)  # Полный путь для сохранения голосового сообщения
                    await message.download(file_path)
                    filepath = f"crm-ut.com/static/files/{filename}"
                    content = message.caption or None
                elif message.text:
                    content = message.text

                user_message = Message(
                    text=codecs.encode(content, 'utf-8'),
                    lead = lead,
                    manager = None
                )

                if filename:
                        # Создание объекта файла и связь с сообщением, пользователем, менеджером и чатрумом
                        file = File(
                            filename=filename,
                            filepath=filepath,
                            lead=lead,
                            manager=None
                        )
                        db.add(file)
                        db.commit()
                        
                        user_message.file_id = file.id

                db.add(user_message)
                db.commit()

                while True:
                    
                    await asyncio.sleep(5)
                    available_manager = db.query(User).filter_by(role="Отдел продаж", language=lead.language, is_busy=False).first()
                    if available_manager:
                        # Присоединение пользователя к свободному менеджеру
                        lead.manager_id = available_manager.id

                        for message in lead.messages:
                             message.manager = available_manager

                        for file in lead.files:
                            file.manager = available_manager

                        available_manager.is_busy = True
                        db.commit()
                        await client.send_message(lead.chat_id, f"Добро пожаловать в MINZIFA TRAVEL!")
                        break
                
            

        #если уже есть
        content = None
        filename = None
        filepath = None

        if message.document:
            filename = message.document.file_name
            file_path = os.path.join("/home/api.minzifatravel/static/files", filename)  # Полный путь для сохранения файла
            await message.download(file_path)
            filepath = f"crm-ut.com/static/files/{filename}"
            content = message.caption or None
        elif message.photo:
            # Генерация уникального имени файла
            filename = f"photo_{message.photo.file_unique_id}.jpg"
            file_path = os.path.join("/home/api.minzifatravel/static/files", filename) # Полный путь для сохранения фото
            await message.download(file_path)
            filepath = f"crm-ut.com/static/files/{filename}"
            content = message.caption or None
        elif message.video:
            filename = f"video_{message.video.file_unique_id}.mp4"  # Use .mp4 extension for video files
            file_path = os.path.join("/home/api.minzifatravel/static/files", filename) # Полный путь для сохранения видео
            await message.download(file_path)
            filepath = f"crm-ut.com/static/files/{filename}"
            content = message.caption or None
        elif message.voice:
        # Генерация уникального имени файла
            filename = f"voice_{message.voice.file_unique_id}.ogg"
            file_path = os.path.join("/home/api.minzifatravel/static/files", filename)  # Полный путь для сохранения голосового сообщения
            await message.download(file_path)
            filepath = f"crm-ut.com/static/files/{filename}"
            content = message.caption or None
        elif message.text:
            content = message.text

        user_message = Message(
            text=codecs.encode(content, 'utf-8'),
            lead = lead,
            manager = lead.manager
        )

        if filename:
                # Создание объекта файла и связь с сообщением, пользователем, менеджером и чатрумом
                file = File(
                    filename=filename,
                    filepath=filepath,
                    lead=lead,
                    manager=lead.manager
                )
                db.add(file)
                db.commit()
                
                user_message.file_id = file.id

        db.add(user_message)
        db.commit()

tgclient.run()