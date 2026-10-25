"""Create personalized recommendations, with an optional AI service hook."""

import json
import logging

from pydantic import ValidationError

from .schemas import Recommendation, RecommendationResponse, TripResponse
from .services.ai import AIGenerationError, get_llm_provider

logger = logging.getLogger(__name__)


def _local_recommendations(trip: TripResponse) -> list[Recommendation]:
    """Return honest starter suggestions when no AI provider is configured."""
    selected = trip.interests or ["local culture", "food"]
    destination = trip.destination
    cost = {"budget": "low", "comfort": "moderate", "luxury": "high"}[trip.travel_style]
    meal_notes = ", ".join(trip.dietary_needs) or "your preferences"
    mobility_note = ", ".join(trip.mobility_needs)
    accessibility = (
        f" Check step-free access for: {mobility_note}."
        if mobility_note
        else " Check venue accessibility details before visiting."
    )
    return [
        Recommendation(
            name=f"Local highlights walk in {destination}",
            category="attraction",
            description=f"Explore central landmarks and public spaces in {destination} at your own pace.",
            why_it_matches=f"A flexible way to start, based on your interests: {', '.join(selected)}.{accessibility}",
            estimated_cost="free",
            interests=selected,
        ),
        Recommendation(
            name=f"A {trip.travel_style}-style local food stop",
            category="dining",
            description=f"Look for a well-reviewed local restaurant or market in {destination}.",
            why_it_matches=f"Choose a place that can accommodate {meal_notes}; contact it to confirm dietary options.",
            estimated_cost=cost,
            interests=[interest for interest in selected if interest.lower() in {"food", "culture"}],
        ),
        Recommendation(
            name=f"Small-group {selected[0].lower()} experience",
            category="experience",
            description=f"Find a local guided class, tour, or hands-on activity related to {selected[0].lower()} in {destination}.",
            why_it_matches=f"Matches your interest in {selected[0].lower()} and can be selected to suit a group of {trip.travelers}.",
            estimated_cost=cost,
            interests=[selected[0]],
        ),
    ]


async def get_recommendations(trip: TripResponse) -> RecommendationResponse:
    """Use Groq when configured; otherwise return categorized starter ideas."""
    provider = get_llm_provider()
    if provider:
        try:
            prompt = f"""Create exactly 5 personalized travel recommendations for this trip.

Trip details:
- Destination: {trip.destination}
- Dates: {trip.start_date.isoformat()} to {trip.end_date.isoformat()}
- Total budget: {trip.budget} (currency not specified)
- Travelers: {trip.travelers}
- Travel style: {trip.travel_style}
- Interests: {', '.join(trip.interests) or 'local highlights'}
- Dietary needs: {', '.join(trip.dietary_needs) or 'none stated'}
- Mobility needs: {', '.join(trip.mobility_needs) or 'none stated'}
- Pace: {trip.travel_pace}

Return a JSON object with a top-level `recommendations` array. Each object must have:
name, category (attraction/dining/experience), description, why_it_matches,
estimated_cost (free/low/moderate/high), and interests (string array).
Avoid claiming current opening hours, exact prices, availability, or accessibility
unless those details are supplied. Return only valid JSON."""
            raw_response = await provider.generate(
                "You are a careful travel recommendation assistant. Follow the trip preferences and return only the requested JSON.",
                prompt,
            )
            parsed = json.loads(raw_response)
            recommendations = [Recommendation.model_validate(item) for item in parsed["recommendations"]]
            if not recommendations:
                raise ValueError("The AI returned no recommendations")
            return RecommendationResponse(
                trip_id=trip.id,
                destination=trip.destination,
                recommendations=recommendations,
                source="ai",
                note="AI suggestions are a starting point. Confirm prices, opening times, dietary options, and accessibility with each venue.",
            )
        except (AIGenerationError, KeyError, TypeError, ValueError, ValidationError):
            # A provider error should not make the project unusable for a demo.
            logger.exception("Using starter recommendations after Groq generation failed")

    return RecommendationResponse(
        trip_id=trip.id,
        destination=trip.destination,
        recommendations=_local_recommendations(trip),
        source="curated_fallback",
        note="Starter suggestions based on your preferences. Set GROQ_API_KEY to enable AI-generated recommendations. Verify venue details before visiting.",
    )
