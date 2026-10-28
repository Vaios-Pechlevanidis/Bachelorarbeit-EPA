# Installation Guide — Group P1-3

> **Hinweis:** Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt. Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume nach dem Annotationsprotokoll (Abschnitt 3.6.1)

---

## Table of Contents

0. [Zero to Running — Quick Start](#0-zero-to-running--quick-start)
1. [Prerequisites](#1-prerequisites)
2. [Clone Repository](#2-clone-repository)
3. [Set Up Backend](#3-set-up-backend)
4. [Set Up Frontend](#4-set-up-frontend)
5. [Configure Environment Variables](#5-configure-environment-variables)
6. [Start the Project](#6-start-the-project)
7. [Verify Installation](#7-verify-installation)
8. [Train & Manage LDA Models](#8-train--manage-lda-models)
9. [Common Problems & Solutions](#9-common-problems--solutions)

---

## 0. Zero to Running — Quick Start

Run all commands in order. At the end the project will be running fully locally.

> **Prerequisite:** Git and Node.js (20+) must already be installed.
> Python is managed via `uv`, so it does **not** need to be installed separately.

### Step 1 — Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.zshrc   # or ~/.bashrc

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2 — Clone Repository

```bash
git clone https://github.com/Vaios-Pechlevanidis/EPA-Bachelorarbeit.git
cd EPA-Bachelorarbeit
```

### Step 3 — Install Backend Dependencies

```bash
cd backend
uv sync
cd ..
```

### Step 4 — Set Environment Variables

```bash
# macOS / Linux
cp backend/.env.example backend/.env

# Windows (PowerShell)
Copy-Item backend/.env.example backend/.env
```

> Fill in `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` and `SUPABASE_KEY` (see [Step 5](#5-configure-environment-variables)). Without credentials the backend still starts, with an in-memory store and three synthetic companies (Demo 1–3).

### Step 5 — Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### Step 6 — Start Backend (keep terminal open)

```bash
cd backend
uv run uvicorn main:app --reload
```

Backend runs at: **<http://localhost:8000>**

### Step 7 — Start Frontend (new terminal)

```bash
cd frontend
npm run dev
```

Frontend runs at: **<http://localhost:5173>**

### Step 8 — Train First LDA Model (new terminal)

```bash
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "both", "num_topics": 5}'
```

> Without a trained model, topic analyses are not available. This step takes 30–120 seconds depending on the amount of data.

### Done

| Service  | URL                          |
| -------- | ---------------------------- |
| Frontend | <http://localhost:5173>      |
| Backend  | <http://localhost:8000>      |
| Swagger  | <http://localhost:8000/docs> |

---

## 1. Prerequisites

Make sure the following software is installed on your system:

| Software    | Minimum Version | Check Command        | Download                                                  |
| ----------- | --------------- | -------------------- | --------------------------------------------------------- |
| **Python**  | 3.13+           | `python --version`   | https://www.python.org/downloads/                         |
| **Node.js** | 20+             | `node --version`     | https://nodejs.org/                                       |
| **npm**     | (with Node.js)  | `npm --version`      | (comes with Node.js)                                      |
| **uv**      | (recommended)   | `uv --version`       | https://docs.astral.sh/uv/getting-started/installation/   |
| **Git**     | —               | `git --version`      | https://git-scm.com/                                      |

### Install uv (recommended)

`uv` is a fast Python package manager and is recommended for this project:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> **Note:** The project also works with classic `pip`, but `uv` is significantly faster.

---

## 2. Clone Repository

```bash
git clone https://github.com/Vaios-Pechlevanidis/EPA-Bachelorarbeit.git
cd EPA-Bachelorarbeit
```

---

## 3. Set Up Backend

### Option A: With `uv` (recommended)

```bash
cd backend
uv sync
```

This automatically creates a `.venv` and installs all dependencies from `pyproject.toml`.

### Option B: With `pip`

```bash
cd backend
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -r ../requirements.txt
pip install pytest   # only needed for the tests
```

### Set Python Interpreter in VS Code

1. Open the Command Palette: `Cmd+Shift+P` (Mac) / `Ctrl+Shift+P` (Windows/Linux)
2. Search: **Python: Select Interpreter**
3. Select the interpreter from `backend/.venv/bin/python`

### Installed Backend Packages

| Package            | Purpose                                        |
| ------------------ | ---------------------------------------------- |
| `fastapi`          | Web Framework (REST API)                       |
| `uvicorn`          | ASGI Server                                    |
| `supabase`         | Database Client (PostgreSQL)                   |
| `gensim`           | LDA Topic Modeling                             |
| `transformers`     | ML-based Sentiment Analysis (German BERT)      |
| `torch`            | PyTorch Backend for Transformers               |
| `pandas`           | Data Processing                                |
| `openpyxl`         | Excel Import/Export                            |
| `statsmodels`      | Statistical Analysis, Holt forecast            |
| `ruptures`         | Change point detection (level shifts)          |
| `yfinance`         | Share prices and company figures               |
| `python-dotenv`    | Environment variables from `.env`              |
| `python-multipart` | File Upload Support                            |

---

## 4. Set Up Frontend

```bash
cd frontend
npm install
```

This installs all dependencies from `package.json`.

### Installed Frontend Packages

| Package                  | Purpose                      |
| ------------------------ | ---------------------------- |
| `react` / `react-dom`   | UI Framework                 |
| `react-router-dom`      | Client-Side Routing          |
| `recharts`              | Chart Library                |
| `tailwindcss`           | CSS Framework                |
| `lucide-react`          | Icon Library                 |
| `@radix-ui/react-*`     | UI Components (shadcn/ui)    |
| `jspdf` / `html2canvas` | PDF Export                   |
| `vite`                  | Build Tool & Dev Server      |

---

## 5. Configure Environment Variables

Create a `.env` file in the `backend/` folder from the template:

```bash
cp backend/.env.example backend/.env
```

Fill in the following variables:

```env
# Supabase project URL
SUPABASE_URL=https://your-project.supabase.co

# service_role key, used by the backend for write operations (bypasses RLS)
SUPABASE_SERVICE_KEY=your-service-role-key

# anon/public key, fallback when no service_role key is set
SUPABASE_KEY=your-anon-key
```

> ⚠️ **Important:**
> - The `.env` file is in `.gitignore` and will **not** be committed to the repository.
> - The backend uses `SUPABASE_SERVICE_KEY` and falls back to `SUPABASE_KEY`.
> - Without `SUPABASE_URL` and a key, the backend starts with an in-memory store and three synthetic companies (Demo 1–3) instead of the database.
> - Further optional switches (`MARKET_LIVE_FETCH`, `CONTEXT_LIVE_FETCH`, `CONTEXT_GDELT` and the frontend's `VITE_*` variables) are listed in the README under [Environment Variables](README.md#-environment-variables).

### Database Schema

For a new Supabase project, run the SQL files in `backend/migrations/` in the Supabase SQL editor in order (`001` to `007`). Migration `006` adds the company metadata, `007` the table `user_events` for user-recorded events; until `007` is applied, the event routes answer 503.

### Frontend Backend URL

The frontend calls `http://localhost:8000` unless `VITE_API_URL` is set. `frontend/.env.production` sets `VITE_API_URL` to the hosted backend, so `npm run build` uses the hosted backend by default; for a local production build set `VITE_API_URL=http://localhost:8000`.

### Finding Supabase Credentials

1. Go to [supabase.com](https://supabase.com) and log in
2. Select your project
3. Go to **Settings → API**
4. Copy the **Project URL** → `SUPABASE_URL`
5. Copy the **service_role Key** (secret) → `SUPABASE_SERVICE_KEY`
6. Copy the **anon/public Key** → `SUPABASE_KEY`

---

## 6. Start the Project

You need **two terminal windows**, one for the backend and one for the frontend.

### Terminal 1 — Start Backend

```bash
cd backend

# With uv (recommended)
uv run uvicorn main:app --reload

# Or with activated venv
source .venv/bin/activate
python -m uvicorn main:app --reload
```

Backend runs at: **http://localhost:8000**  
API Documentation (Swagger): **http://localhost:8000/docs**

### Terminal 2 — Start Frontend

```bash
cd frontend
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

## 7. Verify Installation

### Check Backend

```bash
# API reachable?
curl http://localhost:8000/api/hello
# Expected response: {"message":"Hallo von FastAPI"}

# Database reachable? Lists the companies with their review counts
curl http://localhost:8000/api/companies
# Only "Demo 1" to "Demo 3": the backend runs without Supabase credentials

# Open Swagger UI
open http://localhost:8000/docs   # macOS
# xdg-open http://localhost:8000/docs   # Linux
```

### Check Frontend

Open **http://localhost:5173** in your browser. The welcome page should be displayed.

### Train First LDA Model

```bash
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "both", "num_topics": 5}'
```

### Run Tests

```bash
cd backend

# All backend tests
uv run pytest -q

# One area only, e.g. anomaly detection or topic modeling
uv run pytest tests/anomaly/
uv run pytest tests/topic_modeling/
```

```bash
cd frontend

# Frontend tests (Vitest)
npm test

# Lint (ESLint)
npm run lint
```

Three backend test files connect to the hosted Supabase database and need `backend/.env` and a network connection. The latest results are documented in [docs/testergebnisse.md](docs/testergebnisse.md).

---

## 8. Train & Manage LDA Models

The project uses **LDA (Latent Dirichlet Allocation)** for automatic topic extraction from feedback texts. Without a trained model, no topic analyses can be performed.

> **Prerequisite:** The backend must be running and the Supabase database must contain data.

### 8.1 Train Model via API (recommended)

The backend must be started (`http://localhost:8000`).

#### Train first model

```bash
# Combined model (candidates + employees), 5 topics
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "both", "num_topics": 5}'
```

#### Training Parameters

| Parameter               | Values                                  | Default  | Description                                    |
| ----------------------- | --------------------------------------- | -------- | ---------------------------------------------- |
| `source`                | `"candidates"`, `"employee"`, `"both"` | `"both"` | Data source for training                       |
| `num_topics`            | 2–20                                    | `5`      | Number of topics to extract                    |
| `limit`                 | number or `null`                        | `null`   | Max. number of records per source              |
| `use_employee_weighting`| `true` / `false`                        | `true`   | Apply employee type weighting                  |

#### Examples

```bash
# Employee feedback only, 10 topics
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "employee", "num_topics": 10}'

# Candidate feedback only, 8 topics, max. 100 records
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "candidates", "num_topics": 8, "limit": 100}'

# 15 topics without employee weighting
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "both", "num_topics": 15, "use_employee_weighting": false}'
```

After training, the model is automatically saved under `backend/models/saved_models/`.

### 8.2 Train Model via Training Script

Alternatively, the training script can be run directly (trains a combined model with 15 topics):

```bash
cd backend

# With uv
uv run python scripts/train_models.py

# With activated venv
python scripts/train_models.py
```

The script outputs information about loaded data, perplexity, and coherence score.

### 8.3 List Saved Models

```bash
curl http://localhost:8000/api/topics/models/list
```

Response:
```json
{
  "status": "success",
  "count": 4,
  "models": [
    "lda_model_20260214_233448",
    "lda_model_20260201_152130",
    "..."
  ]
}
```

### 8.4 Load a Saved Model

When restarting the backend, a previously trained model must be loaded:

```bash
curl -X POST "http://localhost:8000/api/topics/models/load?model_name=lda_model_20260214_233448"
```

### 8.5 Check Model Status

```bash
curl http://localhost:8000/api/topics/status
```

Shows whether a model is loaded and how many topics it contains.

### 8.6 Test the Model

After training you can test the model directly:

```bash
# Predict topics for a text
curl -X POST http://localhost:8000/api/topics/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "The work-life balance is excellent and the salary fair!", "threshold": 0.1}'

# Get topic-rating correlation
curl http://localhost:8000/api/topics/analyze/topic-rating-correlation

# Show all discovered topics
curl http://localhost:8000/api/topics/topics
```

### 8.7 Clean Up Old Models

Each training run generates several files (~6 files per model). To free up disk space:

```bash
cd backend/models/saved_models

# List all models
ls -la *.model

# Delete ALL old models (caution!)
rm -f lda_model_*.*

# Delete a specific model only
rm -f lda_model_20260201_143902.*
```

### 8.8 Use Swagger UI

All API calls above can also be conveniently executed via the **Swagger UI**:

1. Open **http://localhost:8000/docs** in your browser
2. Navigate to the **topics** section
3. Click on the desired endpoint (e.g. `/api/topics/train`)
4. Click **Try it out**, adjust the parameters, and click **Execute**

---

## 9. Common Problems & Solutions

### ❌ `uv: command not found`

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Then restart terminal or:
source ~/.bashrc   # or ~/.zshrc
```

### ❌ Port 8000 is in use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
# Restart backend
uv run uvicorn main:app --reload
```

### ❌ Only the companies Demo 1 to Demo 3 appear

The backend found no Supabase credentials and runs with the in-memory demo store. The `.env` file is missing or not correctly configured. See [Step 5](#5-configure-environment-variables).

### ❌ `ModuleNotFoundError: No module named '...'`

```bash
cd backend

# With uv
uv sync

# With pip
source .venv/bin/activate
pip install -r ../requirements.txt
```

### ❌ Frontend: `Module not found` or missing packages

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### ❌ `Model not trained` Error

Train an LDA model first:

```bash
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "employee", "num_topics": 5}'
```

### ❌ Python Cache Issues

```bash
# Delete all __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} +
```

### ❌ Old/corrupted models

```bash
cd backend/models/saved_models
rm -f lda_model_*.* 2>/dev/null
```

### ❌ Dashboard loading slowly

1. **Hard-Reload:** `Cmd+Shift+R` (Mac) / `Ctrl+Shift+F5` (Windows)
2. **Clear browser cache:** DevTools → Application → Clear Storage
3. **Check Network Tab:** API calls should run in parallel

---

## Quick Reference

```bash
# === Backend ===
cd backend
uv sync                              # Install dependencies
uv run uvicorn main:app --reload     # Start server
uv run pytest -q                     # Run tests

# === Frontend ===
cd frontend
npm install                          # Install dependencies
npm run dev                          # Start dev server
npm test                             # Run tests
npm run lint                         # Lint
npm run build                        # Production build

# === Cleanup ===
find . -type d -name "__pycache__" -exec rm -rf {} +   # Python cache
cd backend/models/saved_models && rm -f lda_model_*.*   # Old models
```
