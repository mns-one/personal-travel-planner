"""Request and response models used by the API."""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class TripCreate(BaseModel):
    """Preferences collected by the guided trip form."""

    destination: str = Field(min_length=2, max_length=100)
    start_date: date
    end_date: date
    budget: float = Field(gt=0, le=10_000_000)
    travelers: int = Field(default=1, ge=1, le=20)
    interests: list[str] = Field(default_factory=list, max_length=10)
    dietary_needs: list[str] = Field(default_factory=list, max_length=10)
    mobility_needs: list[str] = Field(default_factory=list, max_length=10)
    travel_pace: Literal["relaxed", "balanced", "active"] = "balanced"
    travel_style: Literal["budget", "comfort", "luxury"] = "comfort"

    @model_validator(mode="after")
    def dates_must_be_in_order(self):
        if self.end_date < self.start_date:
            raise ValueError("End date must be on or after start date")
        if (self.end_date - self.start_date).days > 30:
            raise ValueError("A trip can be at most 31 days long")
        return self


class ItineraryRequest(BaseModel):
    trip_id: UUID


class ItineraryDay(BaseModel):
    day: int
    title: str
    date: date
    morning: list[str] = Field(default_factory=list)
    afternoon: list[str] = Field(default_factory=list)
    evening: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ItineraryResponse(BaseModel):
    trip_id: UUID
    destination: str
    days: list[ItineraryDay]
    note: str


class TripResponse(TripCreate):
    """Validated trip returned after creating or editing a trip."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: Literal["created"] = "created"
    itinerary: ItineraryResponse | None = None


class TripUpdate(BaseModel):
    """Fields that can be changed in a saved trip."""

    destination: str | None = Field(default=None, min_length=2, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = Field(default=None, gt=0, le=10_000_000)
    travelers: int | None = Field(default=None, ge=1, le=20)
    interests: list[str] | None = Field(default=None, max_length=10)
    dietary_needs: list[str] | None = Field(default=None, max_length=10)
    mobility_needs: list[str] | None = Field(default=None, max_length=10)
    travel_pace: Literal["relaxed", "balanced", "active"] | None = None
    travel_style: Literal["budget", "comfort", "luxury"] | None = None


class ItineraryRefineRequest(BaseModel):
    instruction: str = Field(min_length=3, max_length=500)
    day: int | None = Field(default=None, ge=1, le=31)
    itinerary: ItineraryResponse


class ItineraryRefineResponse(BaseModel):
    itinerary: ItineraryResponse
    assistant_message: str
    source: Literal["ai", "local"]


class Recommendation(BaseModel):
    name: str
    category: Literal["attraction", "dining", "experience"]
    description: str
    why_it_matches: str
    estimated_cost: Literal["free", "low", "moderate", "high"]
    interests: list[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    trip_id: UUID
    destination: str
    recommendations: list[Recommendation]
    source: Literal["ai", "curated_fallback"]
    note: str


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"

