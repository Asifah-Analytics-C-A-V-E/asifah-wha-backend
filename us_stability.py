"""
Asifah Analytics — U.S. Stability Index v1.0.0
May 11, 2026

THE SCORING ENGINE for the U.S. Stability page. This is sister-module to
china_stability.py, russia_stability.py, lebanon_stability.py, but with
U.S.-specific dimensions reflecting the structural distinctness of
American government.

ANALYTICAL FRAME — APOLITICAL BY DESIGN:
The same scoring rubric applies regardless of which administration is in
power. Specific events that score the same severity:

  • 1973 Saturday Night Massacre (Nixon firing Cox/Richardson) →
    Democratic Institutions stress
  • 2021 January 6 → Civil/Social + Political Cohesion stress
  • 2024 Trump indictments (Biden-era DOJ) → Democratic Institutions stress
  • 2025 cabinet turnover (Trump 2nd term) → Political Cohesion stress
  • Hypothetical Dem unilateral debt cancellation against court order →
    Democratic Institutions stress

Keyword sets are STRUCTURAL-PATTERN based, not party-coded. Same code
runs in 2026 (unified GOP) or hypothetical 2027 (divided govt).

SIX SCORING DIMENSIONS:

  1. Economic Stability         (20%) — economic_indicators_us module
  2. Political Cohesion         (15%) — cabinet/agency churn, deadlock
  3. Civil / Social             (15%) — mass casualty, protest activity
  4. Democratic Institutions    (20%) — court orders, IGs, electoral
  5. Military Posture           (15%) — military:us:posture fingerprint
  6. Cyber / Infrastructure     (15%) — cyber events, infra failures

COMPOSITE STABILITY INDEX (0-100, higher = more stress):
  0-29   🟢  RESILIENT             — strong functional state
  30-49  🟡  STRESSED               — multiple signals elevated
  50-69  🟠  FRACTURED              — convergent stress
  70-89  🔴  CRISIS MODE            — major institutional pressure
  90-100 🔴  CONSTITUTIONAL CRISIS  — load-bearing institutions failing

Apolitical, structural — not rhetoric-delta-based (unlike older trackers).
This means scores are directly comparable across time periods and
administrations.

ELECTION-CYCLE AWARENESS:
The composite score is multiplied by election_cycle.stability_modifier
(1.0 to 1.6) to reflect that certain phases (lame duck, election week,
late campaign) amplify political stress signals' relevance.

CROSS-TRACKER WRITES (for Global Pressure Index consumption):
  - stability:us:fingerprint   (12h TTL, full payload)
  - stability:us:summary       (12h TTL, compressed for GPI)

REDIS KEYS:
  Cache:           us:stability:latest
  History:         us:stability:history    (30 days, daily snapshots)
  Fingerprint:     stability:us:fingerprint
  Cross-theater:   military:us:posture     (READ — from mil tracker)

ENDPOINTS:
  GET /api/us-stability                 — full payload
  GET /api/us-stability/debug           — diagnostics
  GET /api/us-stability/dimension/<id>  — single dimension detail
  GET /api/us-stability/history         — 30-day trendline data

COPYRIGHT (c) 2025-2026 Asifah Analytics. All rights reserved.
"""

import os
import json
import time
import threading
import requests
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# curl_cffi: TLS/JA3 fingerprint impersonation for sites that detect requests-library
# at the network layer (Cloudflare bot detection). v1.5.0 (May 29 2026).
# Falls back gracefully if not installed — we capture the import error.
try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    curl_requests = None
    CURL_CFFI_AVAILABLE = False
    print("[US Stability] WARNING: curl_cffi not installed — TLS impersonation unavailable")

# ════════════════════════════════════════════════════════════
# SOCIAL SIGNAL COLLECTORS (v1.1.0 — May 2026)
# ════════════════════════════════════════════════════════════
# Three external modules feed social-media signal into the article pool
# alongside RSS / GDELT / NewsAPI. Each module is wrapped in try/except so
# the scan keeps working if any single module is missing or broken.
#
#   Bluesky:  76 accounts (post-audit scrubbed v1.2.0) — no auth
#   Telegram: 33 channels  (Israeli, UK, AJ, breaking news) — requires API keys
#   Reddit:   25 subs (post-audit scrubbed v1.2.0, OAuth-ready) — optional auth
# ════════════════════════════════════════════════════════════
try:
    from bluesky_signals_wha import fetch_bluesky_for_target
    BLUESKY_US_AVAILABLE = True
    print("[US Stability] Bluesky US signals module loaded")
except ImportError as e:
    BLUESKY_US_AVAILABLE = False
    print(f"[US Stability] WARNING: Bluesky unavailable ({e})")

try:
    from telegram_signals_wha import fetch_telegram_signals_us
    TELEGRAM_US_AVAILABLE = True
    print("[US Stability] Telegram US signals module loaded")
except ImportError as e:
    TELEGRAM_US_AVAILABLE = False
    print(f"[US Stability] WARNING: Telegram unavailable ({e})")

try:
    from reddit_signals_us import fetch_reddit_signals_us
    REDDIT_US_AVAILABLE = True
    print("[US Stability] Reddit US signals module loaded")
except ImportError as e:
    REDDIT_US_AVAILABLE = False
    print(f"[US Stability] WARNING: Reddit unavailable ({e})")


# ============================================================
# CONFIGURATION
# ============================================================

print("[US Stability] Module loading...")

UPSTASH_REDIS_URL = (os.environ.get('UPSTASH_REDIS_URL') or
                     os.environ.get('UPSTASH_REDIS_REST_URL'))
UPSTASH_REDIS_TOKEN = (os.environ.get('UPSTASH_REDIS_TOKEN') or
                       os.environ.get('UPSTASH_REDIS_REST_TOKEN'))
NEWSAPI_KEY = os.environ.get('NEWSAPI_KEY')
BRAVE_API_KEY = os.environ.get('BRAVE_API_KEY')
ALPHA_VANTAGE_KEY = os.environ.get('ALPHA_VANTAGE_KEY')

# Cache keys
CACHE_KEY        = 'us:stability:latest'
HISTORY_KEY      = 'us:stability:history'
FINGERPRINT_KEY  = 'stability:us:fingerprint'
SUMMARY_KEY      = 'stability:us:summary'

# NYSE / US Equity Indices (v1.0.0 — May 27 2026)
# Cache-first architecture: twice-daily fetches (7am + 7pm ET), Alpha Vantage
# primary + Yahoo fallback. Sparklines update on EOD pull only.
NYSE_CACHE_KEY   = 'us:nyse:latest'
NYSE_TTL_SECONDS = 14 * 3600   # 14h (covers gap between 7am/7pm fetches with buffer)
NYSE_INDICES = [
    {'key': 'SPX',  'name': 'S&P 500',          'av_symbol': 'SPX',   'yahoo_symbol': '^GSPC'},
    {'key': 'DJIA', 'name': 'Dow Jones',        'av_symbol': '.DJI',  'yahoo_symbol': '^DJI'},
    {'key': 'IXIC', 'name': 'NASDAQ Composite', 'av_symbol': 'IXIC',  'yahoo_symbol': '^IXIC'},
]

CACHE_TTL_SECONDS  = 12 * 3600    # 12h
HISTORY_DAYS       = 30            # 30 daily snapshots
SCAN_INTERVAL_HOURS = 12

# Background scan management
_scan_lock = threading.Lock()
_scan_running = False

DEFAULT_TIMEOUT = 12

print("[US Stability] Configuration loaded.")


# ============================================================
# IMPORT DEPENDENCIES (graceful degradation if missing)
# ============================================================

try:
    from economic_indicators_us import fetch_economic_indicators
    ECON_AVAILABLE = True
    print("[US Stability] ✅ economic_indicators_us imported")
except ImportError:
    ECON_AVAILABLE = False
    print("[US Stability] ⚠️  economic_indicators_us not available — Dimension 1 will fail")

try:
    from us_government_composition import get_government_composition
    GOVT_AVAILABLE = True
    print("[US Stability] ✅ us_government_composition imported")
except ImportError:
    GOVT_AVAILABLE = False
    print("[US Stability] ⚠️  us_government_composition not available — using default baselines")


# ============================================================
# STABILITY BANDS (canonical 5-band system)
# ============================================================

STABILITY_BANDS = [
    {'min':  0, 'max': 29,  'band': 'resilient',           'label': 'Resilient',
     'icon': '🟢', 'color': '#10b981',
     'description': 'Strong functional state across all dimensions.'},
    {'min': 30, 'max': 49,  'band': 'stressed',            'label': 'Stressed',
     'icon': '🟡', 'color': '#f59e0b',
     'description': 'Multiple signals elevated; institutional capacity intact.'},
    {'min': 50, 'max': 69,  'band': 'fractured',           'label': 'Fractured',
     'icon': '🟠', 'color': '#f97316',
     'description': 'Convergent stress across dimensions; some institutional friction.'},
    {'min': 70, 'max': 89,  'band': 'crisis_mode',         'label': 'Crisis Mode',
     'icon': '🔴', 'color': '#ef4444',
     'description': 'Major institutional pressure; multiple load-bearing systems strained.'},
    {'min': 90, 'max': 100, 'band': 'constitutional_crisis', 'label': 'Constitutional Crisis',
     'icon': '🔴', 'color': '#991b1b',
     'description': 'Load-bearing institutions failing or in active conflict.'},
]


def score_to_band(score):
    """Given a 0-100 score, return matching band dict."""
    for b in STABILITY_BANDS:
        if b['min'] <= score <= b['max']:
            return b
    # Fallback (e.g., negative or >100)
    if score < 0:
        return STABILITY_BANDS[0]
    return STABILITY_BANDS[-1]


# ============================================================
# DIMENSION WEIGHTS (must sum to 1.0)
# ============================================================

DIMENSION_WEIGHTS = {
    'economic':                0.20,
    'political_cohesion':      0.15,
    'civil_social':            0.15,
    'democratic_institutions': 0.20,
    'military_posture':        0.15,
    'cyber_infrastructure':    0.15,
}

# Sanity check
assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 0.001, \
    "Dimension weights must sum to 1.0"


# ============================================================
# DIMENSION 1 — ECONOMIC STABILITY THRESHOLDS
# ============================================================
# Threshold tables: maps indicator value to 0-100 stress score
# (Higher value on indicator → higher stress score, EXCEPT for "good_direction"
# indicators where higher = better)
# ============================================================

