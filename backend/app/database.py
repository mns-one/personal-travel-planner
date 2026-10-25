"""Shared database access using Supabase or a local SQLite database."""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any
from uuid import UUID

from dotenv import load_dotenv

load_dotenv()


class Database:
    """Small database wrapper for trip CRUD and saved itinerary data."""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.client = None
        self.service_client = None

        if self.url and (self.anon_key or self.service_role_key):
            try:
                from supabase import Client, create_client

                if self.anon_key:
                    self.client: Client = create_client(self.url, self.anon_key)
                if self.service_role_key:
                    self.service_client: Client = create_client(self.url, self.service_role_key)
                if not self.service_client:
                    # No privileged key: use the caller-limited anon client and its RLS rules.
                    self.service_client = self.client
                self.mode = "supabase"
            except Exception as error:
                raise RuntimeError("Could not initialize Supabase. Check its URL and keys.") from error
        else:
            self.mode = "sqlite"
            self.sqlite_path = Path(os.getenv("TRAVEL_PLANNER_DB", "database/trips.db"))
            if not self.sqlite_path.is_absolute():
                self.sqlite_path = Path(__file__).resolve().parents[1] / self.sqlite_path
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS trips (
                        id TEXT PRIMARY KEY,
                        owner_id TEXT NOT NULL,
                        preferences TEXT NOT NULL,
                        itinerary TEXT,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )"""
                )
                columns = {row["name"] for row in connection.execute("PRAGMA table_info(trips)")}
                if "owner_id" not in columns:
                    connection.execute("ALTER TABLE trips ADD COLUMN owner_id TEXT NOT NULL DEFAULT ''")

    def get_client(self):
        """Return the anon Supabase client when configured."""
        return self.client

    def get_service_client(self):
        """Return the server-side database client."""
        return self.service_client

    def _connect(self):
        connection = sqlite3.connect(self.sqlite_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _decode_row(row: Any) -> dict[str, Any] | None:
        if row is None:
            return None
        data = dict(row)
        if isinstance(data.get("preferences"), str):
            data["preferences"] = json.loads(data["preferences"])
        if isinstance(data.get("itinerary"), str):
            data["itinerary"] = json.loads(data["itinerary"])
        return data

    def create_trip(self, trip_id: UUID, owner_id: str, preferences: dict[str, Any]) -> dict[str, Any]:
        if self.mode == "supabase":
            response = self.get_service_client().table("trips").insert(
                {"id": str(trip_id), "owner_id": owner_id, "preferences": preferences, "itinerary": None}
            ).execute()
            return response.data[0]
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO trips (id, owner_id, preferences) VALUES (?, ?, ?)",
                (str(trip_id), owner_id, json.dumps(preferences)),
            )
        return self.get_trip(trip_id, owner_id)

    def list_trips(self, owner_id: str) -> list[dict[str, Any]]:
        if self.mode == "supabase":
            response = self.get_service_client().table("trips").select("*").eq("owner_id", owner_id).order("created_at", desc=True).execute()
            return response.data
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM trips WHERE owner_id = ? ORDER BY created_at DESC", (owner_id,)).fetchall()
        return [self._decode_row(row) for row in rows]

    def get_trip(self, trip_id: UUID, owner_id: str) -> dict[str, Any] | None:
        if self.mode == "supabase":
            response = self.get_service_client().table("trips").select("*").eq("id", str(trip_id)).eq("owner_id", owner_id).maybe_single().execute()
            return response.data
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM trips WHERE id = ? AND owner_id = ?", (str(trip_id), owner_id)).fetchone()
        return self._decode_row(row)

    def update_trip(self, trip_id: UUID, owner_id: str, preferences: dict[str, Any]) -> dict[str, Any] | None:
        if self.mode == "supabase":
            response = self.get_service_client().table("trips").update({"preferences": preferences, "itinerary": None}).eq("id", str(trip_id)).eq("owner_id", owner_id).execute()
            if not response.data:
                return None
            return self.get_trip(trip_id, owner_id)
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE trips SET preferences = ?, itinerary = NULL WHERE id = ? AND owner_id = ?",
                (json.dumps(preferences), str(trip_id), owner_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_trip(trip_id, owner_id)

    def save_itinerary(self, trip_id: UUID, owner_id: str, itinerary: dict[str, Any]) -> bool:
        if self.mode == "supabase":
            response = self.get_service_client().table("trips").update({"itinerary": itinerary}).eq("id", str(trip_id)).eq("owner_id", owner_id).execute()
            return bool(response.data)
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE trips SET itinerary = ? WHERE id = ? AND owner_id = ?",
                (json.dumps(itinerary), str(trip_id), owner_id),
            )
            return cursor.rowcount > 0

    def delete_trip(self, trip_id: UUID, owner_id: str) -> bool:
        if self.mode == "supabase":
            response = self.get_service_client().table("trips").delete().eq("id", str(trip_id)).eq("owner_id", owner_id).execute()
            return bool(response.data)
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM trips WHERE id = ? AND owner_id = ?", (str(trip_id), owner_id))
            return cursor.rowcount > 0


database = Database()
