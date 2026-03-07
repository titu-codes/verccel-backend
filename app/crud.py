from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Employee, Attendance
from app.schemas import EmployeeCreate, AttendanceCreate
from datetime import date
import logging

logger = logging.getLogger(__name__)

# Employee CRUD operations
def get_employee(db: Session, employee_id: str):
    return db.query(Employee).filter(Employee.employee_id == employee_id).first()

def get_employees(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Employee).offset(skip).limit(limit).all()

def create_employee(db: Session, employee: EmployeeCreate):
    # Check if employee_id already exists
    db_employee = get_employee(db, employee.employee_id)
    if db_employee:
        raise ValueError(f"Employee ID {employee.employee_id} already exists")
    
    # Check if email already exists
    db_employee_email = db.query(Employee).filter(Employee.email == employee.email).first()
    if db_employee_email:
        raise ValueError(f"Email {employee.email} already exists")
    
    db_employee = Employee(**employee.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def delete_employee(db: Session, employee_id: str):
    employee = get_employee(db, employee_id)
    if not employee:
        raise ValueError(f"Employee with ID {employee_id} not found")
    
    # Delete attendance records first
    db.query(Attendance).filter(Attendance.employee_id == employee_id).delete()
    db.delete(employee)
    db.commit()
    return True

# Attendance CRUD operations
def get_attendance_by_employee(db: Session, employee_id: str):
    return db.query(Attendance).filter(Attendance.employee_id == employee_id).all()

def get_attendance_by_date(db: Session, attendance_date: date):
    return db.query(Attendance).filter(Attendance.date == attendance_date).all()

def create_attendance(db: Session, attendance: AttendanceCreate):
    # Check if employee exists
    employee = get_employee(db, attendance.employee_id)
    if not employee:
        raise ValueError(f"Employee with ID {attendance.employee_id} not found")
    
    # Check if attendance already marked for this date
    existing = db.query(Attendance).filter(
        Attendance.employee_id == attendance.employee_id,
        Attendance.date == attendance.date
    ).first()
    
    if existing:
        raise ValueError(f"Attendance already marked for {attendance.date}")
    
    db_attendance = Attendance(**attendance.dict())
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance