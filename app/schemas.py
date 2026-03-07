from pydantic import BaseModel, EmailStr, validator
from datetime import date
from typing import Optional
import re

class EmployeeBase(BaseModel):
    employee_id: str
    full_name: str
    email: EmailStr
    department: str
    
    @validator('employee_id')
    def validate_employee_id(cls, v):
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('Employee ID must contain only letters, numbers, underscores, and hyphens')
        return v

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeResponse(EmployeeBase):
    id: int
    
    class Config:
        from_attributes = True

class AttendanceBase(BaseModel):
    employee_id: str
    date: date
    status: str

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceResponse(AttendanceBase):
    id: int
    
    class Config:
        from_attributes = True

class EmployeeWithAttendance(EmployeeResponse):
    attendance_records: list[AttendanceResponse] = []