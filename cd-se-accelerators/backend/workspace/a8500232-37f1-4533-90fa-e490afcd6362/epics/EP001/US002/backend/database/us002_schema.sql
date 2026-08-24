python
# database.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://user:password@localhost/dbname')
Base = declarative_base()
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)

    def __repr__(self):
        return f"User(id={self.id}, username='{self.username}', password='{self.password}')"

Base.metadata.create_all(engine)

class UserRepository:
    def __init__(self, session):
        self.session = session

    def get_user_by_username(self, username):
        return self.session.query(User).filter_by(username=username).first()

    def create_user(self, username, password):
        user = User(username=username, password=password)
        self.session.add(user)
        self.session.commit()
        return user

    def update_user(self, user, password):
        user.password = password
        self.session.commit()

    def delete_user(self, user):
        self.session.delete(user)
        self.session.commit()