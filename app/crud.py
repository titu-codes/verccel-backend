from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from app.models import Employee, Attendance
from app.schemas import EmployeeCreate, AttendanceCreate
from datetime import date, timedelta
from collections import defaultdict
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


# Analytics
def get_attendance_in_date_range(db: Session, start_date: date, end_date: date):
    return db.query(Attendance).filter(
        and_(Attendance.date >= start_date, Attendance.date <= end_date)
    ).all()


def _is_present(status) -> bool:
    """Handle status from DB (enum/string - Present, PRESENT, present)."""
    s = (str(status) or "").strip().lower()
    return s in ("present",)

def _is_absent(status) -> bool:
    """Handle status from DB (enum/string - Absent, ABSENT, absent)."""
    s = (str(status) or "").strip().lower()
    return s in ("absent",)

def get_analytics_dashboard(db: Session, days: int = 7, today: date = None):
    if today is None:
        today = date.today()
    start_date = today - timedelta(days=days - 1)

    # Total employees
    total_employees = db.query(Employee).count()

    # Today's attendance
    today_attendance = get_attendance_by_date(db, today)
    today_present = sum(1 for a in today_attendance if _is_present(a.status))
    today_absent = sum(1 for a in today_attendance if _is_absent(a.status))

    # Last N days attendance
    range_attendance = get_attendance_in_date_range(db, start_date, today)
    last7_present = sum(1 for a in range_attendance if _is_present(a.status))
    last7_absent = sum(1 for a in range_attendance if _is_absent(a.status))

    # Attendance by date for chart - ONLY include dates that have marked attendance
    by_date = defaultdict(lambda: {"present": 0, "absent": 0})
    for a in range_attendance:
        key = a.date.isoformat()
        if start_date <= a.date <= today:
            if _is_present(a.status):
                by_date[key]["present"] += 1
            elif _is_absent(a.status):
                by_date[key]["absent"] += 1

    attendance_by_date = [
        {"date": k, "present_count": v["present"], "absent_count": v["absent"]}
        for k, v in sorted(by_date.items())
    ]

    # Most absent in last N days
    absent_by_employee = defaultdict(int)
    employee_info = {}
    for a in range_attendance:
        if _is_absent(a.status):
            absent_by_employee[a.employee_id] += 1
        emp = db.query(Employee).filter(Employee.employee_id == a.employee_id).first()
        if emp and a.employee_id not in employee_info:
            employee_info[a.employee_id] = {"full_name": emp.full_name, "department": emp.department}

    # Include all employees who had any attendance in range
    for a in range_attendance:
        if a.employee_id not in employee_info:
            emp = db.query(Employee).filter(Employee.employee_id == a.employee_id).first()
            if emp:
                employee_info[a.employee_id] = {"full_name": emp.full_name, "department": emp.department}

    most_absent = [
        {
            "employee_id": eid,
            "full_name": employee_info.get(eid, {}).get("full_name", "Unknown"),
            "department": employee_info.get(eid, {}).get("department", ""),
            "absent_count": count,
        }
        for eid, count in sorted(absent_by_employee.items(), key=lambda x: -x[1])
    ][:10]

    return {
        "total_employees": total_employees,
        "today_present": today_present,
        "today_absent": today_absent,
        "last7_days": {"present_count": last7_present, "absent_count": last7_absent},
        "most_absent_last7_days": most_absent,
        "attendance_by_date": attendance_by_date,
    }