ECON_THRESHOLDS = {
    'cpi_yoy': {
        'unit':  '%',
        'good_direction': 'down',
        'thresholds': [
            (0,    2.5,   10),   # below 2.5% YoY: very mild
            (2.5,  4.0,   30),   # 2.5-4%: stressed
            (4.0,  6.0,   55),   # 4-6%: fractured
            (6.0,  9.0,   75),   # 6-9%: crisis
            (9.0,  100,   95),   # >9%: constitutional-economic crisis
        ],
    },
    'unemployment': {
        'unit':  '%',
        'good_direction': 'down',
        'thresholds': [
            (0,    4.0,   10),
            (4.0,  5.5,   30),
            (5.5,  7.0,   55),
            (7.0,  9.0,   75),
            (9.0,  100,   95),
        ],
    },
    'mortgage_30yr': {
        'unit':  '%',
        'good_direction': 'down',
        'thresholds': [
            (0,    5.5,   15),
            (5.5,  7.0,   35),
            (7.0,  8.5,   55),
            (8.5,  10.0,  75),
            (10.0, 100,   90),
        ],
    },
    'gas_price': {
        'unit':  '$/gal',
        'good_direction': 'down',
        'thresholds': [
            (0,    3.25,  15),
            (3.25, 4.00,  35),
            (4.00, 5.00,  55),
            (5.00, 6.00,  75),
            (6.00, 100,   90),
        ],
    },
    'treasury_10y': {
        'unit':  '%',
        'good_direction': 'down',
        'thresholds': [
            (0,    4.0,   15),
            (4.0,  5.0,   35),
            (5.0,  6.0,   55),
            (6.0,  7.0,   75),
            (7.0,  100,   90),
        ],
    },
    'jobless_claims': {
        'unit':  'count',
        'good_direction': 'down',
        'thresholds': [
            (0,      230000,   15),
            (230000, 275000,   35),
            (275000, 350000,   55),
            (350000, 450000,   75),
            (450000, 1000000,  90),
        ],
    },
    'fed_funds': {
        'unit':  '%',
        'good_direction': None,    # context-dependent
        'thresholds': [
            (0,    1.0,   25),    # near-zero rates can signal crisis-response
            (1.0,  3.0,   15),    # normal range
            (3.0,  5.0,   25),
            (5.0,  7.0,   45),
            (7.0,  100,   70),
        ],
    },
    'deficit_gdp': {
        'unit':  '%',
        'good_direction': 'up',    # closer to 0 (or surplus) is better
        'thresholds': [
            (-3,   100,   15),    # surplus or deficit < 3%
            (-5,   -3,    30),    # 3-5% deficit
            (-7,   -5,    50),    # 5-7% deficit
            (-10,  -7,    70),    # 7-10% deficit
            (-100, -10,   90),    # >10% deficit
        ],
    },
    # Equity indices and BTC don't have stability thresholds in same way —
    # we skip them in the scoring (they're informational, not stress-mapped)
}


def score_economic_indicator(indicator_id, value):
    """Map an indicator value to a 0-100 stress score using threshold table."""
    if value is None or indicator_id not in ECON_THRESHOLDS:
        return None
    cfg = ECON_THRESHOLDS[indicator_id]
    for low, high, score in cfg['thresholds']:
        if low <= value < high:
            return score
    # Off-table — return highest band score
    return cfg['thresholds'][-1][2]


# ============================================================
# DIMENSION 2-4, 6 — KEYWORD SIGNAL DETECTION SETS
# ============================================================
# APOLITICAL keyword sets — detect structural stress patterns
# regardless of which party is involved.
# ============================================================

POLITICAL_COHESION_KEYWORDS = {
    # Cabinet/Agency Churn (modified by cabinet_turnover_weight from baseline)
    'cabinet_churn': {
        'patterns': [
            'cabinet shakeup', 'cabinet reshuffle', 'cabinet resign',
            'secretary resigns', 'secretary fired', 'secretary stepped down',
            'fired the head of', 'fired the director of', 'removed the director',
            'forced out as', 'ousted as', 'pushed out of',
            'acting secretary', 'interim director', 'interim secretary',
            'leadership vacancy', 'agency leadership vacant',
            'nominee withdrawn', 'withdraws from consideration',
            'rejected by senate', 'failed to confirm',
        ],
        'base_weight': 8,
        'baseline_modifier_key': 'cabinet_turnover_weight',
    },
    # Legislative Deadlock
    'legislative_deadlock': {
        'patterns': [
            'shutdown looms', 'government shutdown', 'continuing resolution',
            'fiscal cliff', 'debt ceiling crisis', 'debt limit fight',
            'filibuster', 'stalemate in', 'no path forward',
            'fiscal impasse', 'budget impasse',
            'failed to pass', 'rejected the bill',
            'cloture vote failed',
        ],
        'base_weight': 6,
        'baseline_modifier_key': 'partisan_deadlock_weight',
    },
    # Inter-branch Friction
    'inter_branch_friction': {
        'patterns': [
            'veto override', 'congressional subpoena', 'subpoena defied',
            'stonewall congress', 'refused to comply with subpoena',
            'speaker challenge', 'motion to vacate',
            'lawmaker indicted', 'congressman indicted', 'senator indicted',
            'ethics violation', 'censure resolution',
            'expelled from congress',
        ],
        'base_weight': 7,
        'baseline_modifier_key': None,
    },
}

CIVIL_SOCIAL_KEYWORDS = {
    # Mass Casualty Events (heaviest weight)
    'mass_casualty': {
        'patterns': [
            'mass shooting', 'active shooter', 'active shooter incident',
            'school shooting', 'workplace shooting', 'church shooting',
            'shooting at', 'gunman opened fire',
            'casualties reported', 'multiple casualties',
            'mass casualty incident',
        ],
        'base_weight': 12,
        'baseline_modifier_key': None,
    },
    # Protest Activity (apolitical — tracked by name+size+frequency)
    'protest_activity': {
        'patterns': [
            'thousands gathered', 'thousands protest', 'tens of thousands',
            'protests in', 'rally drew', 'march on', 'demonstration in',
            'no kings movement', 'no kings rally', 'no kings protest',
            'black lives matter', 'blm rally', 'blm protest',
            'tea party rally', 'tea party movement',
            'march for life', 'pride rally', 'pride march',
            'climate march', 'climate strike',
            'standing protest', 'occupation of',
        ],
        'base_weight': 4,
        'baseline_modifier_key': None,
    },
    # Civil Unrest
    'civil_unrest': {
        'patterns': [
            'riots in', 'riots erupted', 'looting reported',
            'curfew imposed', 'curfew declared',
            'national guard deployed', 'national guard activated',
            'state of emergency declared',
            'martial law',
            'tear gas deployed', 'rubber bullets fired',
        ],
        'base_weight': 10,
        'baseline_modifier_key': None,
    },
    # Severe Weather (climate stability proxy)
    'severe_weather': {
        'patterns': [
            'hurricane warning', 'hurricane landfall', 'category 4 hurricane', 'category 5 hurricane',
            'wildfire evacuation', 'wildfire grew to', 'wildfires destroy',
            'extreme heat', 'heat dome', 'heat advisory',
            'polar vortex', 'arctic blast',
            'flooding emergency', 'flash flood emergency',
            'drought emergency', 'tornado outbreak',
        ],
        'base_weight': 5,
        'baseline_modifier_key': None,
    },
}

DEMOCRATIC_INSTITUTIONS_KEYWORDS = {
    # Court Order Compliance (modified by court_orders_defied_weight)
    'court_order_compliance': {
        'patterns': [
            'court order defied', 'ignored court ruling', 'in contempt of court',
            'judge held in contempt', 'contempt of court',
            'stay denied', 'court issued', 'judge ruled', 'ruling against',
            'temporary restraining order', 'preliminary injunction',
            'supreme court ruled', 'scotus ruled', 'court enjoined',
            'judicial review',
        ],
        'base_weight': 9,
        'baseline_modifier_key': 'court_orders_defied_weight',
    },
    # Inspector General / Oversight Integrity
    'oversight_integrity': {
        'patterns': [
            'inspector general fired', 'removed ig', 'ig dismissed',
            'inspector general dismissed', 'watchdog removed', 'oversight removed',
            'career official replaced', 'career civil service',
            'whistleblower', 'whistleblower retaliation',
            'gao report', 'congressional watchdog',
        ],
        'base_weight': 8,
        'baseline_modifier_key': 'inspector_general_dismissal',
    },
    # Civil Service Erosion
    'civil_service_erosion': {
        'patterns': [
            'schedule f', 'schedule f executive order',
            'civil service reform', 'merit system', 'career civil service fired',
            'agency career staff', 'loyalty test', 'political appointee',
            'mass firings', 'mass termination',
            'reduction in force',
        ],
        'base_weight': 8,
        'baseline_modifier_key': 'civil_service_purge_weight',
    },
    # Electoral Integrity Signals
    'electoral_integrity': {
        'patterns': [
            'election certification', 'certification disputed', 'certification challenged',
            'secretary of state challenged', 'state election official',
            'electoral college dispute', 'faithless elector',
            'ballot challenges', 'ballot rejected', 'voter suppression',
            'voting machines compromised', 'election fraud allegation',
            'election integrity', 'election denialism',
            'gerrymandering ruling', 'redistricting ruling',
        ],
        'base_weight': 9,
        'baseline_modifier_key': None,
    },
    # DOJ Independence Signals (works in both directions)
    'doj_independence': {
        'patterns': [
            'doj politicized', 'political prosecution', 'selective prosecution',
            'attorney general ordered', 'ag ordered to', 'ag fired',
            'white house pressured doj', 'white house pressured prosecutors',
            'special counsel removed', 'special counsel fired',
            'doj reorganization', 'us attorney fired', 'us attorneys removed',
            'pardon controversy', 'preemptive pardon',
        ],
        'base_weight': 9,
        'baseline_modifier_key': None,
    },
}

CYBER_INFRA_KEYWORDS = {
    # Cyber Events
    'cyber_events': {
        'patterns': [
            'ransomware attack', 'ransomware on',
            'data breach', 'data breach exposed',
            'cyberattack on', 'cyber attack on',
            'critical infrastructure attack', 'pipeline hack',
            'election system breach', 'voter data breach',
            'state-sponsored hack', 'apt group',
            'cisa warning', 'cisa alert',
        ],
        'base_weight': 8,
        'baseline_modifier_key': None,
    },
    # Infrastructure Failures
    'infrastructure_failures': {
        'patterns': [
            'power grid failure', 'power outage', 'rolling blackouts',
            'mass power outage', 'electricity grid failure',
            'bridge collapse', 'road collapse',
            'infrastructure failure',
            'water system contamination', 'water crisis',
            'water main break', 'sewer system failure',
            'natural gas explosion', 'pipeline rupture',
        ],
        'base_weight': 7,
        'baseline_modifier_key': None,
    },
    # Tech / Network Stability
    'tech_failures': {
        'patterns': [
            'air traffic outage', 'faa system failure', 'faa ground stop',
            '911 system down', 'emergency services outage',
            'banking system outage', 'payment system failure',
            'major outage at',
        ],
        'base_weight': 6,
        'baseline_modifier_key': None,
    },
}


# ============================================================
# RSS / GDELT / NEWSAPI SIGNAL FETCHERS
# ============================================================

