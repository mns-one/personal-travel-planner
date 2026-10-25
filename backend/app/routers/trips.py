"""Trip and recommendation API endpoints."""

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException

from ..prompt_builder import build_itinerary_prompt
from ..recommendation_service import get_recommendations
from ..schemas import (
    ItineraryRequest,
    ItineraryRefineRequest,
    ItineraryRefineResponse,
    ItineraryResponse,
    RecommendationResponse,
    TripCreate,
    TripResponse,
)
from ..services.itinerary import generate_itinerary as create_itinerary
from ..services.refinement import refine_itinerary as apply_refinement

router = APIRouter(prefix="/api", tags=["trips"])
trips: dict[UUID, TripResponse] = {}


def find_trip(trip_id: UUID) -> TripResponse:
    trip = trips.get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("/trips", response_model=TripResponse, status_code=201)
def create_trip(request: TripCreate):
    trip = TripResponse(id=uuid4(), **request.model_dump())
    trips[trip.id] = trip
    return trip


@router.get("/trips", response_model=list[TripResponse])
def list_trips():
    """Return trips created since this backend process started."""
    return list(trips.values())


@router.get("/trips/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: UUID):
    return find_trip(trip_id)


@router.post("/itineraries/generate", response_model=ItineraryResponse)
async def generate_itinerary(request: ItineraryRequest):
    trip = find_trip(request.trip_id)
    return await create_itinerary(trip)


@router.post("/itineraries/prompt")
def preview_itinerary_prompt(request: ItineraryRequest):
    trip = find_trip(request.trip_id)
    return {"trip_id": str(trip.id), "prompt": build_itinerary_prompt(trip)}


@router.post("/trips/{trip_id}/itinerary/refine", response_model=ItineraryRefineResponse)
async def refine_trip_itinerary(trip_id: UUID, request: ItineraryRefineRequest):
    trip = find_trip(trip_id)
    try:
        return await apply_refinement(trip, request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/trips/{trip_id}/recommendations", response_model=RecommendationResponse)
async def recommend_for_trip(trip_id: UUID):
    trip = find_trip(trip_id)
    return await get_recommendations(trip)
