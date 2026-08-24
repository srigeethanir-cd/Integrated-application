from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import json

app = FastAPI()

class UserStory(BaseModel):
    id: int
    description: str
    status: str

class Module(BaseModel):
    name: str
    description: str

class APIEndpoint(BaseModel):
    method: str
    path: str
    description: str

class DatabaseSchema(BaseModel):
    tables: List[Dict]

class ProjectBlueprint(BaseModel):
    architecture: str
    modules: List[Module]
    api_endpoints: List[APIEndpoint]
    database_schema: DatabaseSchema

# In-memory data store for demonstration purposes
user_stories = [
    UserStory(id=1, description="User story 1", status="approved"),
    UserStory(id=2, description="User story 2", status="approved"),
    UserStory(id=3, description="User story 3", status="pending")
]

project_blueprints = {}

@app.post("/project-blueprint/")
async def generate_project_blueprint(user_stories_ids: List[int]):
    approved_user_stories = [user_story for user_story in user_stories if user_story.id in user_stories_ids and user_story.status == "approved"]
    
    if not approved_user_stories:
        raise HTTPException(status_code=400, detail="No approved user stories found")
    
    # Generate architecture blueprint
    architecture = "Microservices"
    
    # Identify required modules
    modules = [
        Module(name="module1", description="Module 1 description"),
        Module(name="module2", description="Module 2 description")
    ]
    
    # Generate API blueprint
    api_endpoints = [
        APIEndpoint(method="GET", path="/api/endpoint1", description="Endpoint 1 description"),
        APIEndpoint(method="POST", path="/api/endpoint2", description="Endpoint 2 description")
    ]
    
    # Create database schema
    database_schema = DatabaseSchema(tables=[
        {"name": "table1", "columns": ["column1", "column2"]},
        {"name": "table2", "columns": ["column3", "column4"]}
    ])
    
    # Create project blueprint
    project_blueprint = ProjectBlueprint(
        architecture=architecture,
        modules=modules,
        api_endpoints=api_endpoints,
        database_schema=database_schema
    )
    
    # Maintain traceability
    project_blueprints[json.dumps(user_stories_ids)] = project_blueprint
    
    return project_blueprint

@app.get("/project-blueprint/")
async def get_project_blueprint(user_stories_ids: List[int]):
    project_blueprint = project_blueprints.get(json.dumps(user_stories_ids))
    
    if not project_blueprint:
        raise HTTPException(status_code=404, detail="Project blueprint not found")
    
    return project_blueprint