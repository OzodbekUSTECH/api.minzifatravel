
from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship

from datetime import datetime

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    
    title = Column(String)
    description = Column(String, nullable=True)

    time_deadline = Column(String)
    date_deadline = Column(String)

    priority = Column(String)
    is_done = Column(Boolean, default=False)
    percent = Column(Numeric, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by= relationship("User", foreign_keys=[created_by_id], back_populates="created_tasks")

    assigned_to_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    assigned_staff = relationship("User", foreign_keys=[assigned_to_id], back_populates='assigned_tasks')


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    avatar = Column(String, nullable=True)
    full_name = Column(String, index=True)
    department = Column(String,  nullable=True, index=True) # Отдел продаж, Отдел бронирования, Отдел управления
    role = Column(String, nullable=True) #менеджер, Директор

    # If it's a manager
    language = Column(String, nullable=True)
    # status = Column(String, default='Работаю', index=True)
    is_busy = Column(Boolean, default=False, index=True)
    amount_finished_clients = Column(Integer, default=0, index=True)
    has_additional_client = Column(Boolean, default=False)

    email = Column(String, unique=True, index=True)
    password = Column(String)

    # Relationships
    clients = relationship("Lead", back_populates="manager")
    messages = relationship("Message", back_populates="manager")
    files = relationship("File", back_populates="manager")
    work_time = relationship("WorkTime", back_populates='staff')
    created_tasks = relationship("Task", foreign_keys=[Task.created_by_id], back_populates='created_by')
    assigned_tasks = relationship("Task", foreign_keys=[Task.assigned_to_id], back_populates='assigned_staff')


class Lead(Base):
    __tablename__= "clients"

    id = Column(Integer, primary_key=True, index=True)

    chat_id = Column(Integer, index=True, nullable=True)
    last_manager_update = Column(DateTime, default=datetime.utcnow, index=True)

    full_name = Column(String, index=True)
    phone_number = Column(String, nullable=True, index=True)
    email = Column(String, index=True, nullable=True)
    language = Column(String)

    manager_id = Column(Integer, ForeignKey('users.id'))
    manager = relationship("User", back_populates="clients")  # Изменено здесь

    created_at = Column(DateTime, default=datetime.utcnow)

    source = Column(String)  # WhatsApp/Tg/Insta/Web
    status = Column(String, default="Приветствие") 
    description = Column(String, nullable=True)
    
    files = relationship("File", back_populates="lead")
    messages = relationship("Message", back_populates="lead")
    
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=True)
    is_manager_message = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    file_id = Column(Integer, ForeignKey('files.id'))
    file = relationship("File", back_populates="message")

    lead_id = Column(Integer, ForeignKey('clients.id'))
    lead = relationship("Lead", back_populates='messages')

    manager_id = Column(Integer, ForeignKey('users.id'))
    manager = relationship("User", back_populates='messages')

class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=True)
    filepath = Column(String, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow)

    lead_id = Column(Integer, ForeignKey('clients.id'))
    lead = relationship("Lead", back_populates='files')

    manager_id = Column(Integer, ForeignKey("users.id"))
    manager = relationship("User", back_populates="files")

    message = relationship("Message", back_populates="file")


class WorkTime(Base):
    __tablename__ = 'work_time'

    id = Column(Integer, primary_key=True, index=True)

    staff_id = Column(Integer, ForeignKey('users.id'))
    staff = relationship("User", back_populates='work_time')

    date = Column(Date, index=True)  
    start_time = Column(Time, nullable=True)  
    end_time = Column(Time, nullable=True)