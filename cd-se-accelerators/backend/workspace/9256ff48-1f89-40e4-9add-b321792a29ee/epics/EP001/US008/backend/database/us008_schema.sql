python
# database.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///tasks.db')
Base = declarative_base()
Session = sessionmaker(bind=engine)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String)

Base.metadata.create_all(engine)

def get_session():
    return Session()

def create_task(title):
    session = get_session()
    task = Task(title=title)
    session.add(task)
    session.commit()
    return task

def search_tasks(title):
    session = get_session()
    return session.query(Task).filter(Task.title.ilike(f'%{title}%')).all()