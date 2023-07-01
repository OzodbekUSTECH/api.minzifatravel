from app.Administrator.schema import *
from app.manager.schema import *
from fastapi import APIRouter, Depends, UploadFile, File
from database.db import get_db
from app.utils import *

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
    prefix='/api/v1',
    tags = ['Task'],
    dependencies=[Depends(get_current_user)]
)





@router.post('/task', name = "create only own task", response_model=OwnTaskSchema)
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

@router.put('/task/{task_id}', name='change only own task data')
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



@router.put('/task/status/done', name = 'change any task status')
async def change_task_status(task_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, message="Task not found")
    if task.created_by != current_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, message="You can't change this task")
    task.is_done = True
    db.commit()
    #условие если это assoigned_task то логика с статистикой
    return {"message": "Задача успешно сделана!"}

@router.delete('/task/{task_id}', name='delete only own task')
async def delete_task(task_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    own_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not own_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена!")
    if own_task.created_by != current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не ваша задача, ошибка с айди")
    db.delete(own_task)
    db.commit()
    return {"message": "Задача удалена"}