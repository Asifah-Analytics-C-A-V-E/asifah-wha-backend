# asifah-wha-backend

**Western Hemisphere theatre backend for [Asifah Analytics](https://asifahanalytics.com)**

Open-source monitoring of geopolitical pressure, conflict escalation and
humanitarian stress across the Western Hemisphere. Sister backends cover the
Middle East & North Africa, Europe & Eurasia, Asia & the Pacific, and Africa.

> **What this is.** A one-person project, built on nights and weekends, running
> on free tiers and stubbornness. No affiliation with or endorsement by any
> government or organisation. If it has been useful to you,
> ☕ [a coffee](https://buymeacoffee.com/asifahanalytics) pays for the hosting
> that keeps it up.

> 🚨 **Not for operational use.** Analytical and research purposes only. See
> [`LICENSE`](./LICENSE).

**Scale:** 33 modules, 51 registered routes.

---

## 🌎 Coverage

A **rhetoric tracker** is a purpose-built sensor with its own actor roster,
escalation ladder, red lines and interpreter. Only tracked countries reach the
regional BLUF and the Global Pressure Index.

| Country | Tracker | History / Summary | Other modules |
|---|---|---|---|
| 🇺🇸 United States | ✅ | debug only | **Resident hub.** Stability, government composition, economic indicators, Reddit signals |
| 🇻🇪 Venezuela | ✅ | ✅ | Financial pulse, humanitarian. First contract-native tracker (v2.5, May 2026) |
| 🇨🇺 Cuba | ✅ | ✅ | — |
| 🇨🇱 Chile | ✅ | debug only | — |
| 🇵🇪 Peru | ✅ | debug only | — |
| 🇲🇽 Mexico | — | — | Stability module only |

**Resident hub:** `us`. The United States wheel is assembled on this backend, so
its rim — which reaches well outside this theatre — is read everywhere else
through the shared Redis keyspace. The US tracker is the command-node anchor
(Jun 2026).

**Queued, with no sensor today:** 🇭🇹 Haiti, 🇵🇦 Panama, 🇨🇴 Colombia, 🇧🇷 Brazil.
Slots are reserved in `wha_regional_bluf.py`. Until a tracker ships, these
countries are **absent from the WHA read, not assessed as quiet** — earlier
revisions of this file listed all seven as covered, which was ambition rather
than coverage.

---

## 🏗 Architecture

- **Flask + gunicorn** on Render
- **Shared Upstash Redis** for cross-theatre fingerprints and per-tracker caches
- **Background refresh threads** — 4–6 hour cycles, `daemon=True`, 60–120s boot
  delay to stagger startup load
- **Redis-first caching** with a `/tmp` file fallback
- **Multi-source OSINT ingestion** — GDELT, NewsAPI, Brave Search, Google News
  RSS, Reddit, Telegram, Bluesky

### Modules

| Area | Files |
|---|---|
| Rhetoric trackers | `rhetoric_tracker_us.py`, `_venezuela`, `_cuba`, `_chile`, `_peru` |
| Interpreters | `us_signal_interpreter.py`, `venezuela_`, `cuba_`, `chile_`, `peru_` |
| Regional synthesis | `wha_regional_bluf.py` |
| US cluster | `us_stability.py`, `us_government_composition.py`, `economic_indicators_us.py`, `reddit_signals_us.py`, `elite_fracture.py`, `principal_cadence.py`, `patron_axis.py` |
| Country modules | `venezuela_financial_pulse.py`, `venezuela_humanitarian.py`, `mexico_stability.py` |
| Proxies to ME canon | `commodity_proxy_wha.py`, `butterfly_proxy_wha.py`, `jawboning_proxy_wha.py` |
| Ingestion | `gdelt_gateway.py`, `brave_gateway.py`, `telegram_signals_wha.py`, `bluesky_signals_wha.py` |
| Shared libraries | `spoke_wheel_reader.py`, `trajectory_reader.py`, `theatre_state.py`, `feed_health.py` |

**Shared libraries deploy byte-identical to every backend.** `spoke_wheel_reader.py`,
`trajectory_reader.py`, `theatre_state.py` and `gdelt_gateway.py` are library
code, not data. If you change one here, change it everywhere.

**Proxies front the ME backend's canonical registries.** Commodity, butterfly and
jawboning have exactly one producer, on the ME backend. WHA reads through a proxy
rather than keeping a second copy. One writer, many readers.

---

## 🚀 Deployment

Deploys to Render via GitHub auto-deploy.

### Render configuration

```
Language:        Python 3
Build Command:   pip install -r requirements.txt
Start Command:   gunicorn app:app --timeout 300 --workers 2
Health Check:    /health
```

> ⚠️ **CRITICAL:** the start command MUST include `--timeout 300 --workers 2`.
> Render's default 30-second timeout is shorter than a full scan cycle, and this
> is the single most common deploy bug across Asifah backends.

### Environment variables

| Variable | Purpose |
|---|---|
| `UPSTASH_REDIS_URL` / `UPSTASH_REDIS_REST_URL` | Upstash Redis REST endpoint |
| `UPSTASH_REDIS_TOKEN` / `UPSTASH_REDIS_REST_TOKEN` | Upstash Redis REST bearer token |
| `NEWSAPI_KEY` | NewsAPI.org |
| `BRAVE_API_KEY`, `BRAVE_DAILY_BUDGET` | Brave Search + daily call budget |
| `ALPHA_VANTAGE_KEY`, `FRED_API_KEY` | Market and macro data for the US and Venezuela modules |
| `CONGRESS_API_KEY` | US government composition |
| `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` / `TELEGRAM_PHONE` | Telegram MTProto |
| `DEBUG_TOKEN` | Gates the `/debug` endpoints |
| `PYTHONUNBUFFERED` | Set to `1` — forces stdout flush for Render Live Tail visibility |

**Optional:** `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`. `reddit_signals_us.py`
uses OAuth when both are set (60 requests/min) and falls back to anonymous public
endpoints when they are not (10 requests/min). The platform currently runs
anonymous — these are a capacity upgrade, not a dependency.

Tuning: `FEED_HEALTH_TTL_SEC`, `FEED_SILENT_DAYS`, `FEED_DEAD_DAYS`.

### Manual redeploy

Auto-deploy is enabled, but the canonical practice is to confirm each deploy
manually in the Render dashboard so the deploy log can be read before scans run.

> On a 404 after deploy, read the **startup sequence** in the log, not the tail.
> An import error prints its traceback at boot and has usually scrolled away by
> the time you look.

---

## 📡 Endpoints

51 routes are registered; full inventory via the route map in `app.py`. The ones
used most:

| Endpoint | Purpose |
|---|---|
| `/api/rhetoric/<country>` | Country tracker — us, venezuela, cuba, chile, peru |
| `/api/rhetoric/<country>/history` · `/summary` | **Venezuela and Cuba only.** US, Chile and Peru expose `/debug` instead |
| `/api/rhetoric/venezuela/refresh` | Venezuela-specific rescan |
| `/api/rhetoric/wha/bluf` | Regional BLUF — `?force=true` rebuilds |
| `/api/rhetoric/wha/bluf/debug` | Cache state and per-tracker inventory |
| `/api/wha/stability/<country_id>` · `/api/wha/threat/<country_id>` | Stability score and threat probability |
| `/api/wha/countries` | Supported country slugs |
| `/api/us-stability` · `/history` · `/dimension/<dim_id>` · `/nyse` | US stability, by dimension |
| `/api/us-government-composition` · `/api/economic-indicators-us` | US government and macro reads |
| `/api/venezuela/financial-pulse` · `/api/venezuela/humanitarian` | Venezuela modules |
| `/api/mexico/stability` | Mexico stability |
| `/api/wha/commodity/<target>` · `/api/wha/commodity-fingerprint/<country>` | Commodity proxy |
| `/api/wha/butterfly/<consumer_theater>` | Butterfly (second-order effect) read |
| `/api/wha/jawboning/detect` · `/api/wha/absorption-signatures` | Jawboning and absorption reads |
| `/api/wha/leader-interventions` · `/<country>` · `/commodity/<commodity>` | Leader intervention signals |
| `/api/military-posture/<target>` · `/api/wha/travel-advisories` | Military posture, official travel advisories |
| `/health` | Health check |

`?force=true` bypasses the cache and runs a live scan.

> ⚠️ `?force=true` on a cold service can exceed a five-minute client timeout.
> Prefer the cached read unless a rebuild is genuinely needed.

> Earlier revisions of this file documented `/api/rhetoric/wha/<country>`. That
> route does not exist — country trackers are `/api/rhetoric/<country>`, and
> `/api/rhetoric/wha/bluf` is the regional synthesis.

---

## 🤝 Cross-backend integration

Three altitudes: sensors below, analyst in the middle, global index above.

```
Rhetoric trackers (US, Venezuela, Cuba, Chile, Peru)
              │
              ▼
    wha_regional_bluf.py  ─────►  Global Pressure Index (GPI)
              ▲                              ▲
              │                              │
   commodity / butterfly / jawboning proxies │
              ▲                              │
              │                              │
        ME backend's canonical registries ───┘
```

**The US wheel is assembled here**, so spokes that sit in other theatres are read
against a hub resident on this backend, through shared Redis rather than
cross-backend HTTP.

### Sister services

| Service | URL |
|---|---|
| ME / canonical layer | `asifah-backend.onrender.com` |
| Europe & Eurasia | `asifa-europe-backend.onrender.com` ⚠️ **no `h`** |
| Asia & Pacific | `asifah-asia-backend.onrender.com` |
| Africa | `asifah-africa-backend.onrender.com` |
| WHA | `asifah-wha-backend.onrender.com` (this service) |

> ⚠️ The Europe **repo** is `asifah-europe-backend`; the deployed **service** is
> `asifa-europe-backend`, without the `h`. Earlier revisions of this file listed
> the repo spelling as the service URL, which does not resolve.

---

## 📋 Working practices

**Doctrine.** Every module here follows the platform-wide analytical discipline:

- **Convergence, not prediction.** Report the signals that are present. Never
  assert that an outcome is imminent, likely, or dated.
- **`unknown` is a state, never a silence.** A sensor that could not read
  something says so. It does not emit a zero.
- **A real zero is not an unread zero.** "Measured, found nothing" and "nobody
  measured" are different findings and render differently.
- **Absence is reported, not inferred.** A country without a tracker is absent
  from the regional read, not assessed as quiet.
- **Silence can be the signal.** For claiming actors, quiet against their own
  baseline is a tempo change, not calm.
- **Claims are labelled as claims.** Where a reading rests on an interested
  party's unconfirmed assertions, it is reported as claimed, not established.
- **One writer, many readers.** Data has exactly one producer; everything else
  proxies to it.

**Engineering.**

- Surgical find/replace edits preferred over full-file rewrites
- AST validation before every deploy is mandatory:
  `python3 -c "import ast; ast.parse(open('FILE.py').read()); print('ok')"`
- Static reference data carries `source`, source URL and a `data_as_of` date —
  date-stamp rather than hardcode, so staleness is visible rather than assumed
- A diagnostic that lies is worse than no diagnostic. A health check that cannot
  fail is not a health check.

---

## 📞 Contact

Built and maintained independently by RCGG in personal time. Licensing: see
[`LICENSE`](./LICENSE).

- ☕ [Buy Me a Coffee](https://buymeacoffee.com/asifahanalytics) — pays for hosting
- [asifahanalytics.com](https://asifahanalytics.com) · *Not for operational use*

Donations support running costs. They buy no licence, no warranty, no support
obligation and no influence over what gets built.

---

*© 2025–2026 RCGG / Asifah Analytics. All rights reserved.*

*Last updated: 5 October 2026*
