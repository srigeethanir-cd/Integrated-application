# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Component(BaseModel):
    id: int
    name: str

# In-memory component storage
components = [
    Component(id=1, name="Component 1"),
    Component(id=2, name="Component 2"),
]

# GET /components
@app.get("/components")
async def get_components():
    return components

# GET /components/{component_id}
@app.get("/components/{component_id}")
async def get_component(component_id: int):
    for component in components:
        if component.id == component_id:
            return component
    raise HTTPException(status_code=404, detail="Component not found")

# POST /components
@app.post("/components")
async def create_component(component: Component):
    components.append(component)
    return component

# PUT /components/{component_id}
@app.put("/components/{component_id}")
async def update_component(component_id: int, component: Component):
    for existing_component in components:
        if existing_component.id == component_id:
            existing_component.name = component.name
            return existing_component
    raise HTTPException(status_code=404, detail="Component not found")

# DELETE /components/{component_id}
@app.delete("/components/{component_id}")
async def delete_component(component_id: int):
    for component in components:
        if component.id == component_id:
            components.remove(component)
            return {"message": "Component deleted"}
    raise HTTPException(status_code=404, detail="Component not found")