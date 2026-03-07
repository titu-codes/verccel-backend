from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app import crud, schemas
from app.database import Base, engine, get_db

# Create tables (OK for now)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HRMS Lite API",
    description="Lightweight Human Resource Management System",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- HEALTH ----------
@app.get("/")
def root():
    return {"message": "HRMS Lite API running 🚀"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ---------- EMPLOYEE ----------
@app.post("/employees/", response_model=schemas.EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_employee(db=db, employee=employee)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/employees/", response_model=List[schemas.EmployeeResponse])
def read_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_employees(db, skip=skip, limit=limit)

@app.get("/employees/{employee_id}", response_model=schemas.EmployeeWithAttendance)
def read_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = crud.get_employee(db, employee_id=employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: str, db: Session = Depends(get_db)):
    try:
        crud.delete_employee(db, employee_id)
        return {"message": "Employee deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ---------- ATTENDANCE ----------
@app.post("/attendance/", response_model=schemas.AttendanceResponse, status_code=status.HTTP_201_CREATED)
def mark_attendance(attendance: schemas.AttendanceCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_attendance(db=db, attendance=attendance)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/attendance/employee/{employee_id}", response_model=List[schemas.AttendanceResponse])
def get_employee_attendance(employee_id: str, db: Session = Depends(get_db)):
    return crud.get_attendance_by_employee(db, employee_id)

@app.get("/attendance/date/{attendance_date}", response_model=List[schemas.AttendanceResponse])
def get_date_attendance(attendance_date: date, db: Session = Depends(get_db)):
    return crud.get_attendance_by_date(db, attendance_date)