# RSS feeds — focused on US domestic stability (v1.2.0 May 10 2026 audit)
#
# AUDIT NOTES: First production deploy logged the following failures:
#   Reuters US: connection refused (Reuters killed RSS in 2024)
#   AP US:      HTTP 401  -- index.rss URL deprecated
#   Politico:   HTTP 403  -- bot UA blocked
#   Just Security: HTTP 403 -- bot UA blocked
#   Lawfare:    HTTP 403  -- bot UA blocked (URL itself OK, UA issue)
#   FEMA News:  HTTP 403  -- bot UA blocked
#   Univision:  invalid XML (URL changed)
#   Telemundo:  HTTP 404  -- URL dead
#
# FIX STRATEGY:
#   1. Drop Reuters (killed RSS), Univision/Telemundo (URLs dead)
#   2. Use browser User-Agent in _fetch_rss to bypass bot blocks
#   3. Replace dead URLs with current working ones
#   4. Add known-good US news RSS feeds (PBS NewsHour, ProPublica, Atlantic)
US_STABILITY_RSS = [
    # ── Tier 1: Known working from production logs ──
    ('NPR National',     'https://feeds.npr.org/1003/rss.xml'),
    ('NYT US',           'https://rss.nytimes.com/services/xml/rss/nyt/US.xml'),
    ('NYT Politics',     'https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml'),
    ('The Hill',         'https://thehill.com/news/feed/'),
    ('CNN Politics',     'http://rss.cnn.com/rss/cnn_allpolitics.rss'),

    # ── Tier 2: Worked in audit when given browser UA (need UA fix in _fetch_rss) ──
    ('Politico',         'https://www.politico.com/rss/politicopicks.xml'),
    ('Just Security',    'https://www.justsecurity.org/feed/'),
    # Lawfare: swapped to Substack mirror May 29 2026 — main site
    # lawfaremedia.org/feed.xml was 403-blocking even with curl_cffi TLS impersonation.
    # Substack feed is publicly designed for syndication and has different network path.
    ('Lawfare',          'https://lawfare.substack.com/feed'),
    ('FEMA News',        'https://www.fema.gov/about/news-multimedia/rss'),
    ('Axios',            'https://api.axios.com/feed/'),
    # AP US removed May 27 2026 — feeds.apnews.com host no longer resolving.
    # Replacement: ABC News + USA Today politics feeds.

    # ── Tier 3: NEW additions May 2026 — high-quality US news with stable feeds ──
    ('PBS NewsHour',     'https://www.pbs.org/newshour/feeds/rss/headlines'),
    ('ProPublica',       'https://www.propublica.org/feeds/propublica/main'),
    ('Atlantic Politics','https://www.theatlantic.com/feed/channel/politics/'),
    ('WaPo Politics',    'https://feeds.washingtonpost.com/rss/politics'),
    # Reuters US (alt) removed May 27 2026 — 404'd consistently.

    # ── Tier 4: NEW May 27 2026 replacements for dead AP/Reuters feeds ──
    ('ABC News Politics','https://abcnews.go.com/abcnews/politicsheadlines'),
    ('USA Today Politics','https://rssfeeds.usatoday.com/UsatodaycomWashington-TopStories'),
    ('Reuters Top News (rss.app proxy)','https://rss.app/feeds/V8FCFmJyjQX4FmCx.xml'),
    ('Guardian US',      'https://www.theguardian.com/us-news/rss'),
    ('BBC US & Canada',  'https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml'),

    # ── Tier 5: Substack feeds (May 29 2026) — bot-detection-resistant by design ──
    # Substack RSS endpoints are designed for syndication and don't share the same
    # Cloudflare bot detection profile as main news sites. High-quality analytical
    # voices for U.S. economic/political stability tracking.
    ('Punchbowl News',   'https://punchbowl.news/feed/'),
    ('Adam Tooze Chartbook','https://adamtooze.substack.com/feed'),

    # ── Cybersecurity / infrastructure ──
    ('CISA Alerts',      'https://www.cisa.gov/news.xml'),
    ('CISA Advisories',  'https://www.cisa.gov/cybersecurity-advisories/all.xml'),

    # ── Removed (no working alternative as of May 27 2026): ──
    # Reuters US (feeds.reuters.com killed Dec 2024)
    # Reuters US (alt) (reutersagency.com 404'd consistently in production)
    # AP US (feeds.apnews.com — host no longer resolving as of May 27 2026)
    # Univision / Telemundo (feeds dead)
    # Spanish-language US-focused signal now flows via GDELT Spanish queries + Brave fallback
]

# 50 US states — for state-level signal aggregation
US_STATES = {
    'AL': 'Alabama',         'AK': 'Alaska',          'AZ': 'Arizona',
    'AR': 'Arkansas',        'CA': 'California',      'CO': 'Colorado',
    'CT': 'Connecticut',     'DE': 'Delaware',        'FL': 'Florida',
    'GA': 'Georgia',         'HI': 'Hawaii',          'ID': 'Idaho',
    'IL': 'Illinois',        'IN': 'Indiana',         'IA': 'Iowa',
    'KS': 'Kansas',          'KY': 'Kentucky',        'LA': 'Louisiana',
    'ME': 'Maine',           'MD': 'Maryland',        'MA': 'Massachusetts',
    'MI': 'Michigan',        'MN': 'Minnesota',       'MS': 'Mississippi',
    'MO': 'Missouri',        'MT': 'Montana',         'NE': 'Nebraska',
    'NV': 'Nevada',          'NH': 'New Hampshire',   'NJ': 'New Jersey',
    'NM': 'New Mexico',      'NY': 'New York',        'NC': 'North Carolina',
    'ND': 'North Dakota',    'OH': 'Ohio',            'OK': 'Oklahoma',
    'OR': 'Oregon',          'PA': 'Pennsylvania',    'RI': 'Rhode Island',
    'SC': 'South Carolina',  'SD': 'South Dakota',    'TN': 'Tennessee',
    'TX': 'Texas',           'UT': 'Utah',            'VT': 'Vermont',
    'VA': 'Virginia',        'WA': 'Washington',      'WV': 'West Virginia',
    'WI': 'Wisconsin',       'WY': 'Wyoming',         'DC': 'District of Columbia',
}


def _fetch_rss(name, url, max_items=15):
    """Fetch RSS feed and return list of {title, link, published, source}.

    v1.5.0 (May 29 2026): THREE retry tiers for escalating bot detection:
      1. requests + Chrome 130 + Client Hints (fast, works for most)
      2. requests + Firefox UA fallback (defeats Chrome-specific rules)
      3. curl_cffi + TLS/JA3 fingerprint impersonation (defeats Cloudflare
         at network layer — catches sites that detect requests-library
         regardless of headers).
    Tier 3 added because Cloudflare escalated to TLS-fingerprint-based
    detection ~May 2026, defeating header-only approaches.
    """
    # Complete Chrome 130 / Windows 11 browser fingerprint with Client Hints.
    # This is what a real Chrome browser sends on every request.
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/130.0.0.0 Safari/537.36'
        ),
        'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                   'application/rss+xml;q=0.9,image/avif,image/webp,*/*;q=0.8'),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0',
        'Sec-Ch-Ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
    }
    try:
        resp = requests.get(url, timeout=DEFAULT_TIMEOUT, headers=headers,
                            allow_redirects=True)
        # ── Tier 2: Firefox UA fallback on 403 ──
        if resp.status_code == 403:
            print(f"[US Stability RSS] {name}: HTTP 403 — retrying with Firefox UA")
            firefox_headers = {
                'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) '
                               'Gecko/20100101 Firefox/130.0'),
                'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                           'image/avif,image/webp,*/*;q=0.8'),
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Referer': 'https://duckduckgo.com/',
            }
            time.sleep(1.2)
            resp = requests.get(url, timeout=DEFAULT_TIMEOUT, headers=firefox_headers,
                                allow_redirects=True)
        # ── Tier 3: curl_cffi with TLS fingerprint impersonation ──
        # Triggers on persistent 403 (both tiers failed) OR on the "not well-formed"
        # XML parse failures that mean Cloudflare returned an HTML challenge page.
        if resp.status_code == 403 and CURL_CFFI_AVAILABLE:
            print(f"[US Stability RSS] {name}: HTTP 403 — retrying with curl_cffi TLS impersonation")
            try:
                time.sleep(0.8)
                cc_resp = curl_requests.get(url, impersonate='chrome',
                                            timeout=DEFAULT_TIMEOUT,
                                            allow_redirects=True)
                if cc_resp.status_code == 200:
                    # Repackage curl_cffi response for downstream XML parser
                    class _CCWrapper:
                        def __init__(self, cc):
                            self.status_code = cc.status_code
                            self.content = cc.content
                            self.text = cc.text
                    resp = _CCWrapper(cc_resp)
                    print(f"[US Stability RSS] {name}: ✅ curl_cffi rescued (TLS impersonation)")
                else:
                    print(f"[US Stability RSS] {name}: curl_cffi also got HTTP {cc_resp.status_code}")
            except Exception as cc_err:
                print(f"[US Stability RSS] {name}: curl_cffi error {str(cc_err)[:100]}")
        if resp.status_code != 200:
            print(f"[US Stability RSS] {name}: HTTP {resp.status_code}")
            return []
        root = ET.fromstring(resp.text)
        items = []
        # Handle both RSS and Atom
        for item in (root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')):
            title_el = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
            link_el = item.find('link') or item.find('{http://www.w3.org/2005/Atom}link')
            pub_el = (item.find('pubDate') or
                      item.find('{http://www.w3.org/2005/Atom}published') or
                      item.find('{http://www.w3.org/2005/Atom}updated'))
            desc_el = (item.find('description') or
                       item.find('{http://www.w3.org/2005/Atom}summary'))
            if title_el is None or title_el.text is None:
                continue
            link_text = ''
            if link_el is not None:
                link_text = (link_el.text or link_el.get('href') or '').strip()
            items.append({
                'title':       title_el.text.strip(),
                'description': (desc_el.text or '').strip() if desc_el is not None else '',
                'link':        link_text,
                'published':   pub_el.text.strip() if (pub_el is not None and pub_el.text) else '',
                'source':      name,
                'source_type': 'rss',
            })
            if len(items) >= max_items:
                break
        return items
    except Exception as e:
        print(f"[US Stability RSS] {name}: error {str(e)[:100]}")
        return []


def _fetch_gdelt(query, max_records=30):
    """Fetch GDELT articles for a query. Returns list of articles.

    v1.3.0 (May 27 2026): bumped read timeout from 10s to 20s — GDELT regularly
    latencies past 10s under load. Connect timeout still tight at 5s to fail
    fast if the host itself is unreachable.
    """
    try:
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            'query':       f'{query} sourcecountry:US',
            'mode':        'artlist',
            'maxrecords':  max_records,
            'format':      'json',
            'timespan':    '7d',
        }
        resp = requests.get(url, params=params,
                            timeout=(5, 20),    # connect, read — bumped from 10s
                            headers={'User-Agent': 'AsifahAnalytics/1.0'})
        if resp.status_code == 429:
            print(f"[US Stability GDELT] rate-limited")
            return []
        if resp.status_code != 200:
            return []
        data = resp.json()
        articles = data.get('articles', [])
        return [{
            'title':       a.get('title', ''),
            'description': '',
            'link':        a.get('url', ''),
            'published':   a.get('seendate', ''),
            'source':      f"GDELT/{a.get('domain', 'unknown')}",
            'source_type': 'gdelt',
        } for a in articles]
    except Exception as e:
        print(f"[US Stability GDELT] error {str(e)[:100]}")
        return []


