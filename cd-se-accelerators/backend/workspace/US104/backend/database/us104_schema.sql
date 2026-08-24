python
# database.py
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

# Create a database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///component.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = declarative_base()

# Define a model for the component
class Component(Base):
    __tablename__ = "components"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, index=True)

# Create all tables in the engine
Base.metadata.create_all(engine)

# Create a dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define a pydantic model for the component
class ComponentModel(BaseModel):
    name: str
    description: str

# Create a FastAPI app
app = FastAPI()

# Create a route to create a new component
@app.post("/components/")
def create_component(component: ComponentModel, db: Session = Depends(get_db)):
    db_component = Component(name=component.name, description=component.description)
    db.add(db_component)
    db.commit()
    db.refresh(db_component)
    return db_component

# Create a route to get all components
@app.get("/components/")
def get_components(db: Session = Depends(get_db)):
    return db.query(Component).all()