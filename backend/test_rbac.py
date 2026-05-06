from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from main import app, get_db


SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_app.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def register_user(name: str, email: str, password: str = "password123"):
    response = client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def login(email: str, password: str = "password123"):
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def create_project(token: str, name: str = "Alpha"):
    response = client.post(
        "/api/projects",
        json={"name": name, "description": "Test project"},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    return response.json()


def add_member(token: str, project_id: int, user_id: int):
    response = client.post(
        f"/api/projects/{project_id}/members",
        json={"user_id": user_id, "role": "MEMBER"},
        headers=auth_headers(token),
    )
    assert response.status_code == 200


def create_task(token: str, project_id: int, title: str, assignee_ids: list[int]):
    response = client.post(
        f"/api/projects/{project_id}/tasks",
        json={
            "title": title,
            "description": "Test task",
            "priority": "MEDIUM",
            "status": "TODO",
            "assignees": assignee_ids,
        },
        headers=auth_headers(token),
    )
    return response


def test_member_cannot_create_task():
    admin = register_user("Admin", "admin@test.com")
    member = register_user("Member", "member@test.com")

    admin_token = login(admin["email"])
    member_token = login(member["email"])

    project = create_project(admin_token)
    add_member(admin_token, project["id"], member["id"])

    response = create_task(member_token, project["id"], "Member Task", [member["id"]])
    assert response.status_code == 403


def test_member_sees_only_assigned_tasks():
    admin = register_user("Admin", "admin2@test.com")
    member = register_user("Member", "member2@test.com")
    second_member = register_user("Second", "second@test.com")

    admin_token = login(admin["email"])
    member_token = login(member["email"])

    project = create_project(admin_token, "Beta")
    add_member(admin_token, project["id"], member["id"])
    add_member(admin_token, project["id"], second_member["id"])

    task_for_member = create_task(admin_token, project["id"], "Assigned to member", [member["id"]])
    task_for_second = create_task(admin_token, project["id"], "Assigned to second", [second_member["id"]])
    assert task_for_member.status_code == 200
    assert task_for_second.status_code == 200

    response = client.get(
        f"/api/projects/{project['id']}/tasks",
        headers=auth_headers(member_token),
    )
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Assigned to member"


def test_member_can_only_update_status_of_assigned_task():
    admin = register_user("Admin", "admin3@test.com")
    member = register_user("Member", "member3@test.com")

    admin_token = login(admin["email"])
    member_token = login(member["email"])

    project = create_project(admin_token, "Gamma")
    add_member(admin_token, project["id"], member["id"])

    task_response = create_task(admin_token, project["id"], "Task to update", [member["id"]])
    assert task_response.status_code == 200
    task_id = task_response.json()["id"]

    status_update = client.put(
        f"/api/tasks/{task_id}",
        json={"status": "IN_PROGRESS"},
        headers=auth_headers(member_token),
    )
    assert status_update.status_code == 200

    title_update = client.put(
        f"/api/tasks/{task_id}",
        json={"title": "Not allowed"},
        headers=auth_headers(member_token),
    )
    assert title_update.status_code == 403


def test_invalid_assignee_is_rejected_on_create():
    admin = register_user("Admin", "admin4@test.com")
    member = register_user("Member", "member4@test.com")
    outsider = register_user("Outsider", "outsider@test.com")

    admin_token = login(admin["email"])
    project = create_project(admin_token, "Delta")
    add_member(admin_token, project["id"], member["id"])

    response = create_task(admin_token, project["id"], "Invalid assignee", [outsider["id"]])
    assert response.status_code == 400


def test_member_cannot_delete_task():
    admin = register_user("Admin", "admin5@test.com")
    member = register_user("Member", "member5@test.com")

    admin_token = login(admin["email"])
    member_token = login(member["email"])

    project = create_project(admin_token, "Epsilon")
    add_member(admin_token, project["id"], member["id"])

    task_response = create_task(admin_token, project["id"], "Task to delete", [member["id"]])
    assert task_response.status_code == 200
    task_id = task_response.json()["id"]

    delete_response = client.delete(f"/api/tasks/{task_id}", headers=auth_headers(member_token))
    assert delete_response.status_code == 403


def test_admin_can_delete_task():
    admin = register_user("Admin", "admin6@test.com")
    member = register_user("Member", "member6@test.com")

    admin_token = login(admin["email"])
    project = create_project(admin_token, "Zeta")
    add_member(admin_token, project["id"], member["id"])

    task_response = create_task(admin_token, project["id"], "Admin delete task", [member["id"]])
    assert task_response.status_code == 200
    task_id = task_response.json()["id"]

    delete_response = client.delete(f"/api/tasks/{task_id}", headers=auth_headers(admin_token))
    assert delete_response.status_code == 200


def test_add_nonexistent_member_returns_not_found():
    admin = register_user("Admin", "admin7@test.com")
    admin_token = login(admin["email"])
    project = create_project(admin_token, "Eta")

    response = client.post(
        f"/api/projects/{project['id']}/members",
        json={"user_id": 999999, "role": "MEMBER"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404
