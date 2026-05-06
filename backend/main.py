from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

import models, schemas, crud, auth, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Team Task Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/api/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.get("/api/users", response_model=List[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_all_users(db)

@app.get("/api/projects", response_model=List[schemas.ProjectResponse])
def get_projects(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_projects(db, user_id=current_user.id)

@app.post("/api/projects", response_model=schemas.ProjectResponse)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.create_project(db, project=project, user_id=current_user.id)

@app.get("/api/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    project = crud.get_project(db, project_id=project_id, user_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or not a member")
    return project

@app.post("/api/projects/{project_id}/members", response_model=schemas.ProjectMemberResponse)
def add_member(project_id: int, member: schemas.ProjectMemberBase, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Only admins can manage project members.
    user_membership = crud.get_project_member(db, project_id=project_id, user_id=current_user.id)
    if not user_membership or user_membership.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can add members")

    target_user = db.query(models.User).filter(models.User.id == member.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_member = crud.get_project_member(db, project_id=project_id, user_id=member.user_id)
    if existing_member:
        raise HTTPException(status_code=400, detail="User already a member")
        
    return crud.add_project_member(db, project_id=project_id, member=member)

@app.delete("/api/projects/{project_id}/members/{user_id}")
def remove_member(project_id: int, user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    user_membership = crud.get_project_member(db, project_id=project_id, user_id=current_user.id)
    if not user_membership or user_membership.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can remove members")
        
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
        
    removed = crud.remove_project_member(db, project_id=project_id, user_id=user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"message": "Member removed successfully"}

@app.get("/api/projects/{project_id}/tasks", response_model=List[schemas.TaskResponse])
def get_tasks(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Return tasks only for users who belong to this project.
    project = crud.get_project(db, project_id=project_id, user_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied")
    membership = crud.get_project_member(db, project_id=project_id, user_id=current_user.id)
    if membership.role == models.RoleEnum.ADMIN:
        return crud.get_tasks(db, project_id=project_id)
    return crud.get_tasks_assigned_to_user(db, project_id=project_id, user_id=current_user.id)

@app.post("/api/projects/{project_id}/tasks", response_model=schemas.TaskResponse)
def create_task(project_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    project = crud.get_project(db, project_id=project_id, user_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied")

    membership = crud.get_project_member(db, project_id=project_id, user_id=current_user.id)
    if not membership or membership.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create tasks")

    if task.assignees:
        project_member_ids = {
            member.user_id for member in db.query(models.ProjectMember).filter(models.ProjectMember.project_id == project_id).all()
        }
        invalid_assignees = [user_id for user_id in task.assignees if user_id not in project_member_ids]
        if invalid_assignees:
            raise HTTPException(status_code=400, detail="All assignees must be project members")

    return crud.create_task(db, task=task, project_id=project_id)

@app.put("/api/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Update is allowed only for users in the task project.
    project = crud.get_project(db, project_id=db_task.project_id, user_id=current_user.id)
    if not project:
        raise HTTPException(status_code=403, detail="Not authorized to update this task")

    user_membership = crud.get_project_member(db, project_id=db_task.project_id, user_id=current_user.id)

    is_assigned = any(assignee.id == current_user.id for assignee in db_task.assignees)

    if user_membership.role != models.RoleEnum.ADMIN and not is_assigned:
        raise HTTPException(status_code=403, detail="Members can only update assigned tasks")

    if task.assignees is not None:
        project_member_ids = {
            member.user_id
            for member in db.query(models.ProjectMember).filter(models.ProjectMember.project_id == db_task.project_id).all()
        }
        invalid_assignees = [user_id for user_id in task.assignees if user_id not in project_member_ids]
        if invalid_assignees:
            raise HTTPException(status_code=400, detail="All assignees must be project members")

    if user_membership.role != models.RoleEnum.ADMIN:
        # Members can only change status on their own tasks.
        if task.title or task.description or task.due_date or task.priority or task.assignees is not None:
            raise HTTPException(status_code=403, detail="Members can only update task status")

    return crud.update_task(db, task_id=task_id, task=task)

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    user_membership = crud.get_project_member(db, project_id=db_task.project_id, user_id=current_user.id)
    if not user_membership or user_membership.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete tasks")
        
    crud.delete_task(db, task_id=task_id)
    return {"message": "Task deleted successfully"}

@app.get("/api/dashboard", response_model=schemas.DashboardStats)
def get_dashboard(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Build dashboard from all projects the user belongs to.
    projects = crud.get_projects(db, user_id=current_user.id)
    project_ids = [p.id for p in projects]
    
    if not project_ids:
        return schemas.DashboardStats(
            total_tasks=0,
            tasks_by_status={"TODO": 0, "IN_PROGRESS": 0, "DONE": 0},
            tasks_by_user={},
            overdue_tasks=0
        )
        
    tasks = db.query(models.Task).filter(models.Task.project_id.in_(project_ids)).all()
    
    total_tasks = len(tasks)
    tasks_by_status = {"TODO": 0, "IN_PROGRESS": 0, "DONE": 0}
    tasks_by_user = {}
    overdue_tasks = 0
    
    from datetime import datetime
    now = datetime.utcnow()
    
    for task in tasks:
        tasks_by_status[task.status] = tasks_by_status.get(task.status, 0) + 1
        
        if task.due_date and task.due_date < now and task.status != models.StatusEnum.DONE:
            overdue_tasks += 1
            
        for assignee in task.assignees:
            tasks_by_user[assignee.name] = tasks_by_user.get(assignee.name, 0) + 1
            
    return schemas.DashboardStats(
        total_tasks=total_tasks,
        tasks_by_status=tasks_by_status,
        tasks_by_user=tasks_by_user,
        overdue_tasks=overdue_tasks
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
