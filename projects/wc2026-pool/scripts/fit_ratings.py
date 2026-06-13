#!/usr/bin/env python3
"""
fit_ratings.py — CANONICAL offline fitter for the WC 2026 pool prediction app.

Consolidates the four validated models (models/dixon_coles.py, models/elo.py,
models/poisson_glm.py, models/blend.py) into ONE reproducible fitter and emits
the production `ratings.json` the client-side JS ships.

What it does
------------
1. Dixon-Coles ratings core (the shipped predictor), fit on ALL history with the
   frozen hyperparameters the report locked in:
       - exponential time-decay, half-life 1460 days,
       - friendly down-weight 0.7,
       - ridge 0.03 on attack/defence (minnow shrinkage),
       - sum-to-zero identifiability (means absorbed into mu),
       - home advantage gamma applied ONLY when neutral == False,
       - FITTED rho (Dixon-Coles low-score correction; ~ -0.03, NOT 0.13).
   Emits per-team {atk, def} + scalars {mu, gamma, rho}. This is the Maher/DC
   weighted-Poisson MLE from poisson_glm.py (analytic gradient), which the report
   designates as the consolidated core.

2. Elo coverage layer: World-Football-style Elo rebuilt by replaying all history
   (importance K-weights, MoV multiplier, +home term), plus an ordered-logit
   dr -> (H/D/A) mapping with params {s, tau} fit offline. Emits the full per-team
   rating table.

3. A no-leakage walk-forward backtest (expanding-origin, 90-day refit) recomputing
   RPS / Brier / log-loss / accuracy / ECE overall and on the major-tournament
   slice, with a climatology baseline — the honest, reproducible numbers shown to
   users.

4. Team keying & coverage: BOTH dc.teams and elo.ratings are keyed by a NORMALISED
   key (lowercase, NFD accent-stripped, non-letters removed) with aliases so the
   schedule short-forms ("USA", "Bosnia & Herzegovina") resolve. Every one of the
   48 WC2026 teams is verified to resolve; any missing/data-sparse team is given a
   shrunk-to-mean rating and listed.

5. Writes ratings.json to BOTH the scratch dir and the shipped web project path.

Reproducible: python3 + numpy/scipy/pandas only. Run to completion:
    python3 fit_ratings.py
"""

import json
import re
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

# ---------------------------------------------------------------- paths
# Repo-portable paths (this script lives in projects/wc2026-pool/scripts/).
ROOT = Path(__file__).resolve().parent.parent            # projects/wc2026-pool
DATA = ROOT / "scripts" / "results.csv"                  # martj42 raw CSV (auto-downloaded if missing)
WC2026_INDEX = ROOT / "data" / "teams" / "index.json"
OUT_LOCAL = ROOT / "data" / "ratings.json"
OUT_SHIPPED = OUT_LOCAL                                   # single shipped output
# Auto-download the public CC0 dataset if absent (CI). The fit only reads
# date,home_team,away_team,home_score,away_score,tournament,neutral — all in the raw CSV.
if not DATA.exists():
    import urllib.request
    DATA.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/martj42/international_results/master/results.csv", DATA)

# ---------------------------------------------------------------- frozen hyperparameters (report §3b / §5 Stage 0)
HALF_LIFE_DAYS = 1460          # exponential time-decay half-life
FRIENDLY_WEIGHT = 0.7          # friendly down-weight
RIDGE = 0.03                   # attack/defence ridge shrinkage
MAX_GOALS = 10                 # scoreline grid truncation (11x11)
XI = np.log(2) / HALF_LIFE_DAYS

# Elo config (eloratings.net-style)
ELO_INIT = 1500.0
ELO_HFA = 65.0
ELO_DIVISOR = 400.0

# backtest config
TEST_START = pd.Timestamp("2022-01-01")     # forward-in-time hold-out (incl. WC2022)
CAL_START = pd.Timestamp("2018-01-01")      # Elo/ordered-logit calibration era (pre-test)
REFIT_STEP_DAYS = 90                         # DC expanding-origin refit cadence

MAJOR_PAT = (r"FIFA World Cup|UEFA Euro|Copa Am|African Cup of Nations|AFC Asian Cup|"
             r"UEFA Nations League|CONCACAF Nations|Gold Cup|Confederations")

