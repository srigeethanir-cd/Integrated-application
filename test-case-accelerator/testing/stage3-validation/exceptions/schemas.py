from pydantic import BaseModel, Field
class JobCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
class JobOut(BaseModel):
    id: int
    name: str
    state: str