def _fetch_brave(query, max_records=20):
    """Fetch articles from Brave Search API (tertiary fallback when GDELT + NewsAPI
    fall short). Free tier: 2000 queries/month, 1 req/sec.

    v1.0.0 (May 27 2026): wired into WHA backend per backlog item #21.
    Returns same article shape as RSS/GDELT/NewsAPI.
    """
    if not BRAVE_API_KEY:
        return []
    try:
        url = "https://api.search.brave.com/res/v1/news/search"
        params = {
            'q':           query,
            'count':       max_records,
            'country':     'us',
            'search_lang': 'en',
            'spellcheck':  0,
            'freshness':   'pw',   # past week
        }
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT,
                            headers={
                                'Accept': 'application/json',
                                'X-Subscription-Token': BRAVE_API_KEY,
                                'User-Agent': 'AsifahAnalytics/1.0',
                            })
        if resp.status_code == 429:
            print(f"[US Stability Brave] rate-limited")
            return []
        if resp.status_code != 200:
            print(f"[US Stability Brave] HTTP {resp.status_code}")
            return []
        data = resp.json()
        results = data.get('results', []) or []
        return [{
            'title':       a.get('title', '') or '',
            'description': a.get('description', '') or '',
            'link':        a.get('url', ''),
            'published':   a.get('age', '') or '',
            'source':      f"Brave/{(a.get('meta_url') or {}).get('hostname', 'unknown')}",
            'source_type': 'brave',
        } for a in results if a.get('title')]
    except Exception as e:
        print(f"[US Stability Brave] error {str(e)[:120]}")
        return []


def _fetch_newsapi(query, max_records=30):
    """Fetch NewsAPI articles for a query. Returns list of articles."""
    if not NEWSAPI_KEY:
        return []
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q':         query,
            'language':  'en',
            'sortBy':    'publishedAt',
            'pageSize':  max_records,
            'apiKey':    NEWSAPI_KEY,
        }
        # Constrain to last 7 days
        from_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
        params['from'] = from_date
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        if resp.status_code != 200:
            return []
        data = resp.json()
        articles = data.get('articles', [])
        return [{
            'title':       a.get('title', '') or '',
            'description': a.get('description', '') or '',
            'link':        a.get('url', ''),
            'published':   a.get('publishedAt', ''),
            'source':      f"NewsAPI/{(a.get('source') or {}).get('name', 'unknown')}",
            'source_type': 'newsapi',
        } for a in articles if a.get('title')]
    except Exception as e:
        print(f"[US Stability NewsAPI] error {str(e)[:100]}")
        return []


# ============================================================
# NYSE / US EQUITY INDICES (v1.0.0 — May 27 2026)
# ============================================================
# Cache-first architecture:
#   - Page loads NEVER trigger Alpha Vantage calls
#   - Twice-daily scheduled refreshes at 7am + 7pm ET
#   - 7am call: quotes only (3 AV calls)
#   - 7pm call: quotes + sparkline series (6 AV calls)
#   - Daily budget: 9 calls / 500 free-tier limit (1.8% utilization)
#   - Manual refresh button bypasses cache via ?refresh=true&nyse=true
# ============================================================

def _is_us_market_open():
    """Return market status: 'open', 'closed', 'pre-market', or 'after-hours'.

    Uses naive ET time approximation (no DST math — close enough for status display).
    Markets: Mon-Fri, 9:30 AM - 4:00 PM ET regular hours.
    """
    now_utc = datetime.now(timezone.utc)
    # ET is UTC-5 (EST) or UTC-4 (EDT) — approximate as UTC-4 since US is on DST most of year
    et_hour = (now_utc.hour - 4) % 24
    weekday = now_utc.weekday()    # Mon=0 ... Sun=6
    if weekday >= 5:
        return 'closed'
    if 9 <= et_hour < 16:
        # Approximate — doesn't strictly check 9:30, but close enough for display
        return 'open'
    if 4 <= et_hour < 9:
        return 'pre-market'
    if 16 <= et_hour < 20:
        return 'after-hours'
    return 'closed'


def _fetch_av_quote(av_symbol):
    """Fetch a single index quote from Alpha Vantage GLOBAL_QUOTE endpoint.

    Returns dict with {value, change_pct_24h, source} or None on failure.
    """
    if not ALPHA_VANTAGE_KEY:
        return None
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol':   av_symbol,
            'apikey':   ALPHA_VANTAGE_KEY,
        }
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT,
                            headers={'User-Agent': 'AsifahAnalytics/1.0'})
        if resp.status_code != 200:
            print(f"[NYSE/AV] {av_symbol}: HTTP {resp.status_code}")
            return None
        data = resp.json()
        quote = data.get('Global Quote', {}) or data.get('GlobalQuote', {})
        if not quote or '05. price' not in quote:
            # Could be a rate-limit message — log it
            note = data.get('Note') or data.get('Information') or 'no quote field'
            print(f"[NYSE/AV] {av_symbol}: empty response — {str(note)[:120]}")
            return None
        price = float(quote.get('05. price', 0))
        change_pct_str = quote.get('10. change percent', '0%').replace('%', '').strip()
        change_pct = float(change_pct_str)
        return {
            'value':          price,
            'change_pct_24h': change_pct,
            'source':         'Alpha Vantage',
        }
    except Exception as e:
        print(f"[NYSE/AV] {av_symbol}: error {str(e)[:120]}")
        return None


def _fetch_yahoo_quote(yahoo_symbol):
    """Fetch a single index quote from Yahoo Finance (free, no key required).

    Uses the v8 chart endpoint which is the most reliable unauthenticated path.
    Returns dict with {value, change_pct_24h, source} or None on failure.
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
        params = {'range': '5d', 'interval': '1d'}
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT,
                            headers={'User-Agent': 'Mozilla/5.0 (AsifahAnalytics/1.0)'})
        if resp.status_code != 200:
            print(f"[NYSE/Yahoo] {yahoo_symbol}: HTTP {resp.status_code}")
            return None
        data = resp.json()
        result = (data.get('chart', {}).get('result') or [{}])[0]
        meta = result.get('meta', {})
        price = meta.get('regularMarketPrice')
        prev_close = meta.get('chartPreviousClose') or meta.get('previousClose')
        if price is None or prev_close in (None, 0):
            return None
        change_pct = ((price - prev_close) / prev_close) * 100
        return {
            'value':          float(price),
            'change_pct_24h': round(change_pct, 2),
            'source':         'Yahoo Finance',
        }
    except Exception as e:
        print(f"[NYSE/Yahoo] {yahoo_symbol}: error {str(e)[:120]}")
        return None


def _fetch_yahoo_sparkline(yahoo_symbol):
    """Fetch 30-day daily closes for sparkline. Yahoo only (Alpha Vantage time-series
    burns extra calls). Returns list of {time, value} or empty list on failure.
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
        params = {'range': '1mo', 'interval': '1d'}
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT,
                            headers={'User-Agent': 'Mozilla/5.0 (AsifahAnalytics/1.0)'})
        if resp.status_code != 200:
            return []
        data = resp.json()
        result = (data.get('chart', {}).get('result') or [{}])[0]
        timestamps = result.get('timestamp', []) or []
        closes = (result.get('indicators', {}).get('quote') or [{}])[0].get('close', []) or []
        spark = []
        for i, ts in enumerate(timestamps):
            if i < len(closes) and closes[i] is not None:
                spark.append({
                    'time':  datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat(),
                    'value': round(float(closes[i]), 2),
                })
        return spark
    except Exception as e:
        print(f"[NYSE/Yahoo sparkline] {yahoo_symbol}: error {str(e)[:120]}")
        return []


def _refresh_nyse_data(refresh_sparklines=False):
    """Run a full NYSE refresh: fetch quotes for all 3 indices, optionally sparklines.

    Args:
        refresh_sparklines: True for the 7pm EOD pull; False for the 7am quote-only pull.

    Returns the full NYSE payload (also writes to Redis).
    """
    print(f"[NYSE] Refreshing — sparklines={'YES' if refresh_sparklines else 'no'}")
    market_status = _is_us_market_open()
    indices_data = {}

    # Read existing cache so we preserve sparklines on 7am pulls
    existing = _redis_get(NYSE_CACHE_KEY) or {}
    existing_indices = existing.get('indices', {})

    for idx in NYSE_INDICES:
        key = idx['key']
        # Try Alpha Vantage first
        quote = _fetch_av_quote(idx['av_symbol'])
        if not quote:
            # Fallback to Yahoo
            quote = _fetch_yahoo_quote(idx['yahoo_symbol'])
        if not quote:
            # Both failed — preserve last known
            print(f"[NYSE] {key}: both AV and Yahoo failed, preserving last-known")
            if key in existing_indices:
                indices_data[key] = existing_indices[key]
                indices_data[key]['source'] = (existing_indices[key].get('source', 'unknown')
                                                + ' (stale)')
            continue

        # Derive trend from change_pct_24h
        chg = quote['change_pct_24h']
        trend = 'rising' if chg > 0.05 else 'falling' if chg < -0.05 else 'flat'

        indices_data[key] = {
            'index':          key,
            'name':           idx['name'],
            'value':          quote['value'],
            'change_pct_24h': chg,
            'trend':          trend,
            'source':         quote['source'],
            'market_status':  market_status,
            'timestamp':      datetime.now(timezone.utc).isoformat(),
        }

        # Sparkline: only refresh on EOD pull (Yahoo always — sparklines from AV are expensive)
        if refresh_sparklines:
            spark = _fetch_yahoo_sparkline(idx['yahoo_symbol'])
            if spark:
                indices_data[key]['sparkline'] = spark
            elif key in existing_indices and 'sparkline' in existing_indices[key]:
                # Preserve old sparkline if Yahoo failed
                indices_data[key]['sparkline'] = existing_indices[key]['sparkline']
        else:
            # 7am pull — preserve existing sparkline
            if key in existing_indices and 'sparkline' in existing_indices[key]:
                indices_data[key]['sparkline'] = existing_indices[key]['sparkline']

        time.sleep(0.3)    # gentle pacing between AV calls

    payload = {
        'indices':          indices_data,
        'market_status':    market_status,
        'last_refreshed':   datetime.now(timezone.utc).isoformat(),
        'sparklines_age':   'eod' if refresh_sparklines else 'previous_eod',
    }
    _redis_set(NYSE_CACHE_KEY, payload, ttl_seconds=NYSE_TTL_SECONDS)
    print(f"[NYSE] ✅ Refresh complete — {len(indices_data)} indices, market={market_status}")
    return payload


