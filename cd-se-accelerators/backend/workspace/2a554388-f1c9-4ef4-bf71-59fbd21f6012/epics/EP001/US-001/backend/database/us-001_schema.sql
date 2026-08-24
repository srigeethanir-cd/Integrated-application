python
# database/models/component.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)

    def __repr__(self):
        return f"Component(id={self.id}, name='{self.name}', description='{self.description}')"

# database/repository/component_repository.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models.component import Base, Component

engine = create_engine("postgresql://user:password@host:port/dbname")
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

class ComponentRepository:
    def create_component(self, name: str, description: str):
        component = Component(name=name, description=description)
        session.add(component)
        session.commit()
        return component

    def get_all_components(self):
        return session.query(Component).all()

# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from database.repository.component_repository import ComponentRepository

app = FastAPI()

class ComponentRequest(BaseModel):
    name: str
    description: str

component_repository = ComponentRepository()

@app.post("/components")
async def create_component(request: ComponentRequest):
    component = component_repository.create_component(request.name, request.description)
    return {"id": component.id, "name": component.name, "description": component.description}

@app.get("/components")
async def get_all_components():
    components = component_repository.get_all_components()
    return [{"id": component.id, "name": component.name, "description": component.description} for component in components]