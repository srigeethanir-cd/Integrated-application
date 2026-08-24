python
# database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Create a database engine
engine = create_engine('sqlite:///tasks.db')

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

# Define the Task model
class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create all tables in the engine
Base.metadata.create_all(engine)

# Create a new session
session = Session()