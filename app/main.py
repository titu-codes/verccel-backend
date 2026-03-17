from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import date

# Relative imports for Vercel path mapping
from . import crud, schemas
from .database import Base, engine, get_db

app = FastAPI(
    title="HRMS Lite API",
    description="Lightweight Human Resource Management System",
    version="1.0.0"
)

# CORS - Essential for your frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DATABASE INITIALIZATION ----------
# This creates the tables in Aiven if they don't exist
# In a professional setup, you'd use Alembic, but this works for Lite versions
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

# ---------- HEALTH / ROOT ----------
@app.get("/")
def root():
    return {"message": "HRMS Lite API is live on Railway! 🚀", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ---------- EMPLOYEE ENDPOINTS ----------
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

# ---------- ATTENDANCE ENDPOINTS ----------
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


@app.post("/attendance/populate-last-7-days")
def populate_last_7_days(reference_date: str = None, db: Session = Depends(get_db)):
    """Mark all employees as Present for the last 7 days (skips already marked).
    reference_date: YYYY-MM-DD - use user's local date (optional)."""
    from datetime import timedelta, datetime
    if reference_date:
        try:
            today = datetime.strptime(reference_date, "%Y-%m-%d").date()
        except ValueError:
            today = date.today()
    else:
        today = date.today()
    employees = crud.get_employees(db)
    if not employees:
        return {"message": "No employees to mark", "marked": 0}
    marked = 0
    for d in range(7):
        d_date = today - timedelta(days=d)
        for emp in employees:
            try:
                crud.create_attendance(db, schemas.AttendanceCreate(
                    employee_id=emp.employee_id,
                    date=d_date,
                    status="Present",
                ))
                marked += 1
            except ValueError:
                pass  # Already marked
    return {"message": f"Marked {marked} attendance record(s)", "marked": marked}


# ---------- ANALYTICS ENDPOINTS ----------
@app.get("/analytics/dashboard", response_model=schemas.AnalyticsDashboard)
def get_analytics_dashboard(days: int = 7, reference_date: str = None, db: Session = Depends(get_db)):
    """reference_date: YYYY-MM-DD - use user's local date (avoids timezone mismatch)."""
    from datetime import datetime
    today = None
    if reference_date:
        try:
            today = datetime.strptime(reference_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    return crud.get_analytics_dashboard(db, days=days, today=today)