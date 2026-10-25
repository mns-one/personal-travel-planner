# Wanderwise — Personalized Travel Itinerary Planner

A beginner friendly React and Python project that collects trip preferences and creates a simple starter itinerary.

## Phase 1 features

- Three step trip form for destination, dates, budget, travelers, interests, dietary needs, pace, and travel style.
- Frontend checks for required fields and date order, with backend validation using Pydantic.
- FastAPI endpoints to save a trip in memory and create a day-by-day draft.
- A prompt builder that turns saved preferences, including dietary and mobility needs, into structured AI instructions.
- Categorized attraction, dining, and experience suggestions, with optional Gemini generation and a local fallback.
- Structured morning, afternoon, and evening schedules, generated through a provider-based Groq integration or a local fallback.
- Framer Motion transitions and Lucide icons in a responsive interface.
- Pydantic models for trip request/response and registration, login, and token response data.

Groq is optional; without its key the app shows a starter schedule. Recommendation generation can use Gemini from Phase 3, while itinerary generation uses Groq in this phase. Authentication models are data contracts only; registration, login, password storage, and JWT issuance are not implemented. Trips are stored in memory and cleared when the backend restarts.

## Run locally

See [SETUP.md](SETUP.md). The API is documented in [API.md](API.md).
