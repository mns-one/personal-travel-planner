"""Build a clear, personalized prompt for a future AI itinerary service."""

from .schemas import TripResponse


PACE_INSTRUCTIONS = {
    "relaxed": "Plan no more than 2 main activities per day and leave generous rest time.",
    "balanced": "Plan about 3 main activities per day, with sensible breaks between them.",
    "active": "Plan up to 4 main activities per day, grouping nearby places to reduce wasted travel time.",
}


def build_itinerary_prompt(trip: TripResponse) -> str:
    """Turn saved trip preferences into instructions an AI can follow."""
    interests = ", ".join(trip.interests) if trip.interests else "a mix of local highlights"
    dietary = ", ".join(trip.dietary_needs) if trip.dietary_needs else "no stated restrictions"
    mobility = ", ".join(trip.mobility_needs) if trip.mobility_needs else "no stated mobility needs"
    days = (trip.end_date - trip.start_date).days + 1

    return f"""You are a thoughtful travel-planning assistant. Create a practical, personalized itinerary using only the trip details below.

TRIP DETAILS
- Destination: {trip.destination}
- Dates: {trip.start_date.isoformat()} to {trip.end_date.isoformat()} ({days} calendar days)
- Total budget: {trip.budget:g} (currency not specified by traveler)
- Group size: {trip.travelers} traveler(s)
- Travel style: {trip.travel_style}
- Interests: {interests}
- Dietary needs: {dietary}
- Mobility needs: {mobility}
- Travel pace: {trip.travel_pace}

INSTRUCTIONS
- {PACE_INSTRUCTIONS[trip.travel_pace]}
- Choose activities that match the interests, group size, travel style, and trip dates.
- Keep the complete plan realistic for the total budget. Do not invent exact prices, opening hours, or availability.
- Respect every dietary need when suggesting meals. Do not assume a restaurant can accommodate a restriction; tell the traveler to confirm directly.
- Respect mobility needs by avoiding unsuitable activities and suggesting accessible routes or options where possible. If accessibility details are uncertain, say so and recommend checking with the venue.
- Group nearby activities together and include breaks and meal time.
- Within each day, sequence the suggested stops in a geographically sensible order to reduce backtracking. Prefer one compact area per day, and do not claim exact distances or travel times without reliable location data.
- If a preference is missing, make a conservative assumption and state it briefly instead of pretending it was provided.
- Do not claim to have booked anything.

OUTPUT FORMAT
Return a concise itinerary as JSON with one section per calendar day. Each day must contain its day number, date (YYYY-MM-DD), short theme, and morning, afternoon, evening, and notes string arrays. Order stops within each day geographically, keep nearby activities together, and adjust activity counts to the requested pace. Finish with a short assumptions and reminders note."""
