python
# database.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Component(BaseModel):
    id: int
    name: str

# Create a dictionary to simulate a database
components = {}

# Create a route to create a new component
@app.post("/components/")
def create_component(component: Component):
    components[component.id] = component
    return component

# Create a route to get all components
@app.get("/components/", response_model=List[Component])
def get_components():
    return list(components.values())

# Create a route to get a component by id
@app.get("/components/{component_id}", response_model=Component)
def get_component(component_id: int):
    return components.get(component_id)

# Create a route to update a component
@app.put("/components/{component_id}", response_model=Component)
def update_component(component_id: int, component: Component):
    components[component_id] = component
    return component

# Create a route to delete a component
@app.delete("/components/{component_id}")
def delete_component(component_id: int):
    if component_id in components:
        del components[component_id]
        return {"message": "Component deleted successfully"}
    else:
        return {"message": "Component not found"}