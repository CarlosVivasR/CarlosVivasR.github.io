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

-- errors: client-side error log. Never store emails or personal data here,
-- just technical context (browser, action, message). For Carlos to debug
-- silent failures during the tournament.
create table if not exists errors (
  id          uuid        primary key default gen_random_uuid(),
  created_at  timestamptz default now(),
  context     text        not null,            -- which action failed (e.g. "submit_picks", "load_leaderboard")
  message     text        not null,            -- error.message
  user_agent  text,                            -- navigator.userAgent
  meta        jsonb                            -- any extra non-PII context
);


-- ----------------------------------------------------------------
-- 1b. CHECK CONSTRAINTS (data integrity)
-- ----------------------------------------------------------------
-- These prevent malformed payloads from reaching the table even via
-- direct API calls. Wrap in DO blocks to make idempotent.

do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'picks_positions_is_object') then
    alter table picks add constraint picks_positions_is_object
      check (jsonb_typeof(positions) = 'object');
  end if;
  if not exists (select 1 from pg_constraint where conname = 'picks_winners_is_object') then
    alter table picks add constraint picks_winners_is_object
      check (jsonb_typeof(winners) = 'object');
  end if;
  if not exists (select 1 from pg_constraint where conname = 'picks_starred_eight') then
    alter table picks add constraint picks_starred_eight
      check (array_length(starred, 1) = 8);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'picks_final_goals_a_range') then
    alter table picks add constraint picks_final_goals_a_range
      check (final_goals_a is null or (final_goals_a >= 0 and final_goals_a <= 30));
  end if;
  if not exists (select 1 from pg_constraint where conname = 'picks_final_goals_b_range') then
    alter table picks add constraint picks_final_goals_b_range
      check (final_goals_b is null or (final_goals_b >= 0 and final_goals_b <= 30));
  end if;
  if not exists (select 1 from pg_constraint where conname = 'picks_golden_boot_length') then
    alter table picks add constraint picks_golden_boot_length
      check (golden_boot is null or char_length(golden_boot) <= 80);
  end if;
end $$;


-- ----------------------------------------------------------------
-- 2. ROW LEVEL SECURITY
-- ----------------------------------------------------------------

alter table users            enable row level security;
alter table picks            enable row level security;
alter table official_results enable row level security;
alter table errors           enable row level security;


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


-- users delete: needed by admin's "delete participant" feature.
-- Cascade on picks.user_id auto-removes the user's picks.
drop policy if exists "anyone can delete user" on users;
create policy "anyone can delete user"
  on users for delete
  using (true);

-- errors: client can insert (write logs); admin can read.
drop policy if exists "anyone can log errors" on errors;
create policy "anyone can log errors"
  on errors for insert
  with check (true);

drop policy if exists "public read errors" on errors;
create policy "public read errors"
  on errors for select
  using (true);


-- ============================================================
-- END OF SCHEMA
-- ============================================================
