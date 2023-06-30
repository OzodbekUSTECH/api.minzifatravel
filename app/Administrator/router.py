from fastapi import APIRouter, HTTPException, Depends, status
from database.db import get_db
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from app.utils import *
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix='/administrator',
    tags = ['Administrator'],
    dependencies=[Depends(get_current_user)]
)




@router.post('/registration', summary="Create a new user", response_model=RegUserSchemaResponse)
async def register(user: UserCreateSchema,current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")

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

    return db_user



@router.get('/get_all_staff', name="get list of staff with their clients and full chats(except yourself)", response_model=list[UserSchema])
async def get_all_staff(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")

    all_staff = db.query(models.User).filter(models.User.id != current_user.id).order_by('id').all()
    response = []
    for staff in all_staff:
        clients = []
        for client in staff.clients:
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
                language=client.language,
                source=client.source,
                created_at=client.created_at,
                status=client.status,
                last_update=client.last_manager_update,
                description=client.description,
                chat = messages_response
            )
            clients.append(client_data)

        staff_data = UserSchema(
            id=staff.id,
            full_name=staff.full_name,
            email=staff.email,
            department=staff.department,
            role=staff.role,
            language=staff.language,
            is_busy=staff.is_busy,
            amount_finished_clients=staff.amount_finished_clients,
            clients=clients 
        )
        response.append(staff_data)

    return response


@router.get('/get_user/{user_id}', name='get any user by id', response_model = UserSchema)
async def get_user_by_id(user_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    
    staff = db.query(models.User).filter(models.User.id == user_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    clients = []
    for client in staff.clients:
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
            language=client.language,
            source=client.source,
            created_at=client.created_at,
            status=client.status,
            last_update=client.last_manager_update,
            description=client.description,
            chat = messages_response
        )
        clients.append(client_data)
    user_data = UserSchema(
            id=staff.id,
            avatar=staff.avatar,
            full_name=staff.full_name,
            email=staff.email,
            department=staff.department,
            role=staff.role,
            language=staff.language,
            is_busy=staff.is_busy,
            amount_finished_clients=staff.amount_finished_clients,
            clients=clients 
        )
    return user_data



@router.put('/change/{manager_id}/data', response_model=RegUserSchemaResponse)
async def change_user_data(manager_id: int, user: UserUpdateSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    
    user_update = db.query(models.User).filter(models.User.id == manager_id).first()

    if user.full_name is not None:
        user_update.full_name = user.full_name
    if user.email is not None:
        user_update.email = user.email
    if user.department is not None:
        user_update.department = user.department
    if user.role is not None:
        user_update.role = user.role
    if user.language is not None:
        user_update.language = user.language


    db.commit()
    db.refresh(user_update)
    return user_update

@router.put('/change/{manager_id}/password')
async def change_user_password(manager_id: int, user: UserUpdatePasswordSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    
    user_update = db.query(models.User).filter(models.User.id == manager_id).first()
    if verify_password(user.old_password, user_update.password):
        new_hashed_password = pwd_context.hash(user.new_password)
        user_update.password = new_hashed_password
        db.commit()
        return {"message": "Password changed"}
    else:
        raise HTTPException(status_code=400, detail="Неверный пароль")

@router.delete('/delete/{user_id}')
async def delete_user(user_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    db.delete(user)
    db.commit()
    return {"message": "Пользователь удален!"}

@router.get('/get_all_tasks', response_model=List[TaskSchema])
async def get_all_tasks(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    all_tasks = db.query(models.Task).order_by(models.Task.id).all()
    return all_tasks


@router.post('/create_task', response_model=TaskSchema)
async def create_task(task: CreateTaskSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")


    db_task = models.Task(
        assigned_to_id=task.assigned_to_id,
        title=task.title,
        description=task.description,
        time_deadline=task.time_deadline,
        date_deadline=task.date_deadline,
        priority=task.priority,
        percent = task.percent,
        created_by=current_user
    )
    db.add(db_task)
    db.commit()
    return db_task

@router.put('/update_task/{task_id}', response_model=TaskSchema)
async def update_task(task_id: int, updated_task: UpdateTaskSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Задача не найдена.")

    # Обновление полей задачи, если они указаны в запросе
    if updated_task.assigned_to_id is not None:
        db_task.assigned_to_id = updated_task.assigned_to_id
    if updated_task.title is not None:
        db_task.title = updated_task.title
    if updated_task.description is not None:
        db_task.description = updated_task.description
    if updated_task.time_deadline is not None:
        db_task.time_deadline = updated_task.time_deadline
    if updated_task.date_deadline is not None:
        db_task.date_deadline = updated_task.date_deadline
    if updated_task.priority is not None:
        db_task.priority = updated_task.priority
    if updated_task.percent is not None:
        db_task.percent = updated_task.percent

    db.commit()
    db.refresh(db_task)
    
    return db_task

@router.delete('/delete_task')
async def delete_task(task_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
        return {"message": "Задача успешно удалена."}
    else:
        raise HTTPException(status_code=404, detail="Задача не найдена.")


from app.workingtime.schema import *
#working times of managers
@router.get("/workingtime/dates_all", name='get all dates and their staff with working time', response_model=list[WorkDateSchema])
def get_all_users_by_dates(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    users = db.query(models.WorkTime).order_by(models.WorkTime.date, models.WorkTime.staff_id).all()

    result = {}
    for user in users:
        date_str = user.date  

        user_data = WorkTimeSchema(
            id=user.staff.id,
            full_name=user.staff.full_name,
            start_time=user.start_time,
            end_time=user.end_time,
        )
        if date_str in result:
            result[date_str].append(user_data)
        else:
            result[date_str] = [user_data]
    
    response = []
    for date_str, staff in result.items():
        date_data = WorkDateSchema(date=date_str, staff=staff)
        response.append(date_data)
    return response


@router.get("/workingtime/dates/{date}", name='get all staff with working time for a specific date', response_model=List[AllWorkTimeSchema])
def get_all_users_by_date(date: date, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    users = db.query(models.WorkTime).filter(models.WorkTime.date == date).order_by(models.WorkTime.id).all()

    response = []
    for user in users:
        user_data = AllWorkTimeSchema(
            id=user.id,
            staff_id=user.staff.id,
            full_name=user.staff.full_name,
            date=user.date,
            start_time=user.start_time,
            end_time=user.end_time
        )
        response.append(user_data)

    return response

@router.get("/workingtime/range/dates", name='get all staff with working time for a range of dates', response_model=List[AllWorkTimeSchema])
def get_all_users_by_range(start_date: date, end_date: Optional[date] = None,current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    query = db.query(models.WorkTime).filter(models.WorkTime.date >= start_date)

    if end_date:
        query = query.filter(models.WorkTime.date <= end_date)

    users = query.order_by('id').all()
    response = []
    for user in users:
        user_data = AllWorkTimeSchema(
            id=user.id,
            staff_id=user.staff.id,
            full_name=user.staff.full_name,
            date=user.date,
            start_time=user.start_time,
            end_time=user.end_time
        )
        response.append(user_data)

    return response

@router.put('/{client_id}/change/{manager_id}')
async def change_manager(client_id: int, manager_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    db_client = db.query(models.Lead).filter(models.Lead.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Клиент не найден.")
    new_manager = db.query(models.User).filter(models.User.id == manager_id).first()

    db_client.manager = new_manager
    for message in db_client.messages:
        message.manager = new_manager
    
    db.commit()

    return {"message": "Менеджер у клиент сменен"}





####################################avatar


