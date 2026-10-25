"""FastAPI application setup and health endpoint."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.trips import router as trips_router

app = FastAPI(title="Personalized Travel Planner API", version="1.0.0")
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(trips_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
