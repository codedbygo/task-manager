Team Task Manager

Team Task Manager is a full-stack web application for collaborative project and task tracking.
Users can create projects, manage members, assign tasks, and monitor progress with role-based permissions.

Overview
- User authentication with signup and login (JWT)
- Project management with Admin and Member roles
- Team member management (Admin can add/remove members)
- Task management with title, description, due date, priority, assignee, and status
- Dashboard metrics:
  - total tasks
  - tasks by status
  - tasks per user
  - overdue tasks

Access Rules
Admin
- Create projects
- Add and remove project members
- Create and manage all project tasks
- View all project tasks

Member
- View only tasks assigned to them
- Update status of tasks assigned to them

Tech Stack
Frontend
- React + TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Axios

Backend
- FastAPI
- SQLAlchemy
- Pydantic
- JWT authentication

Database
- SQLite for local development
- PostgreSQL for Railway deployment

Project Structure

team-task-manager/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── auth.py
│   ├── database.py
│   ├── requirements.txt
│   └── Procfile
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
└── README.md

Local Setup

Backend Setup

1. Go to backend folder

```bash
cd backend
```

2. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Run backend server

```bash
uvicorn main:app --reload
```

Backend URL: `http://localhost:8000`  
Swagger docs: `http://localhost:8000/docs`

Frontend Setup


1. Go to frontend folder

```bash
cd frontend
```

2. Install dependencies

```bash
npm install
```

3. Start frontend

```bash
npm run dev
```

Frontend URL: `http://localhost:5173`

Environment Variables
Backend
- `DATABASE_URL`
  - Local example: `sqlite:///./sql_app.db`
  - Railway PostgreSQL example: `postgresql://...`
- `SECRET_KEY`
  - Use a strong random secret for JWT signing
- `PORT`
  - Railway sets this automatically

Frontend
- `VITE_API_URL`
  - Local example: `http://localhost:8000/api`
  - Production example: `https://<your-backend-domain>/api`

API Summary
Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/users/me`

Projects
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `POST /api/projects/{project_id}/members`
- `DELETE /api/projects/{project_id}/members/{user_id}`

Tasks
- `GET /api/projects/{project_id}/tasks`
- `POST /api/projects/{project_id}/tasks`
- `PUT /api/tasks/{task_id}`
- `DELETE /api/tasks/{task_id}`

Dashboard
- `GET /api/dashboard`

Verification
Run these checks locally.

Backend checks
```bash
cd backend
python3 -m py_compile main.py crud.py auth.py models.py schemas.py
pytest -q
```

Frontend checks
```bash
cd frontend
npm run lint
npm run build
```



# task-manager
