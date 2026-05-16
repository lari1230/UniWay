from sqlalchemy import create_engine, func, text, Date
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, date
from models import Base, User, Task, DailyTask, CompletedTask
import random
import urllib.parse
from config import SQL_SERVER_CONFIG

class Database:
    def __init__(self):
        # Формируем строку подключения для SQL Server через pyodbc
        if SQL_SERVER_CONFIG.get('trusted_connection', '').lower() == 'yes':
            params = {
                'driver': SQL_SERVER_CONFIG['driver'],
                'server': SQL_SERVER_CONFIG['server'],
                'database': SQL_SERVER_CONFIG['database'],
                'trusted_connection': 'yes'
            }
        else:
            params = {
                'driver': SQL_SERVER_CONFIG['driver'],
                'server': SQL_SERVER_CONFIG['server'],
                'database': SQL_SERVER_CONFIG['database'],
                'uid': SQL_SERVER_CONFIG['username'],
                'pwd': SQL_SERVER_CONFIG['password']
            }
        
        encoded_params = urllib.parse.quote_plus(';'.join([f"{k}={v}" for k, v in params.items()]))
        connection_string = f"mssql+pyodbc:///?odbc_connect={encoded_params}"
        
        print(f"Подключение к SQL Server: {SQL_SERVER_CONFIG['server']}")
        print(f"База данных: {SQL_SERVER_CONFIG['database']}")
        
        self.engine = create_engine(
            connection_string,
            echo=False,
            pool_size=10,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        
        # Создаем таблицы только если их нет
        Base.metadata.create_all(self.engine)
        
        self.Session = scoped_session(sessionmaker(bind=self.engine))
    
    def get_session(self):
        return self.Session()
    
    def add_user(self, telegram_id, username=None, first_name=None, last_name=None):
        session = self.get_session()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
                session.commit()
            return user
        finally:
            session.close()
    
    def get_user(self, telegram_id):
        session = self.get_session()
        try:
            return session.query(User).filter_by(telegram_id=telegram_id).first()
        finally:
            session.close()
    
    def update_user_subjects(self, telegram_id, subjects):
        session = self.get_session()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                user.math_selected = subjects.get('math', False)
                user.russian_selected = subjects.get('russian', False)
                user.history_selected = subjects.get('history', False)
                session.commit()
        finally:
            session.close()
    
    def get_tasks_by_subject_topic(self, subject, topic=None):
        session = self.get_session()
        try:
            query = session.query(Task).filter_by(subject=subject)
            if topic:
                query = query.filter_by(topic=topic)
            return query.all()
        finally:
            session.close()
    
    def get_task_by_id(self, task_id):
        session = self.get_session()
        try:
            return session.query(Task).filter_by(id=task_id).first()
        finally:
            session.close()
    
    def add_task(self, subject, topic, difficulty, text, answer, solution):
        """Добавление одного задания (для администрирования)"""
        session = self.get_session()
        try:
            task = Task(
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                text=text,
                answer=answer,
                solution=solution
            )
            session.add(task)
            session.commit()
            return task
        finally:
            session.close()
    
    def get_topics_by_subject(self, subject):
        session = self.get_session()
        try:
            topics = session.query(Task.topic).filter_by(subject=subject).distinct().all()
            return [topic[0] for topic in topics]
        finally:
            session.close()
    
    def get_daily_task(self, user_id, subject):
        session = self.get_session()
        try:
            today = date.today()
            daily_task = session.query(DailyTask).filter(
                DailyTask.user_id == user_id,
                DailyTask.subject == subject,
                func.cast(DailyTask.date, Date) == today
            ).first()
            
            if daily_task:
                return daily_task.task
            return None
        finally:
            session.close()
    
    def create_daily_tasks(self, user_id, subjects):
        session = self.get_session()
        try:
            today = date.today()
            created_tasks = []
            
            for subject in subjects:
                existing = session.query(DailyTask).filter(
                    DailyTask.user_id == user_id,
                    DailyTask.subject == subject,
                    func.cast(DailyTask.date, Date) == today
                ).first()
                
                if not existing:
                    tasks = session.query(Task).filter_by(subject=subject).all()
                    if tasks:
                        task = random.choice(tasks)
                        daily_task = DailyTask(
                            user_id=user_id,
                            task_id=task.id,
                            subject=subject,
                            date=datetime.now()
                        )
                        session.add(daily_task)
                        created_tasks.append((subject, task))
            
            session.commit()
            return created_tasks
        finally:
            session.close()
    
    def check_daily_task_answer(self, user_id, subject, answer):
        session = self.get_session()
        try:
            today = date.today()
            daily_task = session.query(DailyTask).filter(
                DailyTask.user_id == user_id,
                DailyTask.subject == subject,
                func.cast(DailyTask.date, Date) == today
            ).first()
            
            if daily_task and not daily_task.completed:
                task = daily_task.task
                is_correct = task.answer.lower().strip() == answer.lower().strip()
                
                if is_correct:
                    daily_task.completed = True
                    
                    user = session.query(User).filter_by(id=user_id).first()
                    if subject == 'math':
                        user.math_correct += 1
                        user.math_total += 1
                    elif subject == 'russian':
                        user.russian_correct += 1
                        user.russian_total += 1
                    elif subject == 'history':
                        user.history_correct += 1
                        user.history_total += 1
                    
                    session.commit()
                    return task, is_correct, task.solution
                else:
                    user = session.query(User).filter_by(id=user_id).first()
                    if subject == 'math':
                        user.math_total += 1
                    elif subject == 'russian':
                        user.russian_total += 1
                    elif subject == 'history':
                        user.history_total += 1
                    session.commit()
                    return task, is_correct, task.solution
            
            return None, False, None
        finally:
            session.close()
    
    def complete_practice_task(self, user_id, task_id, subject, is_correct):
        session = self.get_session()
        try:
            # Убрали task_id из таблицы completed_tasks
            completed = CompletedTask(
                user_id=user_id,
                subject=subject,
                is_correct=is_correct
            )
            session.add(completed)
        
            user = session.query(User).filter_by(id=user_id).first()
            if subject == 'math':
                if is_correct:
                    user.math_correct += 1
                user.math_total += 1
            elif subject == 'russian':
                if is_correct:
                    user.russian_correct += 1
                user.russian_total += 1
            elif subject == 'history':
                if is_correct:
                    user.history_correct += 1
                user.history_total += 1
        
            session.commit()
        finally:
            session.close()
    
    def get_user_statistics(self, user_id):
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                stats = {}
                for subject in ['math', 'russian', 'history']:
                    correct = getattr(user, f'{subject}_correct')
                    total = getattr(user, f'{subject}_total')
                    percentage = (correct / total * 100) if total > 0 else 0
                    stats[subject] = {
                        'correct': correct,
                        'total': total,
                        'percentage': round(percentage, 1)
                    }
                return stats
            return None
        finally:
            session.close()
    
    def check_connection(self):
        """Проверяет подключение к SQL Server"""
        try:
            session = self.get_session()
            result = session.execute(text("SELECT @@VERSION")).fetchone()
            print(f"✅ Подключено к SQL Server: {result[0][:50]}...")
            session.close()
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к SQL Server: {e}")
            return False
    
    # Этот метод вызывать только при необходимости (например, для администрирования)
    def add_sample_data_if_empty(self):
        """Добавляет примерные задания только если таблица tasks пуста"""
        session = self.get_session()
        try:
            # Проверяем, есть ли уже задания
            count = session.query(Task).count()
            if count > 0:
                print(f"✅ В базе данных уже есть {count} заданий. Пропускаем добавление.")
                return
            
            print("База данных пуста. Добавляем примерные задания...")
            
            # Здесь код добавления заданий (только если таблица пуста)
            # ... (ваши задания)
            
            session.commit()
            print(f"✅ Добавлены задания")
        except Exception as e:
            print(f"❌ Ошибка при добавлении заданий: {e}")
            session.rollback()
        finally:
            session.close()