from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    registered_at = Column(DateTime, default=datetime.utcnow)
    
    math_selected = Column(Boolean, default=False)
    russian_selected = Column(Boolean, default=False)
    history_selected = Column(Boolean, default=False)
    
    math_correct = Column(Integer, default=0)
    math_total = Column(Integer, default=0)
    russian_correct = Column(Integer, default=0)
    russian_total = Column(Integer, default=0)
    history_correct = Column(Integer, default=0)
    history_total = Column(Integer, default=0)
    
    # Связи
    daily_tasks = relationship("DailyTask", back_populates="user", foreign_keys="DailyTask.user_id")
    completed_tasks = relationship("CompletedTask", back_populates="user", foreign_keys="CompletedTask.user_id")

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(50), nullable=False)
    topic = Column(String(100), nullable=False)
    difficulty = Column(Integer, default=1)
    text = Column(Text, nullable=False)
    answer = Column(String(500), nullable=False)
    solution = Column(Text)
    
    # Связи
    daily_tasks = relationship("DailyTask", back_populates="task", foreign_keys="DailyTask.task_id")
    
    __table_args__ = (
        Index('idx_subject_topic', 'subject', 'topic'),
        Index('idx_subject', 'subject'),
    )

class DailyTask(Base):
    __tablename__ = 'daily_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    subject = Column(String(50), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="daily_tasks", foreign_keys=[user_id])
    task = relationship("Task", back_populates="daily_tasks", foreign_keys=[task_id])
    
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'date'),
        Index('idx_user_subject_date', 'user_id', 'subject', 'date'),
    )

class CompletedTask(Base):
    __tablename__ = 'completed_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subject = Column(String(50), nullable=False)
    is_correct = Column(Boolean, default=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="completed_tasks", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_user_subject', 'user_id', 'subject'),
        Index('idx_completed_at', 'completed_at'),
    )