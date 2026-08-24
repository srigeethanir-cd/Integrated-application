python
# database.py
from sqlalchemy import create_engine, Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///tasks.db')
Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    status = Column(Enum('completed', 'pending'))

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

def create_task(title, status):
    task = Task(title=title, status=status)
    session.add(task)
    session.commit()

def filter_tasks_by_status(status):
    return session.query(Task).filter_by(status=status).all()

def get_all_tasks():
    return session.query(Task).all()