# API contract

Base URL: `http://localhost:8000`. The frontend uses Vite to proxy `/api` calls to this service.

## `GET /api/health`

Returns `{ "status": "ok" }` when the service is running.

## `POST /api/trips`

Creates and stores a trip in memory. Successful response: HTTP 201.

```json
{
  "destination": "Kyoto, Japan",
  "start_date": "2026-11-10",
  "end_date": "2026-11-13",
  "budget": 2500,
  "travelers": 2,
  "interests": ["Food", "Culture"],
  "dietary_needs": ["vegetarian"],
  "mobility_needs": ["step-free routes"],
  "travel_pace": "balanced",
  "travel_style": "comfort"
}
```

Response adds an `id` UUID and `status: "created"`. Dates must be ordered and trips can span at most 31 calendar days. Budget must be positive; travelers must be between 1 and 20. Interests, dietary needs, and mobility needs each accept up to 10 strings. Invalid input returns HTTP 422 with Pydantic validation details.

## `POST /api/itineraries/generate`

Request: `{ "trip_id": "<UUID returned by create trip>" }`. Returns one structured day per trip date. Each day has a date, title, morning, afternoon, evening, and notes fields. When `GROQ_API_KEY` is configured, the API uses the Groq async provider and validates its JSON output with Pydantic. An optimizer applies pace limits and groups activity text that refers to the same area. Without the key, or if the model response is invalid, it returns a clearly labeled starter schedule. The project has no geocoding or maps data, so the optimizer does not calculate real distances or travel times. Unknown trips return HTTP 404.

## `POST /api/itineraries/prompt`

Request: `{ "trip_id": "<UUID returned by create trip>" }`. Returns `{ "trip_id": "...", "prompt": "..." }`: the structured natural-language prompt built from the saved destination, dates, budget, group size, style, interests, dietary needs, mobility needs, and pace. This is a prompt preview for learning and integration; it does not call an AI model. An unknown trip returns HTTP 404.

## `GET /api/trips`

Returns the list of trips held in memory by this running backend process.

## `POST /api/trips/{trip_id}/recommendations`

Returns `{ "trip_id", "destination", "recommendations", "source", "note" }`. Recommendations are categorized as `attraction`, `dining`, or `experience`, and include a description, match reason, cost level, and related interests. `source` is `ai` when Gemini returned validated results, or `curated_fallback` when no AI key is configured or the provider fails. Configure `GEMINI_API_KEY` to enable Gemini. Set optional `GEMINI_MODEL` to change the model (default `gemini-2.5-flash`). The response reminds users to check changing venue details.

## Itinerary generation

`POST /api/itineraries/generate` calls the itinerary service. Set `GROQ_API_KEY` to enable Groq; optional `GROQ_MODEL` selects a model (default `llama-3.3-70b-versatile`). Without a key, this service returns a local fallback itinerary. Both paths pass through the schedule optimizer. Recommendation generation remains a separate Phase 3 feature.

## `GET /api/trips/{trip_id}`

Returns a previously created trip or HTTP 404. Stored trips are cleared when the backend restarts.

## `POST /api/trips/{trip_id}/itinerary/refine`

Accepts `{ "instruction": "Make day 2 more relaxed", "day": 2, "itinerary": { ...current itinerary... } }`. `day` is optional; omit it or send `null` to refine the complete plan. The response contains the updated `itinerary`, an `assistant_message`, and `source` (`ai` or `local`). AI refinement uses the configured Groq provider. Without a key, the instruction is saved as a note on the selected day(s). The service checks that the itinerary belongs to the trip, preserves all dates, and rejects changes to untargeted days. Instructions are limited to 500 characters.

## Authentication model contracts

The backend defines `UserRegister` (`name`, valid `email`, password of 8–128 characters), `UserLogin` (valid `email` and password), and `TokenResponse` (`access_token`, `token_type: "bearer"`) Pydantic schemas. Registration, login, password hashing, and JWT creation are follow-on work; there are no authentication routes yet.
