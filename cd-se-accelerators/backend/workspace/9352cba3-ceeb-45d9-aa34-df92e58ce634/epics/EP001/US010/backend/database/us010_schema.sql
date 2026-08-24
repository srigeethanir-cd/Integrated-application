python
# database/models.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class UserSession(Base):
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    session_token = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)

# database/repository.py
from database.models import Base, UserSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://user:password@host:port/dbname')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

class UserRepository:
    def __init__(self):
        self.session = Session()

    def invalidate_session(self, session_token):
        self.session.query(UserSession).filter_by(session_token=session_token).update({'expires_at': func.now()})
        self.session.commit()

# main.py
from fastapi import FastAPI, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.repository import UserRepository

app = FastAPI()
security = HTTPBearer()

user_repository = UserRepository()

@app.post("/logout")
def logout(token: HTTPAuthorizationCredentials = Depends(security)):
    user_repository.invalidate_session(token.credentials)
    return {"message": "Logged out successfully"}

# React TypeScript code for logout
// components/Logout.tsx
import React from 'react';
import axios from 'axios';

const Logout = () => {
    const handleLogout = async () => {
        try {
            const response = await axios.post('/logout', {}, {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('token')}`
                }
            });
            localStorage.removeItem('token');
            window.location.href = '/login';
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <button onClick={handleLogout}>Logout</button>
    );
};

export default Logout;