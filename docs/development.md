# Enermax CRM — Local Development Guide

## 1. Prerequisites

Before running the application locally, ensure you have:
* **Python**: 3.12+ (tested with Python 3.13)
* **Node.js**: 20+ (tested with Node.js 24)
* **Git**: 2.40+
* **Docker & Docker Compose** (Optional for containerized run)

---

## 2. Quickstart (Under 2 Minutes)

### Option A: Running via Docker Compose
To launch the entire stack (PostgreSQL, Redis, Backend, Frontend) with a single command:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Start all services
docker compose up --build
```
* **Frontend**: Visit [http://localhost:5173](http://localhost:5173)
* **Backend API**: Visit [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Option B: Running Natively for Local Development

#### 1. Setup Backend
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (or in-memory SQLite auto-initialization will run)
python -m alembic upgrade head

# Start FastAPI dev server with auto-reload
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### 2. Setup Frontend
```bash
# Navigate to frontend directory
cd frontend

# Install packages
npm install

# Start Vite dev server
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173) to access the UI.

---

## 3. Running Automated Tests

Run the complete test suite across backend and frontend:

```powershell
# Windows
.\scripts\run_tests.ps1
```

Or execute independently:

```bash
# Backend pytest suite
backend\.venv\Scripts\pytest.exe backend/tests -v

# Frontend production build & type check
cd frontend && npm run build
```

---

## 4. Linting and Code Quality

Format and check backend code using Ruff:
```bash
ruff check backend
ruff format backend
```
