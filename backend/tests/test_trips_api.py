"""API smoke tests using a temporary SQLite database."""

from fastapi.testclient import TestClient

from backend.app.database import Database
from backend.app.main import app
from backend.app.routers import trips as trips_routes


def test_trip_create_generate_update_and_delete(tmp_path, monkeypatch):
    monkeypatch.setenv("TRAVEL_PLANNER_DB", str(tmp_path / "test-trips.db"))
    test_database = Database()
    monkeypatch.setattr(trips_routes, "database", test_database)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    client = TestClient(app)

    trip_data = {
        "destination": "Kyoto, Japan",
        "start_date": "2026-11-10",
        "end_date": "2026-11-11",
        "budget": 1200,
        "travelers": 2,
        "interests": ["Food", "Culture"],
        "dietary_needs": ["vegetarian"],
        "mobility_needs": [],
        "travel_pace": "balanced",
        "travel_style": "comfort",
    }
    created = client.post("/api/trips", json=trip_data)
    assert created.status_code == 201
    trip_id = created.json()["id"]
    assert created.json()["itinerary"] is None

    generated = client.post("/api/itineraries/generate", json={"trip_id": trip_id})
    assert generated.status_code == 200
    assert len(generated.json()["days"]) == 2
    assert generated.json()["days"][0]["morning"]

    fetched = client.get(f"/api/trips/{trip_id}")
    assert fetched.status_code == 200
    assert fetched.json()["itinerary"]["trip_id"] == trip_id
    assert len(client.get("/api/trips").json()) == 1

    updated = client.patch(f"/api/trips/{trip_id}", json={"destination": "Osaka, Japan"})
    assert updated.status_code == 200
    assert updated.json()["destination"] == "Osaka, Japan"
    assert updated.json()["itinerary"] is None

    deleted = client.delete(f"/api/trips/{trip_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/trips/{trip_id}").status_code == 404


def test_trip_validation_rejects_end_date_before_start_date():
    client = TestClient(app)
    response = client.post(
        "/api/trips",
        json={
            "destination": "Kyoto",
            "start_date": "2026-11-12",
            "end_date": "2026-11-10",
            "budget": 1000,
        },
    )
    assert response.status_code == 422