# ---------------------------------------------------------------- normalisation + aliases
def norm_key(name: str) -> str:
    """lowercase, NFD accent-stripped, non-letters removed."""
    s = unicodedata.normalize("NFD", str(name))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z]", "", s)
    return s

# Aliases mapping schedule-short-form normalisation -> canonical (data-name) key.
# Verified against the actual martj42 data names and the web schedule short forms:
#   schedule "USA"                  -> norm "usa"               -> data "United States" -> "unitedstates"
#   schedule "Bosnia & Herzegovina" -> norm "bosniaherzegovina" -> data "Bosnia and Herzegovina" -> "bosniaandherzegovina"
# martj42 itself uses: "Czech Republic" (NOT Czechia), "Turkey" (NOT Türkiye),
# "DR Congo", "Curaçao", "Cape Verde" — those already match the schedule forms.
ALIASES = {
    "usa": "unitedstates",
    "bosniaherzegovina": "bosniaandherzegovina",
    # robustness aliases (other common short/alt forms the JS might normalise to):
    "czechia": "czechrepublic",
    "turkiye": "turkey",
    "congodr": "drcongo",
    "caboverde": "capeverde",
    "korearepublic": "southkorea",
    "republicofkorea": "southkorea",
    "unitedstatesofamerica": "unitedstates",
}


# ============================ DATA ==========================================
def load():
    df = pd.read_csv(DATA, parse_dates=["date"])
    df = df.dropna(subset=["home_score", "away_score"]).copy()
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    df["neutral"] = df["neutral"].astype(bool)
    df = df.sort_values("date").reset_index(drop=True)
    df["is_friendly"] = df["tournament"].str.contains("Friendly", case=False, na=False)
    df["is_major"] = df["tournament"].str.contains(MAJOR_PAT, case=False, regex=True, na=False)
    df["home_adv"] = (~df["neutral"]).astype(float)

    def outcome(r):
        if r.home_score > r.away_score:
            return 0
        if r.home_score == r.away_score:
            return 1
        return 2
    df["outcome"] = df.apply(outcome, axis=1)
    return df


# ============================ DIXON-COLES (Maher/DC weighted Poisson) =======
def dc_tau(xs, ys, lh, la, rho):
    t = np.ones_like(lh, dtype=float)
    m00 = (xs == 0) & (ys == 0)
    m01 = (xs == 0) & (ys == 1)
    m10 = (xs == 1) & (ys == 0)
    m11 = (xs == 1) & (ys == 1)
    t = np.where(m00, 1.0 - lh * la * rho, t)
    t = np.where(m01, 1.0 + lh * rho, t)
    t = np.where(m10, 1.0 + la * rho, t)
    t = np.where(m11, 1.0 - rho, t)
    return np.clip(t, 1e-9, None)


