from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Component(BaseModel):
    id: int
    name: str
    description: str

components = []

@app.post("/components/")
async def create_component(component: Component):
    for existing_component in components:
        if existing_component.id == component.id:
            raise HTTPException(status_code=400, detail="Component with this ID already exists")
    components.append(component)
    return component

@app.get("/components/")
async def read_components():
    return components

@app.get("/components/{component_id}")
async def read_component(component_id: int):
    for component in components:
        if component.id == component_id:
            return component
    raise HTTPException(status_code=404, detail="Component not found")

@app.put("/components/{component_id}")
async def update_component(component_id: int, component: Component):
    for existing_component in components:
        if existing_component.id == component_id:
            existing_component.name = component.name
            existing_component.description = component.description
            return existing_component
    raise HTTPException(status_code=404, detail="Component not found")

@app.delete("/components/{component_id}")
async def delete_component(component_id: int):
    for component in components:
        if component.id == component_id:
            components.remove(component)
            return {"message": "Component deleted successfully"}
    raise HTTPException(status_code=404, detail="Component not found")