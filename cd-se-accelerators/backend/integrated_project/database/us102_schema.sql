python
# database.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi import Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI()

# Initialize database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///employee_database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define Employee model
class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    department = Column(String, index=True)
    role = Column(String, index=True)

# Create database tables
Base.metadata.create_all(bind=engine)

# Define Employee schema
class EmployeeSchema(BaseModel):
    id: int
    name: str
    department: str
    role: str

# Define dashboard data schema
class DashboardDataSchema(BaseModel):
    employees: list[EmployeeSchema]

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create employee
@app.post("/employees/")
def create_employee(employee: EmployeeSchema, db: Session = Depends(get_db)):
    db_employee = Employee(name=employee.name, department=employee.department, role=employee.role)
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return JSONResponse(content={"message": "Employee created successfully"}, status_code=201)

# Get all employees
@app.get("/employees/")
def read_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    return JSONResponse(content=[{"id": employee.id, "name": employee.name, "department": employee.department, "role": employee.role} for employee in employees], status_code=200)

# Get dashboard data
@app.get("/dashboard/")
def read_dashboard_data(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    dashboard_data = DashboardDataSchema(employees=[{"id": employee.id, "name": employee.name, "department": employee.department, "role": employee.role} for employee in employees])
    return JSONResponse(content=dashboard_data.dict(), status_code=200)