from fastapi import HTTPException, status


class UserNotFound(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


class EmailConflict(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")


class InvalidCredentials(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})

