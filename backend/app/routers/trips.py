"""Trip and recommendation API endpoints."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException

from ..prompt_builder import build_itinerary_prompt
from ..recommendation_service import get_recommendations
from ..database import database
from ..schemas import (
    ItineraryRequest,
    ItineraryRefineRequest,
    ItineraryRefineResponse,
    ItineraryResponse,
    RecommendationResponse,
    TripCreate,
    TripResponse,
    TripUpdate,
)
from ..services.itinerary import generate_itinerary as create_itinerary
from ..services.refinement import refine_itinerary as apply_refinement

router = APIRouter(prefix="/api", tags=["trips"])


def _to_trip(row: dict) -> TripResponse:
    return TripResponse(
        id=UUID(str(row["id"])),
        **row["preferences"],
        itinerary=row.get("itinerary"),
    )


def find_trip(trip_id: UUID, owner_id: str) -> TripResponse:
    row = database.get_trip(trip_id, owner_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return _to_trip(row)


@router.post("/trips", response_model=TripResponse, status_code=201)
def create_trip(request: TripCreate, owner_id: UUID = Header(alias="X-Owner-ID")):
    trip = TripResponse(id=uuid4(), **request.model_dump())
    row = database.create_trip(trip.id, str(owner_id), request.model_dump(mode="json"))
    return _to_trip(row)


@router.get("/trips", response_model=list[TripResponse])
def list_trips(owner_id: UUID = Header(alias="X-Owner-ID")):
    """Return trips saved in the configured database."""
    return [_to_trip(row) for row in database.list_trips(str(owner_id))]


@router.get("/trips/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: UUID, owner_id: UUID = Header(alias="X-Owner-ID")):
    return find_trip(trip_id, str(owner_id))


@router.patch("/trips/{trip_id}", response_model=TripResponse)
def update_trip(trip_id: UUID, request: TripUpdate, owner_id: UUID = Header(alias="X-Owner-ID")):
    current = find_trip(trip_id, str(owner_id))
    updated_data = current.model_dump(exclude={"id", "status", "itinerary"})
    updated_data.update(request.model_dump(exclude_unset=True, exclude_none=True))
    validated = TripCreate.model_validate(updated_data)
    row = database.update_trip(trip_id, str(owner_id), validated.model_dump(mode="json"))
    if row is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return _to_trip(row)


@router.delete("/trips/{trip_id}", status_code=204)
def delete_trip(trip_id: UUID, owner_id: UUID = Header(alias="X-Owner-ID")):
    if not database.delete_trip(trip_id, str(owner_id)):
        raise HTTPException(status_code=404, detail="Trip not found")


@router.post("/itineraries/generate", response_model=ItineraryResponse)
async def generate_itinerary(request: ItineraryRequest, owner_id: UUID = Header(alias="X-Owner-ID")):
    trip = find_trip(request.trip_id, str(owner_id))
    itinerary = await create_itinerary(trip)
    database.save_itinerary(trip.id, str(owner_id), itinerary.model_dump(mode="json"))
    return itinerary


@router.post("/itineraries/prompt")
def preview_itinerary_prompt(request: ItineraryRequest, owner_id: UUID = Header(alias="X-Owner-ID")):
    trip = find_trip(request.trip_id, str(owner_id))
    return {"trip_id": str(trip.id), "prompt": build_itinerary_prompt(trip)}


@router.post("/trips/{trip_id}/itinerary/refine", response_model=ItineraryRefineResponse)
async def refine_trip_itinerary(trip_id: UUID, request: ItineraryRefineRequest, owner_id: UUID = Header(alias="X-Owner-ID")):
    trip = find_trip(trip_id, str(owner_id))
    try:
        result = await apply_refinement(trip, request)
        database.save_itinerary(trip.id, str(owner_id), result.itinerary.model_dump(mode="json"))
        return result
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/trips/{trip_id}/recommendations", response_model=RecommendationResponse)
async def recommend_for_trip(trip_id: UUID, owner_id: UUID = Header(alias="X-Owner-ID")):
    trip = find_trip(trip_id, str(owner_id))
    return await get_recommendations(trip)