def fit_dixon_coles(d, ref_date, xi=XI, friendly_w=FRIENDLY_WEIGHT, ridge=RIDGE,
                    rho_init=0.0, maxiter=400):
    """Weighted Poisson MLE on matches strictly before ref_date.
    log lambda_h = mu + atk_i - def_j + gamma*home_adv ; log lambda_a = mu + atk_j - def_i.
    Sum-to-zero on atk/def (means absorbed into mu). rho fit on the four DC cells."""
    d = d[d["date"] < ref_date]
    teams = sorted(set(d["home_team"]) | set(d["away_team"]))
    idx = {t: k for k, t in enumerate(teams)}
    n = len(teams)
    hi = d["home_team"].map(idx).to_numpy()
    ai = d["away_team"].map(idx).to_numpy()
    hg = d["home_score"].to_numpy().astype(float)
    ag = d["away_score"].to_numpy().astype(float)
    adv = d["home_adv"].to_numpy()

    delta = (ref_date - d["date"]).dt.days.to_numpy().astype(float)
    w = np.exp(-xi * delta)
    w = w * np.where(d["is_friendly"].to_numpy(), friendly_w, 1.0)
    w = w / w.mean()

    # params [mu, gamma, atk(n), def(n)] — weighted Poisson NLL with analytic gradient
    p0 = np.concatenate([[0.0, 0.25], np.zeros(n), np.zeros(n)])

    def negll_grad(p):
        mu = p[0]; gamma = p[1]
        atk = p[2:2 + n]; dfn = p[2 + n:2 + 2 * n]
        eta_h = mu + atk[hi] - dfn[ai] + gamma * adv
        eta_a = mu + atk[ai] - dfn[hi]
        lh = np.exp(np.clip(eta_h, -10, 4))
        la = np.exp(np.clip(eta_a, -10, 4))
        nll = np.sum(w * (lh - hg * eta_h)) + np.sum(w * (la - ag * eta_a))
        nll += ridge * (np.sum(atk ** 2) + np.sum(dfn ** 2))
        rh = w * (lh - hg)
        ra = w * (la - ag)
        g = np.zeros_like(p)
        g[0] = rh.sum() + ra.sum()
        g[1] = (rh * adv).sum()
        gatk = np.zeros(n); gdef = np.zeros(n)
        np.add.at(gatk, hi, rh)
        np.add.at(gatk, ai, ra)
        np.add.at(gdef, ai, -rh)
        np.add.at(gdef, hi, -ra)
        gatk += 2 * ridge * atk
        gdef += 2 * ridge * dfn
        g[2:2 + n] = gatk
        g[2 + n:2 + 2 * n] = gdef
        return nll, g

    res = minimize(negll_grad, p0, jac=True, method="L-BFGS-B",
                   options={"maxiter": maxiter, "maxfun": maxiter * 100, "ftol": 1e-9})
    mu = res.x[0]; gamma = res.x[1]
    atk = res.x[2:2 + n]; dfn = res.x[2 + n:2 + 2 * n]
    # re-centre to sum-to-zero (absorb means into mu; lambdas unchanged)
    mu = mu + atk.mean() - dfn.mean()
    atk = atk - atk.mean()
    dfn = dfn - dfn.mean()

    # fit rho on the four DC low-score cells
    lh_all = np.exp(np.clip(mu + atk[hi] - dfn[ai] + gamma * adv, -10, 4))
    la_all = np.exp(np.clip(mu + atk[ai] - dfn[hi], -10, 4))

    def rho_nll(rho):
        tau = dc_tau(hg, ag, lh_all, la_all, rho[0])
        return -np.sum(w * np.log(tau))

    rr = minimize(rho_nll, [rho_init], method="L-BFGS-B",
                  bounds=[(-0.15, 0.25)], options={"maxiter": 80})
    rho = float(rr.x[0])

    return {
        "mu": float(mu), "gamma": float(gamma), "rho": rho,
        "atk": dict(zip(teams, atk)), "dfn": dict(zip(teams, dfn)),
        "teams": set(teams),
    }


def dc_predict_1x2(model, home, away, neutral):
    atk = model["atk"]; dfn = model["dfn"]
    a_h = atk.get(home, 0.0); d_h = dfn.get(home, 0.0)
    a_a = atk.get(away, 0.0); d_a = dfn.get(away, 0.0)
    adv = 0.0 if neutral else 1.0
    lh = float(np.clip(np.exp(model["mu"] + a_h - d_a + model["gamma"] * adv), 1e-4, 30))
    la = float(np.clip(np.exp(model["mu"] + a_a - d_h), 1e-4, 30))
    gh = np.arange(0, MAX_GOALS + 1)
    ph = poisson.pmf(gh, lh)
    pa = poisson.pmf(gh, la)
    grid = np.outer(ph, pa)
    xs, ys = np.meshgrid(gh, gh, indexing="ij")
    tau = dc_tau(xs.ravel(), ys.ravel(), np.full(xs.size, lh), np.full(xs.size, la), model["rho"])
    grid = grid * tau.reshape(grid.shape)
    grid = grid / grid.sum()
    pH = np.tril(grid, -1).sum()
    pA = np.triu(grid, 1).sum()
    pD = np.trace(grid)
    s = pH + pD + pA
    return np.array([pH / s, pD / s, pA / s])


# ============================ ELO ===========================================
def importance_K(t):
    t = t.lower()
    if "world cup" in t and "qualif" not in t:
        return 60.0
    if t in ("uefa euro", "copa américa", "copa america", "african cup of nations",
             "afc asian cup", "gold cup") or "nations league" in t:
        return 50.0
    if "qualif" in t:
        return 40.0
    if "friendly" in t:
        return 20.0
    return 35.0


def mov_mult(goal_diff, rating_diff_winner):
    gd = abs(goal_diff)
    if gd <= 1:
        g = 1.0
    elif gd == 2:
        g = 1.5
    else:
        g = (11.0 + gd) / 8.0
    return g * (2.2 / ((rating_diff_winner * 0.001) + 2.2))


