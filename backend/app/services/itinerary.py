"""Generate and validate a structured day-by-day itinerary."""

import json
import logging

from pydantic import ValidationError

from ..prompt_builder import build_itinerary_prompt
from ..schemas import ItineraryDay, ItineraryResponse, TripResponse
from .ai import AIGenerationError, get_llm_provider
from .schedule_optimizer import optimize_itinerary

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You create safe, realistic travel plans. Follow the supplied preferences and return only valid JSON.
Do not invent confirmed prices, opening hours, bookings, or accessibility facts. Use this exact shape:
{"days":[{"day":1,"title":"Short day theme","date":"YYYY-MM-DD","morning":["activity"],"afternoon":["activity"],"evening":["activity"],"notes":["practical note"]}],"note":"brief assumptions and reminders"}
Include exactly one day for each trip date. Each slot value is a list of concise strings. Keep activity counts appropriate to the requested pace."""


def _fallback_itinerary(trip: TripResponse) -> ItineraryResponse:
    days = []
    day_count = (trip.end_date - trip.start_date).days + 1
    interests = ", ".join(trip.interests) if trip.interests else "local highlights"
    meal = ", ".join(trip.dietary_needs) if trip.dietary_needs else "local cuisine"
    mobility = ", ".join(trip.mobility_needs)

    for index in range(day_count):
        day_date = trip.start_date.fromordinal(trip.start_date.toordinal() + index)
        days.append(
            ItineraryDay(
                day=index + 1,
                title=f"Explore {trip.destination}",
                date=day_date,
                morning=[f"Start with a {interests} activity near your accommodation."],
                afternoon=["Choose an attraction in the same area and leave time for a break."],
                evening=[f"Find a {meal} meal near your final stop; confirm dietary options with the venue."],
                notes=[
                    f"Check step-free access for {mobility}." if mobility else "Confirm opening times and travel times before setting out."
                ],
            )
        )

    return ItineraryResponse(
        trip_id=trip.id,
        destination=trip.destination,
        days=optimize_itinerary(days, trip),
        note="Starter schedule organized by time of day and shared area hints. It does not use live maps. Set GROQ_API_KEY for an AI-generated itinerary; verify venue details before visiting.",
    )


async def generate_itinerary(trip: TripResponse) -> ItineraryResponse:
    """Generate with the configured LLM, falling back to a local schedule."""
    provider = get_llm_provider()
    if provider is None:
        return _fallback_itinerary(trip)

    try:
        prompt = build_itinerary_prompt(trip)
        raw_response = await provider.generate(SYSTEM_PROMPT, prompt)
        parsed = json.loads(raw_response)
        generated_days = [ItineraryDay.model_validate(day) for day in parsed["days"]]
        expected_days = (trip.end_date - trip.start_date).days + 1
        if len(generated_days) != expected_days:
            raise ValueError(f"Expected {expected_days} itinerary days, got {len(generated_days)}")
        for expected_number, (day, expected_date) in enumerate(
            zip(generated_days, (trip.start_date.fromordinal(trip.start_date.toordinal() + index) for index in range(expected_days))),
            start=1,
        ):
            if day.day != expected_number or day.date != expected_date:
                raise ValueError("AI returned incorrect day numbers or dates")
        generated_days = optimize_itinerary(generated_days, trip)
        return ItineraryResponse(
            trip_id=trip.id,
            destination=trip.destination,
            days=generated_days,
            note=parsed.get("note", "AI generated draft. Confirm venue details before visiting."),
        )
    except (AIGenerationError, KeyError, TypeError, ValueError, json.JSONDecodeError, ValidationError):
        logger.exception("Using fallback itinerary after AI response failure")
        return _fallback_itinerary(trip)
