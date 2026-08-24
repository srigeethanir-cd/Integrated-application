# Component.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ComponentRequest(BaseModel):
    id: int
    name: str

class ComponentResponse(BaseModel):
    id: int
    name: str
    status: str

# In-memory data store for demonstration purposes
components = [
    {"id": 1, "name": "Component 1", "status": "active"},
    {"id": 2, "name": "Component 2", "status": "inactive"},
]

@app.post("/components/")
async def create_component(request: ComponentRequest):
    """
    Create a new component.

    Args:
    request (ComponentRequest): The component request.

    Returns:
    ComponentResponse: The created component response.
    """
    component = {"id": request.id, "name": request.name, "status": "active"}
    components.append(component)
    return ComponentResponse(**component)

@app.get("/components/{component_id}")
async def get_component(component_id: int):
    """
    Get a component by ID.

    Args:
    component_id (int): The component ID.

    Returns:
    ComponentResponse: The component response.

    Raises:
    HTTPException: If the component is not found.
    """
    for component in components:
        if component["id"] == component_id:
            return ComponentResponse(**component)
    raise HTTPException(status_code=404, detail="Component not found")

@app.put("/components/{component_id}")
async def update_component(component_id: int, request: ComponentRequest):
    """
    Update a component.

    Args:
    component_id (int): The component ID.
    request (ComponentRequest): The component request.

    Returns:
    ComponentResponse: The updated component response.

    Raises:
    HTTPException: If the component is not found.
    """
    for component in components:
        if component["id"] == component_id:
            component["name"] = request.name
            return ComponentResponse(**component)
    raise HTTPException(status_code=404, detail="Component not found")

@app.delete("/components/{component_id}")
async def delete_component(component_id: int):
    """
    Delete a component.

    Args:
    component_id (int): The component ID.

    Returns:
    None

    Raises:
    HTTPException: If the component is not found.
    """
    for component in components:
        if component["id"] == component_id:
            components.remove(component)
            return
    raise HTTPException(status_code=404, detail="Component not found")