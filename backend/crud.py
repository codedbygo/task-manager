from sqlalchemy.orm import Session
import models, schemas, auth

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_all_users(db: Session):
    return db.query(models.User).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, name=user.name, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_projects(db: Session, user_id: int):
    return db.query(models.Project).join(models.ProjectMember).filter(models.ProjectMember.user_id == user_id).all()

def create_project(db: Session, project: schemas.ProjectCreate, user_id: int):
    db_project = models.Project(**project.model_dump(), creator_id=user_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # The project creator is always stored as admin.
    db_member = models.ProjectMember(project_id=db_project.id, user_id=user_id, role=models.RoleEnum.ADMIN)
    db.add(db_member)
    db.commit()
    
    return db_project

def get_project(db: Session, project_id: int, user_id: int):
    # Return project only when the user is a member.
    member = db.query(models.ProjectMember).filter_by(project_id=project_id, user_id=user_id).first()
    if not member:
        return None
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def add_project_member(db: Session, project_id: int, member: schemas.ProjectMemberBase):
    db_member = models.ProjectMember(project_id=project_id, user_id=member.user_id, role=member.role)
    db.add(db_member)
    db.commit()
    return db_member

def get_project_member(db: Session, project_id: int, user_id: int):
    return db.query(models.ProjectMember).filter_by(project_id=project_id, user_id=user_id).first()

def remove_project_member(db: Session, project_id: int, user_id: int):
    member = db.query(models.ProjectMember).filter_by(project_id=project_id, user_id=user_id).first()
    if member:
        db.delete(member)
        db.commit()
    return member

def create_task(db: Session, task: schemas.TaskCreate, project_id: int):
    task_data = task.model_dump(exclude={"assignees"})
    db_task = models.Task(**task_data, project_id=project_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    for user_id in task.assignees:
        db_assignee = models.TaskAssignee(task_id=db_task.id, user_id=user_id)
        db.add(db_assignee)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_tasks(db: Session, project_id: int):
    return db.query(models.Task).filter(models.Task.project_id == project_id).all()

def get_tasks_assigned_to_user(db: Session, project_id: int, user_id: int):
    return (
        db.query(models.Task)
        .join(models.TaskAssignee, models.Task.id == models.TaskAssignee.task_id)
        .filter(models.Task.project_id == project_id, models.TaskAssignee.user_id == user_id)
        .all()
    )

def update_task(db: Session, task_id: int, task: schemas.TaskUpdate):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        return None
        
    update_data = task.model_dump(exclude_unset=True)
    assignees = update_data.pop("assignees", None)
    
    for key, value in update_data.items():
        setattr(db_task, key, value)
        
    if assignees is not None:
        db.query(models.TaskAssignee).filter(models.TaskAssignee.task_id == task_id).delete()
        for user_id in assignees:
            db.add(models.TaskAssignee(task_id=task_id, user_id=user_id))
            
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        db.query(models.TaskAssignee).filter(models.TaskAssignee.task_id == task_id).delete()
        db.delete(db_task)
        db.commit()
    return db_task
