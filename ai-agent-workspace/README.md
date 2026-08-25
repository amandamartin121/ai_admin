# AI Agent Workspace

A complete, production-ready desktop AI chatbot/agent management platform.

## Overview

AI Agent Workspace is a secure multi-user AI chatbot/agent platform built with Tauri 2, React, TypeScript, FastAPI, and PostgreSQL. It features:

- **User Authentication**: JWT-based authentication with refresh tokens
- **Role-Based Access Control (RBAC)**: Granular permissions system
- **Chat Mode**: ChatGPT-style conversational interface
- **Agent Mode**: Agentic AI execution with tool approval workflows
- **Admin Panel**: Complete user, role, and system management
- **File Management**: Secure file upload and attachment
- **Audit Logging**: Comprehensive security event logging
- **RAG-Ready Architecture**: Designed for retrieval-augmented generation

## Architecture

```
ai-agent-workspace/
├── frontend/          # React + TypeScript + Vite
├── backend/           # FastAPI + Python + SQLAlchemy
├── src-tauri/         # Tauri 2 desktop integration
├── docker/            # Docker Compose for development
└── tests/             # Backend and frontend tests
```

## Requirements

- Node.js 18+
- Python 3.11+
- Rust (for Tauri)
- PostgreSQL 15+ (or SQLite for development)
- Docker & Docker Compose (optional)

## Installation

### 1. Clone the Repository

```bash
cd ai-agent-workspace
```

### 2. Environment Setup

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and configure your settings:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_agent_workspace
# Or for SQLite: DATABASE_URL=sqlite:///./dev.db

# JWT Settings
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ACCESS_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_DAYS=7

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_MODEL=gpt-4o-mini

# CORS
CORS_ORIGINS=http://localhost:5173,tauri://localhost

# File Storage
FILE_STORAGE_PATH=./uploads
MAX_UPLOAD_SIZE=10485760

# Environment
ENVIRONMENT=development

# Super Admin Credentials (for seed)
SUPER_ADMIN_EMAIL=admin@example.com
SUPER_ADMIN_PASSWORD=ChangeMe123!
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed initial data
python -m app.core.seed

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`
OpenAPI docs at `http://localhost:8000/docs`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 5. Tauri Development

```bash
# From the project root or frontend directory
npm run tauri dev
```

This will build and run the desktop application.

## Production Build

### Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m app.core.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend + Tauri

```bash
cd frontend
npm run build
npm run tauri build
```

The production binary will be in `frontend/src-tauri/target/release/`

## Docker Development

```bash
cd docker
docker-compose up -d
```

This starts PostgreSQL and the backend service.

## Authentication Flow

1. **Register**: POST `/api/v1/auth/register`
2. **Login**: POST `/api/v1/auth/login`
3. **Refresh Token**: POST `/api/v1/auth/refresh`
4. **Logout**: POST `/api/v1/auth/logout`

Tokens are stored securely and automatically refreshed.

## Permissions System

### Default Roles

- **SUPER_ADMIN**: Full system access
- **ADMIN**: User and system management
- **USER**: Basic chat access
- **AI_OPERATOR**: Advanced agent access

### Key Permissions

| Permission | Description |
|------------|-------------|
| `chat.access` | Access to chat functionality |
| `agent.access` | Access to agentic mode |
| `agent.execute` | Execute agent tools |
| `agent.approve` | Approve sensitive actions |
| `users.view` | View users |
| `users.manage` | Create/edit/delete users |
| `models.manage` | Manage AI models |
| `audit.view` | View audit logs |
| `files.upload` | Upload files |

## Agent System

### Agent Modes

1. **Chat Mode**: Standard conversational AI
2. **Agent Mode**: Task execution with tools

### Agent Lifecycle

```
USER_REQUEST → PLANNING → TOOL_SELECTION → PERMISSION_CHECK → 
USER_APPROVAL → TOOL_EXECUTION → OBSERVATION → FINAL_RESPONSE
```

### Tool Risk Levels

- **LOW**: Calculator, datetime (auto-approved)
- **MEDIUM**: Web search, file read (permission required)
- **HIGH**: File write, external APIs (user approval required)
- **CRITICAL**: Shell execution (disabled by default)

## API Endpoints

### Authentication
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/change-password`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/sessions`
- `DELETE /api/v1/auth/sessions/{session_id}`

### Users (Admin)
- `GET /api/v1/admin/users`
- `POST /api/v1/admin/users`
- `GET /api/v1/admin/users/{user_id}`
- `PUT /api/v1/admin/users/{user_id}`
- `DELETE /api/v1/admin/users/{user_id}`
- `POST /api/v1/admin/users/{user_id}/reset-password`

### Chat
- `GET /api/v1/conversations`
- `POST /api/v1/conversations`
- `GET /api/v1/conversations/{conversation_id}`
- `PUT /api/v1/conversations/{conversation_id}`
- `DELETE /api/v1/conversations/{conversation_id}`
- `POST /api/v1/chat/completions` (streaming SSE)

### Agents
- `POST /api/v1/agents/run`
- `POST /api/v1/agents/approvals/{approval_id}/approve`
- `POST /api/v1/agents/approvals/{approval_id}/reject`

### Files
- `POST /api/v1/files/upload`
- `GET /api/v1/files`
- `GET /api/v1/files/{file_id}`
- `DELETE /api/v1/files/{file_id}`
- `GET /api/v1/files/{file_id}/download`

### Admin
- `GET /api/v1/admin/dashboard`
- `GET /api/v1/admin/audit-logs`
- `GET /api/v1/admin/settings`
- `PUT /api/v1/admin/settings`

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm run test
```

### E2E Tests

```bash
cd tests/e2e
npm run test:e2e
```

## Security Features

- Argon2 password hashing
- JWT with refresh token rotation
- Role-based and permission-based access control
- Input validation (Pydantic/Zod)
- SQL injection protection (SQLAlchemy ORM)
- XSS protection
- CORS configuration
- Secure HTTP headers
- Audit logging
- File type validation
- Ownership verification

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -U postgres -d ai_agent_workspace
```

### Migration Issues

```bash
cd backend
alembic downgrade base
alembic upgrade head
```

### Port Conflicts

- Backend: Change PORT in `.env`
- Frontend: Change port in `vite.config.ts`
- PostgreSQL: Change port in `docker-compose.yml`

## License

MIT License

## Support

For issues and feature requests, please open an issue on the repository.
