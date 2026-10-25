"""FastAPI application setup and health endpoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.trips import router as trips_router

app = FastAPI(title="Personalized Travel Planner API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(trips_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