def elo_replay(df):
    """Walk forward; return PRE-match adjusted diffs (no leakage) and final ratings."""
    ratings = {}
    diffs = np.empty(len(df))
    for i, row in enumerate(df.itertuples(index=False)):
        h, a = row.home_team, row.away_team
        rh = ratings.get(h, ELO_INIT)
        ra = ratings.get(a, ELO_INIT)
        hfa = 0.0 if row.neutral else ELO_HFA
        rh_adj = rh + hfa
        diffs[i] = rh_adj - ra
        hs, as_ = row.home_score, row.away_score
        if hs > as_:
            sh = 1.0
        elif hs < as_:
            sh = 0.0
        else:
            sh = 0.5
        K = importance_K(row.tournament)
        exp_h = 1.0 / (1.0 + 10 ** ((ra - rh_adj) / ELO_DIVISOR))
        gd = hs - as_
        if gd != 0:
            winner_rd = (rh_adj - ra) if gd > 0 else (ra - rh_adj)
            mult = mov_mult(gd, winner_rd)
        else:
            mult = 1.0
        delta = K * mult * (sh - exp_h)
        ratings[h] = rh + delta
        ratings[a] = ra - delta
    return diffs, ratings


def elo_probs(diff, s, tau):
    z = diff / s
    pH = 1.0 / (1.0 + np.exp(-(z - tau)))
    pA = 1.0 / (1.0 + np.exp(-(-z - tau)))
    pD = np.clip(1.0 - pH - pA, 1e-6, None)
    Z = pH + pD + pA
    return np.vstack([pH / Z, pD / Z, pA / Z]).T


def fit_ordered_logit(diff, y):
    def nll(params):
        s, tau = params
        if s <= 1.0 or tau <= 0:
            return 1e9
        P = elo_probs(diff, s, tau)
        p = P[np.arange(len(y)), y]
        return -np.mean(np.log(np.clip(p, 1e-12, 1.0)))
    res = minimize(nll, x0=[200.0, 0.5], method="Nelder-Mead",
                   options={"xatol": 1e-4, "fatol": 1e-8, "maxiter": 5000})
    return float(res.x[0]), float(res.x[1])


# ============================ METRICS =======================================
def rps_mat(P, y):
    cp = np.cumsum(P, axis=1)
    oh = np.zeros_like(P)
    oh[np.arange(len(y)), y] = 1.0
    co = np.cumsum(oh, axis=1)
    return np.sum((cp - co) ** 2, axis=1) / (P.shape[1] - 1)


def brier_mat(P, y):
    oh = np.zeros_like(P)
    oh[np.arange(len(y)), y] = 1.0
    return np.sum((P - oh) ** 2, axis=1)


def logloss_mat(P, y):
    p = np.clip(P[np.arange(len(y)), y], 1e-12, 1)
    return -np.log(p)


def ece_homewin(P, y, nb=10):
    """Expected calibration error on the home-win probability (quantile bins)."""
    p = P[:, 0]
    yh = (np.asarray(y) == 0).astype(float)
    order = np.argsort(p)
    p = p[order]; yh = yh[order]
    bins = np.array_split(np.arange(len(p)), nb)
    ece = 0.0
    for b in bins:
        if len(b) == 0:
            continue
        ece += len(b) / len(p) * abs(p[b].mean() - yh[b].mean())
    return float(ece)


# ============================ BACKTEST ======================================
def walk_forward_backtest(df):
    """No-leakage expanding-origin backtest of the SHIPPED Dixon-Coles core.
    Refit every REFIT_STEP_DAYS on all data strictly before the origin; predict the
    next block. Returns (P, y, is_major). Also fits/applies Elo on the same matches."""
    test = df[df["date"] >= TEST_START].copy()
    origins = pd.date_range(TEST_START, df["date"].max(), freq=f"{REFIT_STEP_DAYS}D")
    P_dc, ys, majors = [], [], []
    for org in origins:
        nxt = org + pd.Timedelta(days=REFIT_STEP_DAYS)
        chunk = df[(df["date"] >= org) & (df["date"] < nxt)]
        if len(chunk) == 0:
            continue
        model = fit_dixon_coles(df, org, maxiter=300)
        for _, m in chunk.iterrows():
            P_dc.append(dc_predict_1x2(model, m["home_team"], m["away_team"], m["neutral"]))
            ys.append(int(m["outcome"]))
            majors.append(bool(m["is_major"]))
        print(f"  DC backtest origin {org.date()} -> +{len(chunk)} (cum {len(ys)})", file=sys.stderr)
    return np.array(P_dc), np.array(ys), np.array(majors)


