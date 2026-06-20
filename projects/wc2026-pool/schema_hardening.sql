-- ============================================================================
-- WC2026 Pool — RLS HARDENING (P0 security fix)
-- Run this in the Supabase SQL editor:  Dashboard → SQL editor → paste → Run.
--
-- WHAT IT CLOSES (current holes — anyone with the public anon key can do these):
--   • INSERT/UPDATE official_results  → falsify results, reorder the leaderboard
--   • DELETE users                    → wipe participants (cascades to their picks)
--
-- WHAT IT KEEPS WORKING:
--   • public reads (leaderboard), register, submit-picks-before-deadline, error logs
--
-- Pick ONE admin path below for writing official results, then run.
-- ============================================================================

-- --- 1) Remove the public write paths on official_results -------------------
drop policy if exists "anyone can write results"  on official_results;
drop policy if exists "anyone can update results" on official_results;

-- --- 2) Remove the public DELETE on users (no replacement needed) -----------
--     If you ever need to remove a participant, do it from the dashboard.
drop policy if exists "anyone can delete user" on users;


-- ============================================================================
-- ADMIN PATH — choose A or B (leave the other commented out)
-- ============================================================================

-- OPTION B (RECOMMENDED, simplest, zero code change): NO public write at all.
--   You enter official results from the Supabase dashboard (Table editor →
--   official_results → edit the id=1 row) after each match. admin.html becomes
--   read-only. Nobody can ever write results via the public API → unsabotageable.
--   → Just run sections 1 & 2 above and stop here. Done.

-- OPTION A (CHOSEN): writes require a logged-in admin. admin.html now has a
--   Supabase Auth login (already added). Before this works you must, in the
--   Supabase dashboard:
--     1. Authentication → Providers → Email: keep enabled.
--     2. Authentication → Sign In / Providers (or Settings): DISABLE "Allow new
--        users to sign up"  (so "authenticated" = only you, not the public).
--     3. Authentication → Users → "Add user" → create ONE user (your email +
--        a password). That is the account you log into admin.html with.
--   Then run the two policies below:

create policy "admin write results"
  on official_results for insert to authenticated with check (true);
create policy "admin update results"
  on official_results for update to authenticated using (true) with check (true);

--   STRONGER (optional — lock to your exact account instead of any authenticated
--   user, in case sign-ups ever get re-enabled): after creating your user, copy
--   its UUID from Authentication → Users and replace the two policies above with
--   `using (auth.uid() = 'YOUR-ADMIN-UUID')` / `with check (auth.uid() = 'YOUR-ADMIN-UUID')`.


-- ============================================================================
-- 3) PII note (lower urgency, do when convenient)
-- ============================================================================
--   "public read users" currently exposes name + email to anyone with the anon
--   key. The leaderboard only needs name. Recommended: stop reading email
--   client-side and expose a view without it, e.g.:
--
--   create or replace view public.leaderboard_users as
--     select id, name, joined_at from public.users;   -- no email
--   grant select on public.leaderboard_users to anon;
--   -- then drop "public read users" and have the client read the view.
