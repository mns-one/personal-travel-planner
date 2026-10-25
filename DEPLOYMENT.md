# Production deployment on Render

The root `render.yaml` defines two services: a Python FastAPI API and a static Vite/React site. It sets the public service URLs in `VITE_API_URL` and `CORS_ORIGINS`. Render static sites are built on a CDN and cannot use private service hostnames, so these values use the public `onrender.com` URLs.

## Before deploying

1. Push the repository to GitHub.
2. Create a Supabase project and run `backend/database/schema.sql` in its SQL Editor. SQLite on a hosted web service is temporary; use Supabase for data that must survive restarts.
3. In Render, choose **New → Blueprint** and connect the repository containing `render.yaml`.
4. Add `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` when Render prompts for the `sync: false` values. Set the service role key only on `wanderwise-api`.
5. Optionally provide `GROQ_API_KEY` for AI recommendations, itinerary generation, and refinements. Set `GROQ_MODEL` if you want a model other than the default. Without a key, the app uses its local fallback content.
6. Wait for the GitHub Actions checks to pass; both Render services deploy with the `checksPass` trigger.

The backend health endpoint is `/api/health`. The frontend is served as a static site with a rewrite to `index.html`, so query-string share links continue to open the React app. If you rename either Render service or attach custom domains, update `VITE_API_URL` and `CORS_ORIGINS`; frontend URL changes require a new static build.

## Local production build

```powershell
cd frontend
npm ci
npm run build
```

For the backend, run `pip install -r backend/requirements-dev.txt` from the repository root and `pytest backend/tests -q`.

## Important security limits

Authentication and user ownership are not implemented. The current service-role database access and trip routes let anyone who can reach the API manage saved trips. Do not use real private travel data or deploy this API for public use until authentication, owner checks, and access-controlled sharing links are implemented. Keep all provider and database keys in Render environment settings, never in the frontend bundle or repository.
