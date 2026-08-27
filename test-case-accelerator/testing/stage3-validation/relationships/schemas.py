from pydantic import BaseModel, ConfigDict, Field
class AuthorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    isbn: str = Field(pattern=r"^[0-9-]{10,20}$")
    publisher_name: str = Field(min_length=2)
class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    isbn: str
