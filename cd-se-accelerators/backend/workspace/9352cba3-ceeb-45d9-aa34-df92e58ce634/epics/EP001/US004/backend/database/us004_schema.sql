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

    def __repr__(self):
        return f'Task(id={self.id}, title={self.title})'

Base.metadata.create_all(engine)

def create_task(title):
    session = Session()
    task = Task(title=title)
    session.add(task)
    session.commit()
    session.close()
    return task

def get_task(id):
    session = Session()
    task = session.query(Task).filter_by(id=id).first()
    session.close()
    return task