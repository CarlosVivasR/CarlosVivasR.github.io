-- ============================================================
-- WC 2026 Pool — Supabase schema
-- ============================================================
-- This file is the canonical blueprint of the database used by the
-- World Cup 2026 prediction pool. If the Supabase project is lost,
-- deleted, or you want to recreate it elsewhere, paste this whole
-- file into Supabase → SQL Editor → New query → Run.
--
-- Project ref (current): mdiijmvjzjqnhvvjqqht
-- Region              : Europe
-- Plan                : Free tier
-- Last applied        : 2026-05-13
--
-- Notes:
--   * Run order matters — tables first, then RLS enable, then policies.
--   * `picks.user_id` is both PK and FK with ON DELETE CASCADE,
--     so deleting a user via admin automatically removes their picks.
--   * The deadline policy hard-blocks any insert into `picks` after
--     2026-06-11 16:00 UTC (kick-off Mexico vs South Africa).
-- ============================================================


-- ----------------------------------------------------------------
-- 1. TABLES
-- ----------------------------------------------------------------

create table if not exists users (
  id          uuid        primary key default gen_random_uuid(),
  name        text        not null,
  email       text        not null unique,
  joined_at   timestamptz default now()
);

create table if not exists picks (
  user_id        uuid        primary key references users(id) on delete cascade,
  positions      jsonb       not null,   -- {"A-Mexico": 1, "A-South Africa": 2, ...}
  starred        text[]      not null,   -- ['A','C','E','F','H','I','J','L']
  winners        jsonb       not null,   -- {"R32-1": "a", "R32-2": "b", ...}
  final_goals_a  int,
  final_goals_b  int,
  golden_boot    text,
  submitted_at   timestamptz default now()
);

create table if not exists official_results (
  id             int         primary key default 1,
  positions      jsonb,
  starred        text[],
  winners        jsonb,
  final_goals_a  int,
  final_goals_b  int,
  golden_boot    text,
  updated_at     timestamptz default now()
);


-- ----------------------------------------------------------------
-- 2. ROW LEVEL SECURITY
-- ----------------------------------------------------------------

alter table users            enable row level security;
alter table picks            enable row level security;
alter table official_results enable row level security;


-- ----------------------------------------------------------------
-- 3. POLICIES
-- ----------------------------------------------------------------

-- users: anyone can read the registry (needed for leaderboard joins)
-- and anyone can register themselves once.
drop policy if exists "public read users" on users;
create policy "public read users"
  on users for select
  using (true);

drop policy if exists "anyone can register" on users;
create policy "anyone can register"
  on users for insert
  with check (true);

-- picks: anyone can read all picks (needed for leaderboard); inserts
-- are allowed only BEFORE the WC 2026 kick-off (2026-06-11 16:00 UTC).
-- The picks.user_id PK enforces "one submission per user" automatically.
drop policy if exists "public read picks" on picks;
create policy "public read picks"
  on picks for select
  using (true);

drop policy if exists "anyone can submit picks once" on picks;
drop policy if exists "submit before deadline" on picks;
create policy "submit before deadline"
  on picks for insert
  with check (
    now() < '2026-06-11T16:00:00+00'::timestamptz
  );

-- official_results: world readable; writable by anyone authenticated
-- with the anon key. Real protection happens client-side via the
-- admin URL key in admin.html (security by obscurity — acceptable for
-- a friend pool, NOT for anything serious).
drop policy if exists "public read results" on official_results;
create policy "public read results"
  on official_results for select
  using (true);

drop policy if exists "anyone can write results" on official_results;
create policy "anyone can write results"
  on official_results for insert
  with check (true);

drop policy if exists "anyone can update results" on official_results;
create policy "anyone can update results"
  on official_results for update
  using (true)
  with check (true);


-- ============================================================
-- END OF SCHEMA
-- ============================================================
