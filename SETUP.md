# Run locally

You need Python 3.10+ and Node.js 18+ installed.

## 1. Start the backend

Open a terminal in the project folder:

```powershell
cd backend
python -m venv .venv
```

Activate the environment on Windows with `.venv\Scripts\Activate.ps1`, or on macOS/Linux with `source .venv/bin/activate`. Then install and run:

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is at `http://localhost:8000`; interactive API docs are at `http://localhost:8000/docs`.

## 2. Start the frontend

Open a second terminal in the project folder:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (usually `http://localhost:5173`). Vite forwards `/api` requests to the backend on port 8000.

Trips are held in backend memory and cleared when it restarts. The auth schemas do not yet implement authentication.

## Optional AI generation

The app works without an AI API key and shows clearly labeled starter suggestions and schedules. To enable Groq itinerary generation, set `GROQ_API_KEY` in the backend terminal before starting Uvicorn. You can optionally set `GROQ_MODEL`; the default is `llama-3.3-70b-versatile`. Keep the key private and do not put it in frontend code.

With the same key configured, the itinerary screen can also send conversational refinement requests to Groq. Without it, the app keeps the itinerary and records the request as a note on the selected day(s).
