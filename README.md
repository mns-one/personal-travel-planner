# Wanderwise

Wanderwise is a personal travel planner built with React and FastAPI. Enter your destination, dates, budget, group size, interests, travel pace, and travel needs to create a day-by-day itinerary.

## What it does

- Collects trip details in a step-by-step form.
- Uses Groq for attraction, dining, and experience recommendations, day-by-day itinerary generation, and itinerary refinements.
- Provides starter suggestions and a basic itinerary when Groq is not configured or returns an unusable response.
- Lets you refine a plan, save trips, view trip history, edit or delete trips, and share or export an itinerary.
- Stores trips in local SQLite by default, or Supabase when configured.
- Separates trips by a random browser ID stored in `localStorage`.

## Tech stack

- Frontend: React, Vite, Framer Motion, Lucide
- Backend: Python, FastAPI, Pydantic
- Storage: SQLite or Supabase
- Optional AI: Groq for all AI features

## Run locally

You need Python 3.10+ and Node.js 18+.

### 1. Start the backend

In a terminal at the project root:

```powershell
cd backend
python -m venv .venv
```

Activate the virtual environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies and start FastAPI:

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. API docs are at `http://localhost:8000/docs`.

### 2. Start the frontend

In a second terminal at the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

## Database

The app uses SQLite automatically when Supabase is not configured. The local database file is `backend/database/trips.db` and is excluded from Git.

To use Supabase:

1. Create a Supabase project.
2. Run [`backend/database/schema.sql`](backend/database/schema.sql) in the Supabase SQL Editor.
3. Copy `backend/.env.example` to `backend/.env`.
4. Set `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env`.
5. Restart the backend.

Keep `.env` and the service-role/secret key private. Never put the service key in frontend code or commit it. The current API has no login or per-user trip access, so keep a deployed demo private.

Each browser creates a random owner ID and sends it with trip API requests. Clearing browser storage or switching browsers creates a different ID, so the old trips will not appear. This is only a college-demo separation method, not authentication.

## Optional Groq AI

Set keys in `backend/.env` and restart FastAPI:

```env
GROQ_API_KEY=your-groq-key
```

`GROQ_MODEL` can optionally choose a model; the default is `llama-3.3-70b-versatile`. Without the key, the app uses starter suggestions and a basic itinerary. Keep the key in the backend only; do not add it to the React app.

## Project structure

```text
backend/
  app/                 FastAPI routes, schemas, prompts, and services
  database/schema.sql  Supabase table definition
  tests/               Backend API tests
frontend/
  src/                 React app and API client
```

## More information

- [Setup guide](SETUP.md)
- [API routes](API.md)
- [Deployment guide](DEPLOYMENT.md)
