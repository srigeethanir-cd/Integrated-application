from pydantic import BaseModel, ConfigDict, Field, field_validator
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern=r"^[a-zA-Z][a-zA-Z0-9_]+$")
    password: str = Field(min_length=12, max_length=128)
    role: str = Field(default="user", pattern=r"^(user|admin)$")
    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if not any(c.isupper() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("password requires uppercase and digit")
        return value
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: str
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)
