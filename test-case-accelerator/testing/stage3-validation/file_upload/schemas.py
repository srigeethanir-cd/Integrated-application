from pydantic import BaseModel, ConfigDict, Field
class FileMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    content_type: str
    label: str
    size: int = Field(ge=1, le=1_048_576)
