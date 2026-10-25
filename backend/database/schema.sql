-- Run this in Supabase SQL Editor to create persistent trip storage.
-- Keep the service role key on the backend only; never place it in React.
create table if not exists public.trips (
    id uuid primary key,
    owner_id text not null,
    preferences jsonb not null,
    itinerary jsonb,
    created_at timestamptz not null default now()
);

-- Add the column to an existing table. Older trips get an empty owner ID and
-- stay hidden until assigned to a browser ID.
alter table public.trips add column if not exists owner_id text not null default '';

create index if not exists trips_created_at_idx on public.trips (created_at desc);
create index if not exists trips_owner_id_idx on public.trips (owner_id);
alter table public.trips enable row level security;

-- The browser sends a random owner ID with each API request. This is a demo
-- separation only, not authentication. The FastAPI server accesses this table
-- with the service role key and scopes queries by owner_id.
