# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class EmployeeData(BaseModel):
    id: int
    name: str
    department: str
    sales: int

class DashboardData(BaseModel):
    total_employees: int
    total_sales: int
    top_performers: List[EmployeeData]

# Sample in-memory data store
employees = [
    EmployeeData(id=1, name="John Doe", department="Sales", sales=1000),
    EmployeeData(id=2, name="Jane Doe", department="Marketing", sales=500),
    EmployeeData(id=3, name="Bob Smith", department="Sales", sales=2000),
]

# API endpoint to fetch dashboard data
@app.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data():
    total_employees = len(employees)
    total_sales = sum(employee.sales for employee in employees)
    top_performers = sorted(employees, key=lambda x: x.sales, reverse=True)[:3]
    return {
        "total_employees": total_employees,
        "total_sales": total_sales,
        "top_performers": top_performers,
    }