def get_nyse_data(force_refresh=False, refresh_sparklines=False):
    """Read NYSE data — cache-first by default. Page loads should NEVER force.

    Only the manual refresh button + scheduled scanner should pass force_refresh=True.
    """
    if not force_refresh:
        cached = _redis_get(NYSE_CACHE_KEY)
        if cached:
            return cached
    return _refresh_nyse_data(refresh_sparklines=refresh_sparklines)


# ============================================================
# REDIS HELPERS
# ============================================================

def _redis_get(key):
    if not (UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN):
        return None
    try:
        resp = requests.get(
            f"{UPSTASH_REDIS_URL}/get/{key}",
            headers={"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"},
            timeout=5)
        body = resp.json()
        if body.get('result'):
            return json.loads(body['result'])
    except Exception as e:
        print(f"[US Stability] Redis get error: {str(e)[:100]}")
    return None


def _redis_set(key, value, ttl_seconds=CACHE_TTL_SECONDS):
    if not (UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN):
        return False
    try:
        resp = requests.post(
            f"{UPSTASH_REDIS_URL}/setex/{key}/{int(ttl_seconds)}",
            headers={"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"},
            data=json.dumps(value, default=str),
            timeout=8)
        return resp.status_code == 200
    except Exception:
        return False


# ============================================================
# SIGNAL DETECTION
# ============================================================

def _detect_signals(articles, keyword_dimension):
    """Scan articles for keyword matches in a dimension's keyword set.

    Returns list of {category, pattern, weight, article} matches.
    Same article can match multiple categories.
    """
    matches = []
    for art in articles:
        haystack = (art.get('title', '') + ' ' + art.get('description', '')).lower()
        if not haystack.strip():
            continue
        for category, cfg in keyword_dimension.items():
            for pattern in cfg['patterns']:
                if pattern.lower() in haystack:
                    matches.append({
                        'category':                category,
                        'pattern':                 pattern,
                        'base_weight':             cfg['base_weight'],
                        'baseline_modifier_key':   cfg.get('baseline_modifier_key'),
                        'article':                 art,
                    })
                    break    # only one pattern per article per category
    return matches


def _extract_states(text):
    """Find U.S. state name mentions in text. Returns list of state codes."""
    text_lower = (text or '').lower()
    mentioned = []
    for code, name in US_STATES.items():
        if name.lower() in text_lower:
            mentioned.append(code)
    return mentioned


# ============================================================
# DIMENSION SCORING FUNCTIONS
# ============================================================

def score_economic_dimension():
    """Score Dimension 1 — Economic Stability.

    Returns: {score, band, indicators, top_signals, source: 'economic_indicators_us'}
    """
    if not ECON_AVAILABLE:
        return {
            'score':       50,
            'band':        score_to_band(50),
            'error':       'economic_indicators_us module not available',
            'indicators':  {},
            'top_signals': [],
        }

    try:
        econ_data = fetch_economic_indicators()
    except Exception as e:
        return {
            'score':       50,
            'band':        score_to_band(50),
            'error':       f'economic fetch failed: {str(e)[:100]}',
            'indicators':  {},
            'top_signals': [],
        }

    indicators = econ_data.get('indicators', {})
    scored = {}
    weighted_sum = 0.0
    weight_total = 0.0
    top_signals = []

    for indicator_id, ind in indicators.items():
        value = ind.get('value')
        if value is None:
            continue
        if indicator_id not in ECON_THRESHOLDS:
            continue
        stress = score_economic_indicator(indicator_id, value)
        if stress is None:
            continue
        # Tier weighting: top-tier 2x, expanded 1x
        tier_w = 2.0 if ind.get('tier') == 'top' else 1.0
        weighted_sum += stress * tier_w
        weight_total += tier_w
        scored[indicator_id] = {
            'name':   ind.get('name'),
            'value':  value,
            'unit':   ind.get('unit'),
            'stress_score': stress,
            'tier':   ind.get('tier'),
            'frame':  ind.get('frame'),
            'source': ind.get('source'),
        }
        # Surface high-stress indicators as top signals
        if stress >= 50:
            top_signals.append({
                'short_text':  f"{ind.get('name')}: {value} {ind.get('unit', '')}",
                'long_text':   ind.get('frame', '') + f" Current: {value} {ind.get('unit', '')}.",
                'level':       3 if stress >= 70 else 2 if stress >= 50 else 1,
                'level_name':  'crisis' if stress >= 70 else 'elevated' if stress >= 50 else 'monitor',
                'category':    'econ_indicator',
                'icon':        '📉',
                'priority':    int(stress / 10),
            })

    final_score = round(weighted_sum / weight_total) if weight_total > 0 else 50

    # Sort top signals by priority
    top_signals.sort(key=lambda s: -s['priority'])

    return {
        'dimension':   'economic',
        'score':       final_score,
        'band':        score_to_band(final_score),
        'indicators':  scored,
        'top_signals': top_signals[:5],
        'source':      f"FRED + Yahoo ({len(scored)} indicators scored)",
        'fetched_at':  econ_data.get('fetched_at'),
        'fred_configured': econ_data.get('fred_configured'),
    }


def _score_keyword_dimension(dimension_id, keyword_set, articles, baseline_modifiers):
    """Generic scorer for keyword-based dimensions (Political, Civil, Democratic, Cyber).

    Returns: {score, band, top_signals, signals_detected, articles_scanned}
    """
    matches = _detect_signals(articles, keyword_set)

    # Aggregate by category
    category_data = {}
    for m in matches:
        cat = m['category']
        if cat not in category_data:
            category_data[cat] = {
                'count':       0,
                'weight':      m['base_weight'],
                'modifier':    1.0,
                'modifier_key': m['baseline_modifier_key'],
                'sample_articles': [],
                'states':      set(),
            }
        category_data[cat]['count'] += 1
        # Apply baseline modifier
        if m['baseline_modifier_key'] and baseline_modifiers:
            category_data[cat]['modifier'] = baseline_modifiers.get(
                m['baseline_modifier_key'], 1.0)
        # Sample article (up to 3 per category)
        if len(category_data[cat]['sample_articles']) < 3:
            category_data[cat]['sample_articles'].append({
                'title':     m['article'].get('title', ''),
                'link':      m['article'].get('link', ''),
                'source':    m['article'].get('source', ''),
                'pattern':   m['pattern'],
            })
        # Aggregate state mentions
        states_in_article = _extract_states(
            m['article'].get('title', '') + ' ' + m['article'].get('description', ''))
        category_data[cat]['states'].update(states_in_article)

    # Compute dimension score
    # Each category contributes: count * base_weight * modifier
    # Capped at 100; aggregated cumulatively but with diminishing returns
    raw_score = 0.0
    for cat, data in category_data.items():
        category_contribution = data['count'] * data['weight'] * data['modifier']
        # Diminishing returns: cap individual category at 35 points
        raw_score += min(35, category_contribution)
    # Cap total at 100
    final_score = min(100, round(raw_score))

    # Build top signals from highest-impact categories
    top_signals = []
    sorted_cats = sorted(category_data.items(),
                         key=lambda x: -x[1]['count'] * x[1]['weight'] * x[1]['modifier'])
    for cat, data in sorted_cats[:5]:
        impact = data['count'] * data['weight'] * data['modifier']
        if impact < 5:
            continue
        level = 3 if impact >= 30 else 2 if impact >= 15 else 1
        level_name = 'crisis' if level == 3 else 'elevated' if level == 2 else 'monitor'
        top_signals.append({
            'short_text':  f"{cat.replace('_', ' ').title()}: {data['count']} signal(s)",
            'long_text':   (f"{data['count']} signal(s) detected in {cat.replace('_', ' ')} "
                            f"category. Weight {data['weight']} × modifier {data['modifier']:.2f}. "
                            f"States mentioned: {', '.join(sorted(data['states'])) or 'national'}."),
            'level':       level,
            'level_name':  level_name,
            'category':    f'{dimension_id}_{cat}',
            'icon':        '⚡' if level == 3 else '🔶' if level == 2 else '🔸',
            'priority':    int(impact),
            'sample_articles': data['sample_articles'],
        })

    # Convert sets to sorted lists for JSON serialization
    cat_data_serializable = {}
    for cat, data in category_data.items():
        cat_data_serializable[cat] = {
            **{k: v for k, v in data.items() if k != 'states'},
            'states': sorted(data['states']),
        }

    return {
        'dimension':       dimension_id,
        'score':           final_score,
        'band':            score_to_band(final_score),
        'top_signals':     top_signals,
        'category_data':   cat_data_serializable,
        'signals_detected': len(matches),
        'articles_scanned': len(articles),
    }


def score_political_cohesion(articles, baseline_modifiers):
    """Score Dimension 2 — Political Cohesion."""
    return _score_keyword_dimension(
        'political_cohesion', POLITICAL_COHESION_KEYWORDS, articles, baseline_modifiers)


def score_civil_social(articles, baseline_modifiers):
    """Score Dimension 3 — Civil/Social Stability."""
    return _score_keyword_dimension(
        'civil_social', CIVIL_SOCIAL_KEYWORDS, articles, baseline_modifiers)


def score_democratic_institutions(articles, baseline_modifiers):
    """Score Dimension 4 — Democratic Institutions."""
    return _score_keyword_dimension(
        'democratic_institutions', DEMOCRATIC_INSTITUTIONS_KEYWORDS, articles, baseline_modifiers)


def score_cyber_infrastructure(articles, baseline_modifiers):
    """Score Dimension 6 — Cyber/Infrastructure."""
    return _score_keyword_dimension(
        'cyber_infrastructure', CYBER_INFRA_KEYWORDS, articles, baseline_modifiers)


