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
    {"id": 2, "name": "Component 2", "status": "inactive"}
]

@app.post("/components/")
async def create_component(request: ComponentRequest):
    """
    Creates a new component.

    Args:
    request (ComponentRequest): The request body containing the component details.

    Returns:
    ComponentResponse: The created component details.
    """
    # Validate the request
    if not request.id or not request.name:
        raise HTTPException(status_code=400, detail="Invalid request")

    # Create a new component
    new_component = {"id": request.id, "name": request.name, "status": "active"}
    components.append(new_component)

    # Return the created component
    return ComponentResponse(id=new_component["id"], name=new_component["name"], status=new_component["status"])

@app.get("/components/{component_id}")
async def get_component(component_id: int):
    """
    Retrieves a component by ID.

    Args:
    component_id (int): The ID of the component to retrieve.

    Returns:
    ComponentResponse: The retrieved component details.
    """
    # Find the component
    component = next((c for c in components if c["id"] == component_id), None)

    # Return the component if found
    if component:
        return ComponentResponse(id=component["id"], name=component["name"], status=component["status"])
    else:
        raise HTTPException(status_code=404, detail="Component not found")

@app.put("/components/{component_id}")
async def update_component(component_id: int, request: ComponentRequest):
    """
    Updates a component.

    Args:
    component_id (int): The ID of the component to update.
    request (ComponentRequest): The request body containing the updated component details.

    Returns:
    ComponentResponse: The updated component details.
    """
    # Find the component
    component = next((c for c in components if c["id"] == component_id), None)

    # Update the component if found
    if component:
        component["name"] = request.name
        return ComponentResponse(id=component["id"], name=component["name"], status=component["status"])
    else:
        raise HTTPException(status_code=404, detail="Component not found")

@app.delete("/components/{component_id}")
async def delete_component(component_id: int):
    """
    Deletes a component.

    Args:
    component_id (int): The ID of the component to delete.

    Returns:
    None
    """
    # Find the component
    component = next((c for c in components if c["id"] == component_id), None)

    # Delete the component if found
    if component:
        components.remove(component)
    else:
        raise HTTPException(status_code=404, detail="Component not found")