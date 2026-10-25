"""Small deterministic schedule optimizer for generated day plans.

Without coordinates, this groups activities that mention the same area and
orders the available time slots in a steady morning-to-evening flow. It does
not claim to calculate real distances or travel times.
"""

import re

from ..schemas import ItineraryDay, TripResponse

AREA_WORDS = {
    "city center": "central",
    "city centre": "central",
    "downtown": "central",
    "old town": "historic",
    "historic quarter": "historic",
    "waterfront": "waterfront",
    "harbor": "waterfront",
    "harbour": "waterfront",
    "riverside": "riverside",
    "near your accommodation": "nearby",
}


def _area_key(activity: str) -> str | None:
    text = activity.lower()
    for phrase, key in AREA_WORDS.items():
        if phrase in text:
            return key
    match = re.search(r"\b(?:in|near|around|at) ([a-z][a-z -]{2,35})", text)
    return match.group(1).strip() if match else None


def _reorder_slot(items: list[str], preferred_area: str | None) -> list[str]:
    if len(items) < 2:
        return items
    return sorted(
        items,
        key=lambda item: (
            0 if preferred_area and _area_key(item) == preferred_area else 1,
            _area_key(item) or "",
        ),
    )


def optimize_day(day: ItineraryDay) -> ItineraryDay:
    """Keep matching place references together and preserve time-slot flow."""
    slots = [day.morning, day.afternoon, day.evening]
    area_counts: dict[str, int] = {}
    for slot in slots:
        for activity in slot:
            key = _area_key(activity)
            if key:
                area_counts[key] = area_counts.get(key, 0) + 1

    preferred_area = max(area_counts, key=area_counts.get) if area_counts else None
    return day.model_copy(
        update={
            "morning": _reorder_slot(day.morning, preferred_area),
            "afternoon": _reorder_slot(day.afternoon, preferred_area),
            "evening": _reorder_slot(day.evening, preferred_area),
        }
    )


def optimize_itinerary(days: list[ItineraryDay], trip: TripResponse) -> list[ItineraryDay]:
    """Apply pacing limits and group activities with shared area hints."""
    slot_limits = {"relaxed": 1, "balanced": 2, "active": 3}
    limit = slot_limits[trip.travel_pace]
    optimized = []
    for day in days:
        day = optimize_day(day)
        day = day.model_copy(
            update={
                "morning": day.morning[:limit],
                "afternoon": day.afternoon[:limit],
                "evening": day.evening[:limit],
            }
        )
        optimized.append(day)
    return optimized