def score_military_posture():
    """Score Dimension 5 — Military Posture.

    Reads from military:us:posture Redis fingerprint (the contract built
    earlier today in military_tracker.py v3.x).
    """
    us_posture = _redis_get('military:us:posture')
    cross_refs = {}
    for label in ['nato_us_active', 'us_venezuela_active', 'us_cuba_active',
                  'us_panama_active', 'us_greenland_active']:
        cr = _redis_get(f'military:cross:{label}')
        if cr:
            cross_refs[label] = cr

    if not us_posture:
        # Cold start — no military fingerprint available
        return {
            'dimension':   'military_posture',
            'score':       40,
            'band':        score_to_band(40),
            'top_signals': [],
            'mil_fingerprint': None,
            'cross_references': cross_refs,
            'note':        'Military posture fingerprint not yet available (cold start or mil tracker not deployed).',
        }

    # Extract score from posture (mil tracker peaks ~200; map to 0-100)
    raw_score = us_posture.get('score', 0)
    stability_score = min(100, round(raw_score / 2))

    # Surface top mil signals
    top_signals = []
    mil_top = us_posture.get('top_signals', [])
    for sig in mil_top[:3]:
        top_signals.append({
            'short_text':  f"🪖 {sig.get('asset_label', 'Mil signal')}: {sig.get('actor_name', '')}",
            'long_text':   f"{sig.get('article_title', '')[:200]} (weight {sig.get('weight', 0)}, "
                            f"location: {sig.get('hotspot_location', 'unspecified')})",
            'level':       3 if sig.get('weight', 0) >= 8 else 2 if sig.get('weight', 0) >= 5 else 1,
            'level_name':  'crisis' if sig.get('weight', 0) >= 8 else 'elevated' if sig.get('weight', 0) >= 5 else 'monitor',
            'category':    'mil_us_posture',
            'icon':        '🪖',
            'priority':    int(sig.get('weight', 0)),
        })

    # Add cross-reference signals
    for label, cr_data in cross_refs.items():
        if cr_data and cr_data.get('active'):
            top_signals.append({
                'short_text':  f"🔗 Cross-reference: {label.replace('_', ' ')}",
                'long_text':   f"Military cross-reference signal active: {label}. "
                                f"{cr_data.get('rationale', '')}",
                'level':       2,
                'level_name':  'elevated',
                'category':    'mil_cross_ref',
                'icon':        '🔗',
                'priority':    5,
            })

    return {
        'dimension':         'military_posture',
        'score':             stability_score,
        'band':              score_to_band(stability_score),
        'top_signals':       top_signals,
        'mil_fingerprint':   us_posture,
        'cross_references':  cross_refs,
        'mil_alert_level':   us_posture.get('alert_level'),
        'evac_active':       us_posture.get('evac_active', False),
    }


# ============================================================
# COMPOSITE SCORING
# ============================================================

def compute_composite_score(dimension_scores, election_cycle):
    """Compute weighted composite score from 6 dimensions.

    Applies election-cycle stability_modifier as final multiplier.
    Capped at 100.
    """
    composite_raw = 0.0
    for dim_id, weight in DIMENSION_WEIGHTS.items():
        dim = dimension_scores.get(dim_id, {})
        score = dim.get('score', 50)
        composite_raw += score * weight

    cycle_modifier = (election_cycle or {}).get('stability_modifier', 1.0)
    composite_final = min(100, round(composite_raw * cycle_modifier))

    return {
        'score':            composite_final,
        'raw_score':        round(composite_raw, 1),
        'cycle_modifier':   cycle_modifier,
        'band':             score_to_band(composite_final),
        'weights_applied':  DIMENSION_WEIGHTS,
    }


# ============================================================
# 30-DAY HISTORY MANAGEMENT
# ============================================================

def update_history(composite_score):
    """Append today's composite score to 30-day history.

    History stored as list of {date, score, band} dicts. One entry per day;
    if today already has an entry, it's overwritten with latest.
    """
    history = _redis_get(HISTORY_KEY) or {'snapshots': []}
    snapshots = history.get('snapshots', [])
    today_str = datetime.now(timezone.utc).date().isoformat()

    # Remove any existing entry for today
    snapshots = [s for s in snapshots if s.get('date') != today_str]

    # Add today's entry
    snapshots.append({
        'date':  today_str,
        'score': composite_score['score'],
        'band':  composite_score['band']['band'],
    })

    # Sort by date and keep only last 30 days
    snapshots.sort(key=lambda s: s['date'])
    snapshots = snapshots[-HISTORY_DAYS:]

    history['snapshots'] = snapshots
    history['updated_at'] = datetime.now(timezone.utc).isoformat()
    _redis_set(HISTORY_KEY, history, ttl_seconds=90 * 24 * 3600)    # 90-day TTL safety
    return history


# ============================================================
# CROSS-TRACKER FINGERPRINT WRITES
# ============================================================

def write_stability_fingerprint(scan_result):
    """Write a compressed stability fingerprint for GPI consumption.

    Schema:
      stability:us:fingerprint = {
        'composite_score':  int 0-100,
        'composite_band':   'resilient' | 'stressed' | 'fractured' | 'crisis_mode' | 'constitutional_crisis',
        'dimension_scores': {economic: int, political_cohesion: int, ...},
        'election_phase':   string,
        'unified_government': bool,
        'top_signals_count': int,
        'updated_at':       ISO timestamp,
      }
    """
    composite = scan_result.get('composite', {})
    dimensions = scan_result.get('dimensions', {})

    fingerprint = {
        'composite_score':    composite.get('score', 50),
        'composite_band':     composite.get('band', {}).get('band', 'stressed'),
        'composite_label':    composite.get('band', {}).get('label', 'Stressed'),
        'dimension_scores':   {dim_id: dim.get('score', 50)
                                for dim_id, dim in dimensions.items()},
        'election_phase':     scan_result.get('election_cycle', {}).get('phase'),
        'unified_government': scan_result.get('structural_baseline', {}).get('unified_government'),
        'top_signals_count':  len(scan_result.get('top_signals', [])),
        'updated_at':         datetime.now(timezone.utc).isoformat(),
    }
    _redis_set(FINGERPRINT_KEY, fingerprint, ttl_seconds=CACHE_TTL_SECONDS)
    _redis_set(SUMMARY_KEY, {
        'score':  fingerprint['composite_score'],
        'band':   fingerprint['composite_band'],
        'updated_at': fingerprint['updated_at'],
    }, ttl_seconds=CACHE_TTL_SECONDS)
    return fingerprint


# ============================================================
# MAIN SCAN
# ============================================================

def _read_us_rhetoric_fingerprint():
    """Read fingerprint:us:current written by the US Rhetoric Tracker.

    Returns dict with at least the following keys (or empty dict if unavailable):
      us_active, us_composite_score, us_executive_volatility,
      us_dhs_enforcement_score, us_dhs_enforcement_active,
      us_branch_divergence_score, us_domestic_fracture_score,
      us_outbound_targets[], us_judicial_pushback_score, updated_at

    Wire #5 (May 2026): Civil/Social and Political Cohesion dimensions
    get a small adjustment based on this fingerprint so the stability score
    reflects current rhetoric volatility (not just keyword news scanning).
    """
    fp = _redis_get('fingerprint:us:current')
    if not fp or not isinstance(fp, dict):
        return {}
    return fp


def _apply_rhetoric_adjustments(dimensions, rhetoric_fp):
    """Apply rhetoric-driven adjustments to Civil/Social and Political Cohesion
    dimensions based on the US Rhetoric Tracker's fingerprint.

    Mutates dimensions in place. Returns dict of adjustments applied (for logging
    + frontend transparency).

    Calibration philosophy (per Rachel May 2026):
      - DHS/ICE rhetoric is the highest-volatility civil unrest leading indicator,
        so its score boosts Civil/Social.
      - Branch divergence is institutional friction, so it boosts Political Cohesion.
      - Both adjustments are capped to avoid swamping the underlying keyword score.
    """
    adjustments = {}
    if not rhetoric_fp:
        return adjustments

    # ── Civil/Social: boost by DHS/ICE enforcement score ──
    dhs_score = rhetoric_fp.get('us_dhs_enforcement_score', 0) or 0
    if dhs_score >= 26:  # only adjust if rhetoric is at least Active
        # Convert rhetoric score to stability bump (cap at +20)
        bump = min(20, round(dhs_score / 4))
        if 'civil_social' in dimensions:
            old_score = dimensions['civil_social'].get('score', 0)
            new_score = min(100, old_score + bump)
            dimensions['civil_social']['score'] = new_score
            dimensions['civil_social']['band'] = score_to_band(new_score)
            dimensions['civil_social']['rhetoric_adjustment'] = {
                'source':         'us_rhetoric_dhs',
                'rhetoric_score': dhs_score,
                'stability_bump': bump,
                'rationale':      'DHS/ICE rhetoric is a civil unrest leading indicator.',
            }
            adjustments['civil_social'] = bump

    # ── Political Cohesion: boost by branch divergence ──
    branch_div = rhetoric_fp.get('us_branch_divergence_score', 0) or 0
    if branch_div >= 26:
        bump = min(15, round(branch_div / 5))
        if 'political_cohesion' in dimensions:
            old_score = dimensions['political_cohesion'].get('score', 0)
            new_score = min(100, old_score + bump)
            dimensions['political_cohesion']['score'] = new_score
            dimensions['political_cohesion']['band'] = score_to_band(new_score)
            dimensions['political_cohesion']['rhetoric_adjustment'] = {
                'source':         'us_rhetoric_branch_divergence',
                'rhetoric_score': branch_div,
                'stability_bump': bump,
                'rationale':      'Branch divergence indicates institutional friction.',
            }
            adjustments['political_cohesion'] = bump

    return adjustments


