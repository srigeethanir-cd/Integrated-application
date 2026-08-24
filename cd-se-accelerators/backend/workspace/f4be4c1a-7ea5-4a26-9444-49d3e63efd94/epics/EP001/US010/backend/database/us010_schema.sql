python
# database/models.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    session_token = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)

# database/repository.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, UserSession

engine = create_engine("postgresql://user:password@host:port/dbname")
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

class UserRepository:
    def __init__(self, session):
        self.session = session

    def invalidate_session(self, session_token):
        self.session.query(UserSession).filter_by(session_token=session_token).update({"expires_at": func.now()})
        self.session.commit()

# main.py
from fastapi import FastAPI, Response, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.repository import UserRepository, Session
from pydantic import BaseModel

app = FastAPI()

class LogoutRequest(BaseModel):
    session_token: str

security = HTTPBearer()

@app.post("/logout")
async def logout(request: LogoutRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    session = Session()
    user_repository = UserRepository(session)
    user_repository.invalidate_session(credentials.credentials)
    return {"message": "Logged out successfully"}

# React TypeScript code for logout
// components/Logout.tsx
import React from "react";
import axios from "axios";

const Logout = () => {
    const handleLogout = async () => {
        try {
            const response = await axios.post("/logout", {
                session_token: localStorage.getItem("session_token")
            }, {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem("session_token")}`
                }
            });
            if (response.status === 200) {
                localStorage.removeItem("session_token");
                window.location.href = "/login";
            }
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <button onClick={handleLogout}>Logout</button>
    );
};

export default Logout;