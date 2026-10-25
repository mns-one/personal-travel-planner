# API contract

Base URL: `http://localhost:8000`. The frontend uses Vite to proxy `/api` calls to this service.

All trip endpoints require an `X-Owner-ID` header containing a UUID. The frontend creates a random ID and stores it in browser `localStorage`. Requests with a different ID cannot list, fetch, edit, generate, or delete those trips. This is temporary demo separation, not authentication.

## `GET /api/health`

Returns `{ "status": "ok" }` when the service is running.

## `POST /api/trips`

Creates and persistently stores a trip for the owner ID in `X-Owner-ID`. Successful response: HTTP 201. Response includes `itinerary: null` until one is generated.

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

Returns trips belonging to the owner ID in `X-Owner-ID`, including saved itineraries.

## `PATCH /api/trips/{trip_id}`

Updates any supplied trip preference fields. The merged preferences are validated as a complete trip before saving. Returns the updated trip; invalid dates or other fields return HTTP 422.

## `DELETE /api/trips/{trip_id}`

Deletes the trip and its saved itinerary. Returns HTTP 204, or HTTP 404 if it does not exist.

## `POST /api/trips/{trip_id}/recommendations`

Returns `{ "trip_id", "destination", "recommendations", "source", "note" }`. Recommendations are categorized as `attraction`, `dining`, or `experience`, and include a description, match reason, cost level, and related interests. Recommendations use Groq when `GROQ_API_KEY` is configured; otherwise, or if generation fails, the API returns starter suggestions with `source: "curated_fallback"`. The response reminds users to check changing venue details.

## Itinerary generation

`POST /api/itineraries/generate` calls the itinerary service and saves the result to its trip. Set `GROQ_API_KEY` to enable Groq for itinerary generation, recommendations, and refinements; optional `GROQ_MODEL` selects a model (default `openai/gpt-oss-20b`). Without a key, these features use local fallback content. Generated itineraries pass through the schedule optimizer.

## `GET /api/trips/{trip_id}`

Returns a previously created trip and its saved itinerary (if generated), or HTTP 404.

## Sharing and export

The frontend shares a URL with the trip ID in the `?trip=` query parameter. Opening it fetches the saved trip through `GET /api/trips/{trip_id}` and displays the itinerary in view mode. The browser can also download the trip as Markdown or JSON; those exports are generated locally from the response and need no extra API endpoint. The viewer must have the same browser owner ID, so the link does not grant access from another browser.

## `POST /api/trips/{trip_id}/itinerary/refine`

Accepts `{ "instruction": "Make day 2 more relaxed", "day": 2, "itinerary": { ...current itinerary... } }`. `day` is optional; omit it or send `null` to refine the complete plan. The response contains the updated `itinerary`, an `assistant_message`, and `source` (`ai` or `local`). AI refinement uses the configured Groq provider. Without a key, the instruction is saved as a note on the selected day(s). The service checks that the itinerary belongs to the trip, preserves all dates, and rejects changes to untargeted days. Instructions are limited to 500 characters.

## Authentication model contracts

The backend defines `UserRegister` (`name`, valid `email`, password of 8–128 characters), `UserLogin` (valid `email` and password), and `TokenResponse` (`access_token`, `token_type: "bearer"`) Pydantic schemas. Registration, login, password hashing, and JWT creation are follow-on work; there are no authentication routes yet.
