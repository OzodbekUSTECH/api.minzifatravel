from fastapi import APIRouter, HTTPException, Depends, status
from database.db import get_db
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from app.utils import *
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix='/api/v1/administrator',
    tags = ['Administrator'],
    dependencies=[Depends(get_current_user)]
)


@router.get('/users/', name="get all users by a range of date and page", response_model=list[UserSchema])
async def get_all_users(date_from: date = None, date_to: date = None, page: int = 1, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")

    if date_from is None:
        date_from = datetime.combine(date.today(), datetime.min.time())
    if date_to is None:
        date_to = datetime.combine(date.today(), datetime.max.time())

    all_users = db.query(models.User).filter(models.User.created_at.between(date_from, date_to)).order_by('id').all()

    leads_per_page = 100
    start_index = (page - 1) * leads_per_page
    end_index = start_index + leads_per_page
    paginated_users = all_users[start_index:end_index]

    return paginated_users



@router.get('/leads/', name="get all leads by a range of date and page", response_model=list[LeadSchema])
async def get_all_leads(date_from: date = None, date_to: date = None, page: int = 1, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")

    if date_from is None:
        date_from = datetime.combine(date.today(), datetime.min.time())
    if date_to is None:
        date_to = datetime.combine(date.today(), datetime.max.time())


    all_leads = db.query(models.Lead).filter(models.Lead.created_at.between(date_from, date_to)).order_by(models.Lead.id).all()

    leads_per_page = 100
    start_index = (page - 1) * leads_per_page
    end_index = start_index + leads_per_page
    paginated_leads = all_leads[start_index:end_index]

    response = []
    for lead in paginated_leads:
        lead_data = LeadSchema(
            id=lead.id,
            manager_id=lead.manager_id,
            full_name=lead.full_name,
            phone_number=lead.phone_number,
            email=lead.email,
            language=lead.language,
            source=lead.source,
            created_at=lead.created_at,
            status=lead.status,
            last_update=lead.last_manager_update,
            description=lead.description,
        )
        response.append(lead_data)
    return response

@router.get('/{manager_id}/chat/{lead_id}', name="get all chats by a range of date and page", response_model=list[MessageSchema])
async def get_all_leads(manager_id: int, lead_id: int, page: int = 1, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")

    chat = db.query(models.Message).filter(models.Message.manager_id == manager_id, models.Message.lead_id == lead_id).order_by('id').all()

    leads_per_page = 100
    start_index = (page - 1) * leads_per_page
    end_index = start_index + leads_per_page
    paginated_chat = chat[start_index:end_index]

    response = []
   
    return paginated_chat

@router.get('/user/{user_id}', name='get any user by id', response_model = UserSchema)
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
            manager_id = client.manager_id,
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


@router.post('/user', summary="Create a new user", response_model=RegUserSchemaResponse)
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


@router.put('/user/{user_id}', name='update user data', response_model=RegUserSchemaResponse)
async def change_user_data(user_id: int, user: UserUpdateSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    
    user_update = db.query(models.User).filter(models.User.id == user_id).first()

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




@router.put('/user/{user_id}/password', name = "chagne password of user")
async def change_user_password(user_id: int, user: UserUpdatePasswordSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    
    user_update = db.query(models.User).filter(models.User.id == user_id).first()
    if verify_password(user.old_password, user_update.password):
        new_hashed_password = pwd_context.hash(user.new_password)
        user_update.password = new_hashed_password
        db.commit()
        return {"message": "Password changed"}
    else:
        raise HTTPException(status_code=400, detail="Неверный пароль")


@router.delete('/user/{user_id}', name = "delete an user")
async def delete_user(user_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    db.delete(user)
    db.commit()
    return {"message": "Пользователь удален!"}
#######################tasks################

@router.get('/tasks', name='get all tasks that have been assigned to someone', response_model=List[TaskSchema])
async def get_all_tasks(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    all_tasks = db.query(models.Task).filter(models.Task.assigned_to_id != None).order_by(models.Task.id).all()
    return all_tasks


@router.post('/task', name='Create a task only to someone', response_model=TaskSchema)
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

@router.get('/tasks/{user_id}', name='get tasks of user that are assigned to', summary='Прикрепленные задачи этого юзера от директоров',  response_model=list[TaskSchema])
async def get_tasks_of_user(user_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    all_tasks = db.query(models.Task).filter(models.Task.assigned_to_id == user_id).order_by(models.Task.id).all()
    return all_tasks

@router.get('/task/{task_id}', name='get task by id', response_model=TaskSchema)
async def get_task_by_id(task_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена.")
    return task




@router.put('/task/{task_id}', name='update task data', response_model=TaskSchema)
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

@router.delete('/task/{task_id}', name='delete an assigned task')
async def delete_task(task_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    db_task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.assigned_to_id != None).first()
    if db_task:
        db.delete(db_task)
        db.commit()
        return {"message": "Задача успешно удалена."}
    else:
        raise HTTPException(status_code=404, detail="Задача не найдена.")


from app.workingtime.schema import *
#working times of managers

@router.get("/workingtime/dates", name='get workingtimes of users', response_model=list[AllWorkTimeSchema])
def get_all_users_by_dates(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    users = db.query(models.WorkTime).order_by('id').all()

    return users


@router.get("/workingtime/dates/{date}", name='get all staff with working time for a specific date', response_model=List[AllWorkTimeSchema])
def get_all_users_by_date(date: date, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    users = db.query(models.WorkTime).filter(models.WorkTime.date == date).order_by(models.WorkTime.id).all()

    return users

@router.get("/workingtime/range/dates", name='get all staff with working time for a range of dates', response_model=List[AllWorkTimeSchema])
async def get_all_users_by_range(start_date: date, end_date: Optional[date] = None,current_user=Depends(get_current_user), db: Session = Depends(get_db)):
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
            date=user.date,
            start_time=user.start_time,
            end_time=user.end_time
        )
        response.append(user_data)

    return response
@router.put('/{lead_id}/change/{user_id}', name = 'change manager of lead')
async def change_manager(lead_id: int, user_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    db_client = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Клиент не найден.")
    new_manager = db.query(models.User).filter(models.User.id == user_id).first()

    db_client.manager = new_manager
    for message in db_client.messages:
        message.manager = new_manager
    
    db.commit()

    return {"message": "Менеджер у клиент сменен"}

####################################avatar



@router.delete('/lead/{lead_id}', name='delete lead(client)')
async def delete_lead(lead_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "Отдел управления":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Лид не найден.")
    db.delete(lead)
    db.commit()

    return {"message": "Лид успешно удален!"}

