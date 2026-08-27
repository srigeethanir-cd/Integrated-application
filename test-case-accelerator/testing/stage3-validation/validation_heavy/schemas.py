from datetime import date
import pydantic.v1 as pydantic_v1
from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

class LegacyReferral(pydantic_v1.BaseModel):
    code: str = pydantic_v1.Field(..., regex=r"^[A-Z]{3}-[0-9]{4}$")

class ProfileCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=24, pattern=r"^[a-z][a-z0-9_]+$", title="Username", description="Public account name", examples=["ada_1"])
    email: str = Field(..., min_length=6, max_length=200, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=12, max_length=128, pattern=r"^[A-Za-z0-9!@#$%^&*]+$")
    age: int = Field(..., ge=18, le=120)
    score: float = Field(default=0, gt=-1, lt=1001)
    referral_code: str | None = Field(default=None, pattern=r"^[A-Z]{3}-[0-9]{4}$")
    tags: list[str] = Field(default_factory=list, min_length=1, max_length=5)
    birth_date: date

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if not any(character.isupper() for character in value) or not any(
            character.isdigit() for character in value
        ):
            raise ValueError("password requires uppercase and digit")
        return value

    @field_validator("tags")
    @classmethod
    def unique_tags(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("tags must be unique")
        return value

    @model_validator(mode="after")
    def birth_date_matches_age(self):
        if date.today().year - self.birth_date.year < self.age:
            raise ValueError("birth date conflicts with age")
        return self

    @computed_field
    @property
    def display_name(self) -> str:
        return f"@{self.username}"

class ProfileOut(BaseModel):
    id: int
    username: str
    email: str
    age: int
    tags: list[str]
