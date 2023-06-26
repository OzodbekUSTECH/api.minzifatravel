from pyrogram import Client, filters
from app.models import *
from pyrogram.types import Message as TelegramMessage
import os
from sqlalchemy import desc
import asyncio
from database.db import Session
from datetime import datetime

# Установите соединение с базой данных


# Введите ваш API ID и API Hash
api_id = '20122546'
api_hash = 'c3ca5ae4e368b18eccd06a5edcd7eec0'

# Создайте экземпляр клиента Pyrogram
tgclient = Client("your_session_name", api_id=api_id, api_hash=api_hash)

db = Session()
@tgclient.on_message(filters.private & filters.incoming)
async def handle_private_message(client: Client, message: TelegramMessage):
    # Проверка, является ли отправитель пользователем
    if message.from_user:
        lead_id = message.from_user.id
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""

        # Поиск пользователя в базе данных
        lead = db.query(Lead).filter_by(chat_id=lead_id).first()

        if not lead:
            # Создание нового пользователя
            lead = Lead(chat_id=lead_id, full_name=f"{first_name} {last_name}", language="Both", source="Telegram")
            db.add(lead)
            db.commit()

            # Поиск свободного менеджера
            available_manager = db.query(User).filter_by(role="manager", language=lead.language, status="Free").first()
            better_manager = db.query(User).filter_by(role="manager", language=lead.language, has_additional_client=False).order_by(desc(User.amount_finished_clients)).first()
            if available_manager:
                # Присоединение пользователя к свободному менеджеру
                lead.manager_id = available_manager.id
                available_manager.status = "Busy"
                db.commit()

                await client.send_message(lead.chat_id, f"Добро пожаловать в MINZIFA TRAVEL!")
            elif better_manager:
                # await client.send_message(message.chat.id, "Извините, в данный момент все менеджеры заняты. Пожалуйста, ожидайте.")
                better_manager.has_additional_client = True
                lead.manager_id = better_manager.id
                db.commit()
                await client.send_message(lead.chat_id, f"Добро пожаловать в MINZIFA TRAVEL!")
            else:
                await client.send_message(lead.chat_id, "<b><em>Добро пожаловать в MINZIFA TRAVEL!</em></b>\n\nИзвините, в данный момент все менеджеры заняты. Пожалуйста, ожидайте.")
                
                content = None
                filename = None
                filepath = None

                if message.document:
                    filename = message.document.file_name
                    file_path = os.path.join("D:\\ozod\\tgProject\\files", filename)  # Полный путь для сохранения файла
                    await message.download(file_path)
                    filepath = file_path
                    content = message.caption or None
                elif message.photo:
                    # Генерация уникального имени файла
                    filename = f"photo_{message.photo.file_unique_id}.jpg"
                    file_path = os.path.join("D:\\ozod\\tgProject\\files", filename)  # Полный путь для сохранения фото
                    await message.download(file_path)
                    filepath = file_path
                    content = message.caption or None
                elif message.video:
                    filename = f"video_{message.video.file_unique_id}.mp4"  # Use .mp4 extension for video files
                    file_path = os.path.join("D:\\ozod\\tgProject\\files", filename)  # Полный путь для сохранения видео
                    await message.download(file_path)
                    filepath = file_path
                    content = message.caption or None
                elif message.text:
                    content = message.text

                user_message = Message(
                    text=content,
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
                    available_manager = db.query(User).filter_by(role="manager", language=lead.language, status="Free").first()
                    if available_manager:
                        # Присоединение пользователя к свободному менеджеру
                        lead.manager_id = available_manager.id

                        for message in lead.messages:
                             message.manager = available_manager

                        for file in lead.files:
                            file.manager = available_manager

                        available_manager.status = "Busy"
                        db.commit()
                        await client.send_message(lead.chat_id, f"Добро пожаловать в MINZIFA TRAVEL!")
                        break
                
            

        #если уже есть
        content = None
        filename = None
        filepath = None

        if message.document:
            filename = message.document.file_name
            file_path = os.path.join("D:\\ozod\\tgProject\\files", filename)  # Полный путь для сохранения файла
            await message.download(file_path)
            filepath = file_path
            content = message.caption or None
        elif message.photo:
            # Генерация уникального имени файла
            filename = f"photo_{message.photo.file_unique_id}.jpg"
            file_path = os.path.join("D:\\ozod\\tgProject\\files", filename)  # Полный путь для сохранения фото
            await message.download(file_path)
            filepath = file_path
            content = message.caption or None
        elif message.video:
            filename = f"video_{message.video.file_unique_id}.mp4"  # Use .mp4 extension for video files
            file_path = os.path.join("D:\\ozod\\tgProject\\files", filename)  # Полный путь для сохранения видео
            await message.download(file_path)
            filepath = file_path
            content = message.caption or None
        elif message.text:
            content = message.text

        user_message = Message(
            text=content,
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




        