def metric_dict(P, y):
    return {
        "rps": round(float(np.mean(rps_mat(P, y))), 5),
        "brier": round(float(np.mean(brier_mat(P, y))), 5),
        "logloss": round(float(np.mean(logloss_mat(P, y))), 5),
        "acc": round(float(np.mean(np.argmax(P, axis=1) == y)), 5),
        "ece": round(ece_homewin(P, y), 5),
        "n": int(len(y)),
    }


# ============================ MAIN ==========================================
def main():
    t0 = time.time()
    df = load()
    print(f"loaded {len(df)} matches {df.date.min().date()}..{df.date.max().date()}", file=sys.stderr)

    # ---------- FINAL shipped Dixon-Coles fit on ALL history ----------
    snapshot_date = df.date.max()
    ref = snapshot_date + pd.Timedelta(days=1)   # include the very last match
    dc_final = fit_dixon_coles(df, ref, maxiter=600)
    print(f"DC final: mu={dc_final['mu']:.4f} gamma={dc_final['gamma']:.4f} "
          f"rho={dc_final['rho']:.4f} teams={len(dc_final['atk'])}", file=sys.stderr)

    # ---------- Elo replay on ALL history + ordered-logit on calibration era ----------
    diffs, elo_final = elo_replay(df)
    df["_elo_diff"] = diffs
    cal = df[(df.date >= CAL_START) & (df.date < TEST_START)]
    s_hat, tau_hat = fit_ordered_logit(cal["_elo_diff"].to_numpy(), cal["outcome"].to_numpy())
    print(f"Elo: {len(elo_final)} teams; ordered-logit s={s_hat:.2f} tau={tau_hat:.4f}", file=sys.stderr)

    # ---------- No-leakage walk-forward backtest (shipped DC core) ----------
    print("running no-leakage walk-forward DC backtest...", file=sys.stderr)
    P, y, maj = walk_forward_backtest(df)
    overall = metric_dict(P, y)
    major = metric_dict(P[maj], y[maj]) if maj.sum() > 30 else {"n": int(maj.sum()), "note": "too few"}

    # climatology baseline (H/D/A base rate from 20y before test, scored on same outcomes)
    pre = df[(df.date < TEST_START) & (df.date >= TEST_START - pd.Timedelta(days=365 * 20))]
    base = np.array([(pre.outcome == 0).mean(), (pre.outcome == 1).mean(), (pre.outcome == 2).mean()])
    Pb = np.tile(base, (len(y), 1))
    base_rps = round(float(np.mean(rps_mat(Pb, y))), 5)
    print(f"backtest overall RPS={overall['rps']} major RPS={major.get('rps')} "
          f"acc={overall['acc']} ece={overall['ece']} n={overall['n']} | clim RPS={base_rps}",
          file=sys.stderr)

    # ---------- build keyed rating tables with aliases ----------
    # DC: shrink-to-mean (atk=def=0, i.e. the league-average team) for missing/sparse.
    # Count games per team to flag data-sparse (< 5 games) -> shrink as well.
    gc = pd.concat([df["home_team"], df["away_team"]]).value_counts()

    def build_dc_teams():
        teams = {}
        for name in dc_final["atk"]:
            teams[norm_key(name)] = {
                "atk": round(float(dc_final["atk"][name]), 4),
                "def": round(float(dc_final["dfn"][name]), 4),
                "name": name,
            }
        return teams

    def build_elo_ratings():
        ratings = {}
        for name, r in elo_final.items():
            ratings[norm_key(name)] = {"r": round(float(r), 1), "name": name}
        return ratings

    dc_teams = build_dc_teams()
    elo_ratings = build_elo_ratings()

    # add alias keys (point them at the canonical entry's data, copying so JS lookups by
    # the schedule-normalised key resolve directly)
    def apply_aliases(table):
        for ali, canon in ALIASES.items():
            if canon in table and ali not in table:
                table[ali] = dict(table[canon])

    apply_aliases(dc_teams)
    apply_aliases(elo_ratings)

    # ---------- WC2026 coverage verification ----------
    wc = json.load(open(WC2026_INDEX))["teams"]
    elo_mean = float(np.mean(list(elo_final.values())))
    shrunk = []
    missing_after = []
    for t in wc:
        name = t["name"]
        k = norm_key(name)
        k = ALIASES.get(k, k)  # follow alias to canonical if needed
        # DC coverage
        dc_present = k in dc_teams and gc.get(dc_teams[k]["name"], 0) >= 5
        elo_present = k in elo_ratings and gc.get(elo_ratings[k]["name"], 0) >= 5
        if not dc_present:
            dc_teams[norm_key(name)] = {"atk": 0.0, "def": 0.0, "name": name}
            shrunk.append((name, "dc"))
        if not elo_present:
            elo_ratings[norm_key(name)] = {"r": round(elo_mean, 1), "name": name}
            shrunk.append((name, "elo"))
        # final resolution check
        kk = norm_key(name)
        if kk not in dc_teams or kk not in elo_ratings:
            missing_after.append(name)

    shrunk_teams = sorted(set(n for n, _ in shrunk))

    # ---------- assemble ratings.json ----------
    out = {
        "snapshot_date": str(snapshot_date.date()),
        "dc": {
            "teams": dc_teams,
            "mu": round(dc_final["mu"], 4),
            "gamma": round(dc_final["gamma"], 4),
            "rho": round(dc_final["rho"], 4),
            "half_life_days": HALF_LIFE_DAYS,
            "friendly_weight": FRIENDLY_WEIGHT,
            "ridge": RIDGE,
            "max_goals": MAX_GOALS,
        },
        "elo": {
            "ratings": elo_ratings,
            "hfa_points": ELO_HFA,
            "divisor": ELO_DIVISOR,
            "s": round(s_hat, 4),
            "tau": round(tau_hat, 4),
        },
        "blend": {"w_model": 0.30},
        "backtest": {
            "rps": overall["rps"],
            "rps_major": major.get("rps"),
            "acc": overall["acc"],
            "n": overall["n"],
            "baseline_climatology_rps": base_rps,
            "ece": overall["ece"],
        },
        "_meta": {
            "generated_utc": datetime.utcnow().isoformat() + "Z",
            "fitter": "fit_ratings.py",
            "key_scheme": "lowercase, NFD accent-stripped, non-letters removed; aliases applied",
            "aliases": ALIASES,
            "wc2026_teams_total": len(wc),
            "wc2026_shrunk_or_missing": shrunk_teams,
            "backtest_major": major,
            "backtest_protocol": (
                f"no-leakage expanding-origin walk-forward, DC refit every {REFIT_STEP_DAYS}d "
                f"on data < origin; test era from {TEST_START.date()}; ordered-logit s,tau fit on "
                f"calibration era {CAL_START.date()}..{TEST_START.date()}"),
        },
    }

    for p in (OUT_LOCAL, OUT_SHIPPED):
        with open(p, "w") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"wrote {p} ({p.stat().st_size} bytes)", file=sys.stderr)

    # ---------- console summary ----------
    print("\n===== SUMMARY =====")
    print(f"snapshot_date            {out['snapshot_date']}")
    print(f"dc.teams count           {len(dc_teams)}")
    print(f"elo.ratings count        {len(elo_ratings)}")
    print(f"backtest.rps             {overall['rps']}")
    print(f"backtest.rps_major       {major.get('rps')}  (n={major.get('n')})")
    print(f"backtest.acc             {overall['acc']}")
    print(f"backtest.ece             {overall['ece']}")
    print(f"backtest.n               {overall['n']}")
    print(f"baseline_climatology_rps {base_rps}")
    print(f"WC2026 teams total       {len(wc)}")
    print(f"WC2026 shrunk/missing    {shrunk_teams if shrunk_teams else 'NONE — all 48 resolved from data'}")
    print(f"unresolved after fill    {missing_after if missing_after else 'NONE'}")
    print(f"ratings.json bytes       {OUT_SHIPPED.stat().st_size}")
    print(f"shipped path             {OUT_SHIPPED}")
    print(f"runtime                  {time.time() - t0:.0f}s")
    return out


if __name__ == "__main__":
    main()