def run_stability_scan():
    """Run a full US stability scan. Returns the complete scan_result dict."""
    print("[US Stability] === Starting full scan ===")
    scan_start = time.time()

    # ── Fetch government composition + structural baseline ──
    if GOVT_AVAILABLE:
        govt = get_government_composition()
    else:
        govt = {
            'congress':            {},
            'executive':           {},
            'election_cycle':      {'phase': 'regular', 'stability_modifier': 1.0},
            'structural_baseline': {
                'unified_government':  False,
                'baseline_modifiers':  {},
            },
        }
    structural_baseline = govt.get('structural_baseline', {})
    baseline_modifiers = structural_baseline.get('baseline_modifiers', {})
    election_cycle = govt.get('election_cycle', {})

    # ── Aggregate articles from all sources ──
    print("[US Stability] Phase 1: fetching articles...")
    all_articles = []

    # RSS feeds
    for name, url in US_STABILITY_RSS:
        articles = _fetch_rss(name, url)
        all_articles.extend(articles)
        time.sleep(0.2)    # gentle pacing

    print(f"[US Stability] RSS: {len(all_articles)} articles")

    # GDELT queries (one per dimension to avoid hammering)
    gdelt_queries = [
        '("court order" OR "inspector general" OR "civil service")',
        '("mass shooting" OR "active shooter" OR "protest")',
        '("cabinet" OR "secretary resigns" OR "shutdown")',
        '("ransomware" OR "cyberattack" OR "infrastructure")',
    ]
    for q in gdelt_queries:
        gdelt_articles = _fetch_gdelt(q, max_records=15)
        all_articles.extend(gdelt_articles)
        time.sleep(0.5)

    # NewsAPI fallback
    if NEWSAPI_KEY:
        for q in ['"court order" defied United States',
                  '"mass shooting" United States',
                  '"cabinet" OR "secretary fired" United States',
                  '"ransomware" United States']:
            na = _fetch_newsapi(q, max_records=10)
            all_articles.extend(na)

    pre_social_count = len(all_articles)
    print(f"[US Stability] Pre-social article pool: {pre_social_count}")

    # ── Social media signals (Bluesky / Telegram / Reddit) ──
    # Each call is independently try/except-wrapped so one source failing
    # never breaks the scan. All three return the standard article shape.

    if BLUESKY_US_AVAILABLE:
        try:
            bluesky_raw = fetch_bluesky_for_target('us', days=7, max_posts_per_account=20)
            bluesky_articles = []
            for p in bluesky_raw:
                bluesky_articles.append({
                    'title':       p.get('title') or p.get('text') or '',
                    'description': p.get('text') or p.get('description') or '',
                    'link':        p.get('url') or p.get('link') or '',
                    'published':   p.get('publishedAt') or p.get('published') or '',
                    'source':      p.get('source') or f"Bluesky/{p.get('handle','unknown')}",
                    'source_type': 'bluesky',
                })
            all_articles.extend(bluesky_articles)
            print(f"[US Stability] Bluesky: +{len(bluesky_articles)} posts")
        except Exception as e:
            print(f"[US Stability] Bluesky fetch error: {str(e)[:200]}")

    if TELEGRAM_US_AVAILABLE:
        try:
            telegram_raw = fetch_telegram_signals_us(hours_back=7 * 24)
            # Diagnostic: log raw count + sample channel names + sample title
            # to figure out why posts return 0 despite auth being valid
            if not telegram_raw:
                print("[US Stability] Telegram diagnostic: fetch_telegram_signals_us returned EMPTY list — "
                      "possible causes: (1) channel list empty in telegram_signals_wha config, "
                      "(2) session expired despite env var being set, (3) no posts in scan window")
            else:
                sample_channels = set()
                for p in telegram_raw[:10]:
                    raw_src = p.get('source')
                    if isinstance(raw_src, dict):
                        sample_channels.add(raw_src.get('name', '') or p.get('channel', '?'))
                    else:
                        sample_channels.add(str(raw_src or p.get('channel', '?')))
                print(f"[US Stability] Telegram diagnostic: raw={len(telegram_raw)} posts, "
                      f"sample channels={list(sample_channels)[:5]}")

            telegram_articles = []
            for p in telegram_raw:
                # Defensive: source may be a dict like {'name': 'Telegram @channel'} — coerce to string
                raw_src = p.get('source')
                if isinstance(raw_src, dict):
                    src_str = raw_src.get('name', '') or f"Telegram/{p.get('channel','unknown')}"
                else:
                    src_str = raw_src or f"Telegram/{p.get('channel','unknown')}"
                telegram_articles.append({
                    'title':       p.get('title') or p.get('text') or '',
                    'description': p.get('text') or p.get('description') or '',
                    'link':        p.get('url') or p.get('link') or '',
                    'published':   p.get('publishedAt') or p.get('published') or p.get('date') or '',
                    'source':      str(src_str),
                    'source_type': 'telegram',
                })
            all_articles.extend(telegram_articles)
            print(f"[US Stability] Telegram: +{len(telegram_articles)} posts")
        except Exception as e:
            print(f"[US Stability] Telegram fetch error: {str(e)[:200]}")

    # ── Brave Search fallback (v1.0.0 May 27 2026) ──
    # Fires when GDELT + NewsAPI under-deliver. Free tier: 2000/month, 1 req/sec.
    # Use 4 broad stability queries matching the 4 dimensions.
    if BRAVE_API_KEY:
        try:
            pre_brave_count = len(all_articles)
            brave_queries = [
                '"court order" OR "inspector general" OR "civil service" United States',
                '"mass shooting" OR "active shooter" OR "protest" United States',
                '"cabinet" OR "secretary resigns" OR "shutdown" United States',
                '"ransomware" OR "cyberattack" OR "infrastructure" United States',
            ]
            for q in brave_queries:
                brave_results = _fetch_brave(q, max_records=10)
                all_articles.extend(brave_results)
                time.sleep(1.1)   # respect 1 req/sec rate limit
            brave_added = len(all_articles) - pre_brave_count
            print(f"[US Stability] Brave fallback: +{brave_added} articles "
                  f"(across {len(brave_queries)} queries)")
        except Exception as e:
            print(f"[US Stability] Brave fallback error: {str(e)[:200]}")
    else:
        print("[US Stability] Brave fallback skipped: BRAVE_API_KEY not set")

    if REDDIT_US_AVAILABLE:
        try:
            reddit_articles = fetch_reddit_signals_us(days=7, max_per_sub=25)
            all_articles.extend(reddit_articles)
            print(f"[US Stability] Reddit: +{len(reddit_articles)} posts")
        except Exception as e:
            print(f"[US Stability] Reddit fetch error: {str(e)[:200]}")

    social_added = len(all_articles) - pre_social_count
    print(f"[US Stability] Social signal total: +{social_added} posts "
          f"(article pool now {len(all_articles)})")

    # Deduplicate by link
    seen_links = set()
    unique_articles = []
    for a in all_articles:
        link = a.get('link', '')
        if link and link not in seen_links:
            seen_links.add(link)
            unique_articles.append(a)
    all_articles = unique_articles

    print(f"[US Stability] Total deduplicated: {len(all_articles)} articles")

    # ── Score each dimension ──
    print("[US Stability] Phase 2: scoring dimensions...")
    dimensions = {
        'economic':                score_economic_dimension(),
        'political_cohesion':      score_political_cohesion(all_articles, baseline_modifiers),
        'civil_social':            score_civil_social(all_articles, baseline_modifiers),
        'democratic_institutions': score_democratic_institutions(all_articles, baseline_modifiers),
        'military_posture':        score_military_posture(),
        'cyber_infrastructure':    score_cyber_infrastructure(all_articles, baseline_modifiers),
    }

    # ── Wire #5 (May 2026): Read US Rhetoric fingerprint + apply adjustments ──
    # The rhetoric tracker writes fingerprint:us:current. We read it here and
    # apply small bumps to Civil/Social (DHS/ICE) and Political Cohesion
    # (branch divergence) so the stability score reflects rhetoric volatility.
    print("[US Stability] Phase 2.5: reading US rhetoric fingerprint...")
    rhetoric_fp = _read_us_rhetoric_fingerprint()
    if rhetoric_fp:
        adjustments = _apply_rhetoric_adjustments(dimensions, rhetoric_fp)
        if adjustments:
            print(f"[US Stability] Rhetoric adjustments applied: {adjustments}")
        else:
            print("[US Stability] Rhetoric fingerprint read but no thresholds met for adjustment")
    else:
        print("[US Stability] No rhetoric fingerprint available (tracker may still be on first scan)")

    # ── Composite score ──
    composite = compute_composite_score(dimensions, election_cycle)

    # ── Top signals across all dimensions (canonical schema for GPI) ──
    all_top_signals = []
    for dim_id, dim in dimensions.items():
        for sig in dim.get('top_signals', []):
            sig_copy = dict(sig)
            sig_copy['dimension'] = dim_id
            all_top_signals.append(sig_copy)
    all_top_signals.sort(key=lambda s: -s.get('priority', 0))
    top_signals = all_top_signals[:10]

    # ── State-level signal aggregation ──
    state_signals = {}
    for dim_id in ['political_cohesion', 'civil_social',
                    'democratic_institutions', 'cyber_infrastructure']:
        cat_data = (dimensions.get(dim_id, {}) or {}).get('category_data', {})
        for cat, data in cat_data.items():
            for state in data.get('states', []):
                state_signals[state] = state_signals.get(state, 0) + data['count']

    # ── Build scan result ──
    # Wire #5: include rhetoric fingerprint snapshot in the response so the
    # frontend can display the live coupling.
    # NYSE (v1.0.0 May 27 2026): cache-first — page loads NEVER trigger AV calls.
    # Scheduler fires at 7am + 7pm ET; manual refresh button can force via ?nyse=true.
    nyse_payload = _redis_get(NYSE_CACHE_KEY) or {
        'indices': {},
        'market_status': _is_us_market_open(),
        'last_refreshed': None,
        'note': 'NYSE cache not yet populated — first scheduled fetch pending',
    }
    elapsed = round(time.time() - scan_start, 1)
    scan_result = {
        'success':              True,
        'composite':            composite,
        'dimensions':           dimensions,
        'top_signals':          top_signals,
        'state_signals':        state_signals,
        'rhetoric_fingerprint': rhetoric_fp if rhetoric_fp else None,
        'election_cycle':       election_cycle,
        'structural_baseline':  structural_baseline,
        'government_data_freshness': govt.get('data_freshness'),
        'staleness_warning':    govt.get('staleness_warning'),
        'articles_scanned':     len(all_articles),
        'nyse':                 nyse_payload,
        'scan_time_seconds':    elapsed,
        'last_updated':         datetime.now(timezone.utc).isoformat(),
        'version':              '1.1.0',
    }

    # ── Update 30-day history ──
    update_history(composite)

    # ── Write cross-tracker fingerprint ──
    write_stability_fingerprint(scan_result)

    # ── Cache ──
    _redis_set(CACHE_KEY, scan_result)

    print(f"[US Stability] ✅ Scan complete in {elapsed}s — composite "
          f"{composite['score']} {composite['band']['label']} "
          f"({len(top_signals)} top signals across {len(state_signals)} states)")

    return scan_result


def get_stability_data(force_refresh=False):
    """Get current US stability data (cache-aware)."""
    if not force_refresh:
        cached = _redis_get(CACHE_KEY)
        if cached:
            return cached
    return run_stability_scan()


# ============================================================
# BACKGROUND SCAN MANAGEMENT
# ============================================================

def _trigger_background_scan():
    """Trigger an async background scan (non-blocking)."""
    global _scan_running
    with _scan_lock:
        if _scan_running:
            print("[US Stability] Background scan already running, skipping")
            return
        _scan_running = True

    def _bg():
        global _scan_running
        try:
            run_stability_scan()
        except Exception as e:
            print(f"[US Stability] Background scan error: {str(e)[:200]}")
            import traceback
            traceback.print_exc()
        finally:
            with _scan_lock:
                _scan_running = False

    threading.Thread(target=_bg, daemon=True).start()


def _periodic_scanner():
    """Background thread that runs scans every SCAN_INTERVAL_HOURS."""
    # Initial 90-second delay to let the app fully boot
    time.sleep(90)
    while True:
        try:
            print("[US Stability] Periodic scan starting...")
            run_stability_scan()
        except Exception as e:
            print(f"[US Stability] Periodic scan error: {str(e)[:200]}")
        time.sleep(SCAN_INTERVAL_HOURS * 3600)


def start_periodic_scanner():
    """Start the background periodic scanner thread."""
    t = threading.Thread(target=_periodic_scanner, daemon=True, name='us-stability-scanner')
    t.start()
    print(f"[US Stability] ✅ Periodic scanner started "
          f"(interval: {SCAN_INTERVAL_HOURS}h)")


