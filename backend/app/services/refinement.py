"""Conversationally refine a generated itinerary while retaining context."""

import json
import logging

from pydantic import ValidationError

from ..schemas import (
    ItineraryDay,
    ItineraryRefineRequest,
    ItineraryRefineResponse,
    TripResponse,
)
from .ai import AIGenerationError, get_llm_provider
from .schedule_optimizer import optimize_itinerary

logger = logging.getLogger(__name__)

REFINE_SYSTEM_PROMPT = """You are helping a traveler revise an existing itinerary. Apply the requested change while preserving all unrelated days and preferences. Keep every trip date, respect the travel pace, budget, dietary needs, and mobility needs. Return only JSON with keys: days (same structured shape as the supplied itinerary) and note (a short explanation of the changes). Do not invent confirmed prices, opening hours, bookings, or accessibility facts."""


def _local_refinement(request: ItineraryRefineRequest) -> ItineraryRefineResponse:
    """Provide a safe local response when no LLM key is available."""
    itinerary = request.itinerary.model_copy(deep=True)
    target_days = itinerary.days
    if request.day is not None:
        target_days = [day for day in itinerary.days if day.day == request.day]

    instruction = request.instruction.strip()
    message = "I kept your existing plan and added your request as a note. Add a Groq API key to regenerate activities with AI."
    if not target_days:
        return ItineraryRefineResponse(
            itinerary=itinerary,
            assistant_message="That day is not part of this trip, so I left the itinerary unchanged.",
            source="local",
        )

    for day in target_days:
        day.notes.append(f"Requested adjustment: {instruction}")
    return ItineraryRefineResponse(itinerary=itinerary, assistant_message=message, source="local")


async def refine_itinerary(trip: TripResponse, request: ItineraryRefineRequest) -> ItineraryRefineResponse:
    """Ask the configured model to revise the itinerary, with a local fallback."""
    if request.itinerary.trip_id != trip.id:
        raise ValueError("The itinerary does not belong to this trip")
    if len(request.itinerary.days) != (trip.end_date - trip.start_date).days + 1:
        raise ValueError("The itinerary day count does not match the trip dates")
    if request.day and request.day > len(request.itinerary.days):
        raise ValueError("The requested day is not part of this trip")

    provider = get_llm_provider()
    if provider is None:
        return _local_refinement(request)

    context = {
        "traveler_preferences": trip.model_dump(mode="json"),
        "current_itinerary": request.itinerary.model_dump(mode="json"),
        "request": request.instruction,
        "only_change_day": request.day,
    }
    try:
        raw = await provider.generate(REFINE_SYSTEM_PROMPT, json.dumps(context))
        parsed = json.loads(raw)
        updated_days = [ItineraryDay.model_validate(day) for day in parsed["days"]]
        if len(updated_days) != len(request.itinerary.days):
            raise ValueError("The revised itinerary must keep the same number of days")
        for expected_day, (day, old_day) in enumerate(zip(updated_days, request.itinerary.days), start=1):
            if day.day != expected_day or day.date != old_day.date:
                raise ValueError("The revised itinerary must keep the original day numbers and dates")
            if request.day is not None and day.day != request.day and day != old_day:
                raise ValueError("The model changed a day outside the requested day")

        updated = request.itinerary.model_copy(
            update={"days": optimize_itinerary(updated_days, trip), "note": parsed.get("note", "Itinerary updated from your request. Confirm details before visiting.")}
        )
        return ItineraryRefineResponse(
            itinerary=updated,
            assistant_message=parsed.get("note", "I updated the itinerary based on your request."),
            source="ai",
        )
    except (AIGenerationError, KeyError, TypeError, ValueError, json.JSONDecodeError, ValidationError):
        logger.exception("Using local refinement response after AI failure")
        return _local_refinement(request)
