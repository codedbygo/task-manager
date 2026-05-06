from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime
from models import RoleEnum, StatusEnum, PriorityEnum

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: PriorityEnum = PriorityEnum.MEDIUM
    status: StatusEnum = StatusEnum.TODO

class TaskCreate(TaskBase):
    assignees: List[int] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[PriorityEnum] = None
    status: Optional[StatusEnum] = None
    assignees: Optional[List[int]] = None

class TaskResponse(TaskBase):
    id: int
    project_id: int
    assignees: List[UserResponse] = []
    class Config:
        from_attributes = True

class ProjectMemberBase(BaseModel):
    user_id: int
    role: RoleEnum = RoleEnum.MEMBER

class ProjectMemberResponse(BaseModel):
    user: UserResponse
    role: RoleEnum
    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    creator_id: int
    members: List[ProjectMemberResponse] = []
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_tasks: int
    tasks_by_status: Dict[str, int]
    tasks_by_user: Dict[str, int]
    overdue_tasks: int