def _nyse_scheduler():
    """Background thread that refreshes NYSE indices twice daily.

    Schedule (ET, approximate via UTC-4):
      - 7:00 AM ET  → quotes only (3 AV calls)
      - 7:00 PM ET  → quotes + sparklines (3 AV + 3 Yahoo calls)

    On boot, runs an initial fetch so the cache isn't empty for first-time visitors.
    """
    # Initial 120-second boot delay (stagger after main scanner)
    time.sleep(120)
    # Initial seed fetch so cache is warm on first deploy
    try:
        print("[NYSE Scheduler] Initial seed fetch (quotes + sparklines)")
        _refresh_nyse_data(refresh_sparklines=True)
    except Exception as e:
        print(f"[NYSE Scheduler] Initial seed error: {str(e)[:200]}")

    # Loop: check every 15 minutes if we're within the 7am or 7pm window
    last_morning_run = None
    last_evening_run = None
    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            et_hour = (now_utc.hour - 4) % 24    # UTC-4 approximation (DST most of year)
            today_str = now_utc.date().isoformat()

            # 7 AM ET window (any 15-min check between 7:00-7:14 ET)
            if et_hour == 7 and last_morning_run != today_str:
                print("[NYSE Scheduler] 7am ET — refreshing quotes (no sparklines)")
                _refresh_nyse_data(refresh_sparklines=False)
                last_morning_run = today_str

            # 7 PM ET window (any 15-min check between 19:00-19:14 ET)
            elif et_hour == 19 and last_evening_run != today_str:
                print("[NYSE Scheduler] 7pm ET — refreshing quotes + sparklines (EOD)")
                _refresh_nyse_data(refresh_sparklines=True)
                last_evening_run = today_str

        except Exception as e:
            print(f"[NYSE Scheduler] Loop error: {str(e)[:200]}")
        time.sleep(15 * 60)    # check every 15 minutes


def start_nyse_scheduler():
    """Start the NYSE twice-daily scheduler thread."""
    t = threading.Thread(target=_nyse_scheduler, daemon=True, name='us-nyse-scheduler')
    t.start()
    print(f"[NYSE Scheduler] ✅ Started — twice-daily refresh (7am + 7pm ET)")


# ============================================================
# FLASK ENDPOINT REGISTRATION
# ============================================================

def register_us_stability_endpoints(app):
    """Register all /api/us-stability endpoints."""
    from flask import jsonify, request

    @app.route('/api/us-stability', methods=['GET', 'OPTIONS'])
    def api_us_stability():
        if request.method == 'OPTIONS':
            return '', 200
        try:
            force = request.args.get('refresh', 'false').lower() == 'true'
            force_nyse = request.args.get('nyse', 'false').lower() == 'true'
            if force:
                _trigger_background_scan()
            if force_nyse:
                # Manual NYSE refresh — fire async so we don't block the response
                # Sparklines refresh only if it's after 4pm ET (avoid burning AV budget
                # on intraday sparkline pulls)
                now_utc = datetime.now(timezone.utc)
                et_hour = (now_utc.hour - 4) % 24
                refresh_spark = et_hour >= 16    # only after market close
                threading.Thread(
                    target=_refresh_nyse_data,
                    kwargs={'refresh_sparklines': refresh_spark},
                    daemon=True,
                    name='nyse-manual-refresh'
                ).start()
            data = get_stability_data(force_refresh=False)
            if not data:
                return jsonify({'success': False,
                                'error': 'No data — first scan in progress.'}), 503
            return jsonify(data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)[:200]}), 500

    @app.route('/api/us-stability/nyse', methods=['GET'])
    def api_us_stability_nyse():
        """Dedicated NYSE endpoint — cache-first, no AV calls on page loads.

        Pass ?force=true to manually trigger a refresh (sparklines only after 4pm ET).
        """
        try:
            force = request.args.get('force', 'false').lower() == 'true'
            if force:
                now_utc = datetime.now(timezone.utc)
                et_hour = (now_utc.hour - 4) % 24
                refresh_spark = et_hour >= 16
                data = _refresh_nyse_data(refresh_sparklines=refresh_spark)
            else:
                data = get_nyse_data(force_refresh=False)
            return jsonify(data or {'indices': {}, 'error': 'no data'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)[:200]}), 500

    @app.route('/api/us-stability/dimension/<dim_id>', methods=['GET'])
    def api_us_stability_dimension(dim_id):
        try:
            data = get_stability_data(force_refresh=False)
            if not data or dim_id not in data.get('dimensions', {}):
                return jsonify({'success': False,
                                'error': f'Dimension {dim_id} not found'}), 404
            return jsonify(data['dimensions'][dim_id])
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)[:200]}), 500

    @app.route('/api/us-stability/history', methods=['GET'])
    def api_us_stability_history():
        try:
            history = _redis_get(HISTORY_KEY) or {'snapshots': []}
            return jsonify(history)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)[:200]}), 500

    @app.route('/api/us-stability/debug', methods=['GET'])
    def api_us_stability_debug():
        cached = _redis_get(CACHE_KEY)
        history = _redis_get(HISTORY_KEY)
        fingerprint = _redis_get(FINGERPRINT_KEY)
        return jsonify({
            'version':                '1.0.0',
            'redis_configured':       bool(UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN),
            'newsapi_configured':     bool(NEWSAPI_KEY),
            'brave_configured':       bool(BRAVE_API_KEY),
            'econ_module_available':  ECON_AVAILABLE,
            'govt_module_available':  GOVT_AVAILABLE,
            'cache_present':          bool(cached),
            'cache_last_updated':     (cached or {}).get('last_updated'),
            'cache_composite_score':  (cached or {}).get('composite', {}).get('score'),
            'cache_articles_scanned': (cached or {}).get('articles_scanned'),
            'history_snapshots':      len((history or {}).get('snapshots', [])),
            'fingerprint_present':    bool(fingerprint),
            'fingerprint_data':       fingerprint,
            'dimension_weights':      DIMENSION_WEIGHTS,
            'rss_feed_count':         len(US_STABILITY_RSS),
            'scan_interval_hours':    SCAN_INTERVAL_HOURS,
        })

    print("[US Stability] ✅ Endpoints registered: /api/us-stability, "
          "/dimension/<id>, /history, /debug")


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == '__main__':
    """Self-test — runs synthetic test against fake articles."""
    print("\n" + "=" * 60)
    print("US STABILITY — SELF-TEST")
    print("=" * 60)

    # Test 1: Score-to-band mapping
    print("\n=== Test 1: Score-to-band mapping ===")
    for score in [10, 35, 55, 75, 95]:
        band = score_to_band(score)
        print(f"  Score {score:3} → {band['icon']} {band['label']} ({band['band']})")

    # Test 2: Economic indicator scoring
    print("\n=== Test 2: Economic indicator scoring ===")
    test_cases = [
        ('cpi_yoy',       2.0, 'Below Fed target'),
        ('cpi_yoy',       3.5, 'Stressed inflation'),
        ('cpi_yoy',       7.0, 'Crisis-level inflation'),
        ('unemployment',  3.5, 'Below 4%'),
        ('unemployment',  6.0, 'Fractured'),
        ('mortgage_30yr', 6.5, 'Mid-stressed'),
        ('mortgage_30yr', 9.0, 'Crisis-level'),
        ('gas_price',     3.50, 'Stressed'),
        ('gas_price',     5.50, 'Crisis'),
    ]
    for ind, val, label in test_cases:
        score = score_economic_indicator(ind, val)
        band = score_to_band(score) if score else None
        print(f"  {ind:18s} = {val:6} ({label:25s}) → score {score:3} {band['label'] if band else '?'}")

    # Test 3: Synthetic keyword detection
    print("\n=== Test 3: Synthetic keyword detection ===")
    test_articles = [
        {'title': 'Mass shooting at high school in Texas leaves multiple casualties',
         'description': 'Active shooter incident at Houston-area school',
         'source': 'AP', 'link': 'https://example.com/1'},
        {'title': 'Cabinet shakeup as Secretary of State resigns abruptly',
         'description': 'Acting secretary will fill role until nominee confirmed',
         'source': 'NPR', 'link': 'https://example.com/2'},
        {'title': 'Federal judge held in contempt as administration defied court order',
         'description': 'Judge ruled administration ignored ruling on immigration',
         'source': 'NYT', 'link': 'https://example.com/3'},
        {'title': 'Major ransomware attack on US healthcare system reported',
         'description': 'CISA issued emergency alert; hospitals across multiple states affected',
         'source': 'Reuters', 'link': 'https://example.com/4'},
        {'title': 'Thousands gathered for No Kings Movement protest in Washington',
         'description': 'Demonstration drew estimated 50,000 in DC and major cities',
         'source': 'WaPo', 'link': 'https://example.com/5'},
        {'title': 'Inspector General fired by White House — third in two months',
         'description': 'Whistleblower retaliation alleged by oversight groups',
         'source': 'Politico', 'link': 'https://example.com/6'},
    ]

    # Use unified-R baseline modifiers (current state)
    test_baseline_modifiers = {
        'cabinet_turnover_weight':         1.3,
        'agency_leadership_churn_weight':  1.3,
        'court_orders_defied_weight':      1.4,
        'partisan_deadlock_weight':        1.5,
        'inspector_general_dismissal':     1.4,
        'civil_service_purge_weight':      1.3,
    }

    pol = score_political_cohesion(test_articles, test_baseline_modifiers)
    civ = score_civil_social(test_articles, test_baseline_modifiers)
    dem = score_democratic_institutions(test_articles, test_baseline_modifiers)
    cyb = score_cyber_infrastructure(test_articles, test_baseline_modifiers)

    print(f"  Political Cohesion:        score {pol['score']:3} ({pol['band']['label']}) — "
          f"{pol['signals_detected']} signals detected")
    print(f"  Civil/Social:              score {civ['score']:3} ({civ['band']['label']}) — "
          f"{civ['signals_detected']} signals detected")
    print(f"  Democratic Institutions:   score {dem['score']:3} ({dem['band']['label']}) — "
          f"{dem['signals_detected']} signals detected")
    print(f"  Cyber/Infrastructure:      score {cyb['score']:3} ({cyb['band']['label']}) — "
          f"{cyb['signals_detected']} signals detected")

    print("\n  Top signals from Civil/Social:")
    for s in civ['top_signals'][:3]:
        print(f"    {s['icon']} [{s['level_name']}] {s['short_text']}")

    # Test 4: Composite scoring
    print("\n=== Test 4: Composite scoring ===")
    fake_dimensions = {
        'economic':                {'score': 55},
        'political_cohesion':      {'score': pol['score']},
        'civil_social':            {'score': civ['score']},
        'democratic_institutions': {'score': dem['score']},
        'military_posture':        {'score': 65},
        'cyber_infrastructure':    {'score': cyb['score']},
    }
    fake_cycle = {'stability_modifier': 1.15, 'phase': 'primary_season'}
    comp = compute_composite_score(fake_dimensions, fake_cycle)
    print(f"  Composite score:    {comp['score']} ({comp['band']['label']})")
    print(f"  Raw score:          {comp['raw_score']}")
    print(f"  Cycle modifier:     {comp['cycle_modifier']}x (primary_season)")
    print(f"  Band description:   {comp['band']['description']}")

    print("\n✅ SELF-TEST COMPLETE")
