# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    id: int
    name: str
    email: str

# In-memory data store for demonstration purposes
users = []

@app.post("/users/")
async def create_user(user: User):
    """
    Create a new user.

    Args:
    user (User): The user to create.

    Returns:
    User: The created user.
    """
    # Check if user with same email already exists
    for existing_user in users:
        if existing_user.email == user.email:
            raise HTTPException(status_code=400, detail="Email already in use")

    # Add user to in-memory data store
    users.append(user)
    return user

@app.get("/users/")
async def read_users():
    """
    Read all users.

    Returns:
    list[User]: A list of all users.
    """
    return users

@app.get("/users/{user_id}")
async def read_user(user_id: int):
    """
    Read a user by ID.

    Args:
    user_id (int): The ID of the user to read.

    Returns:
    User: The user with the given ID.
    """
    for user in users:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.put("/users/{user_id}")
async def update_user(user_id: int, user: User):
    """
    Update a user.

    Args:
    user_id (int): The ID of the user to update.
    user (User): The updated user.

    Returns:
    User: The updated user.
    """
    for existing_user in users:
        if existing_user.id == user_id:
            existing_user.name = user.name
            existing_user.email = user.email
            return existing_user
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """
    Delete a user.

    Args:
    user_id (int): The ID of the user to delete.

    Returns:
    None
    """
    for user in users:
        if user.id == user_id:
            users.remove(user)
            return
    raise HTTPException(status_code=404, detail="User not found")