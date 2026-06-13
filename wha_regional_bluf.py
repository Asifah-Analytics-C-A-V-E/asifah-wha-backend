"""
wha_regional_bluf.py
Asifah Analytics -- Western Hemisphere Backend Module
v1.0.0 -- April 2026

Western Hemisphere Regional BLUF (Bottom Line Up Front) Engine.

Reads from WHA rhetoric tracker Redis caches and synthesizes a single
analyst-prose BLUF paragraph + top-5 structured top-line signals.

Architecture mirrors me_regional_bluf.py v2.0 + asia_regional_bluf.py v2.1
(proven canonical pattern).

Currently active trackers:
  - Cuba (rhetoric:cuba:latest) -- 9-actor model with 3-vector frame

Roadmap (slot in via TRACKER_KEYS as they come online):
  - Venezuela (post-Maduro transition watch)
  - Haiti (state failure / migration cascade)
  - Mexico (cartel military ops)
  - Panama (Panama Canal rhetoric)
  - Colombia (FARC / ELN / cartel pressures)
  - Brazil (regional balance)
  - United States (anchor page; sovereign-domestic dual axis)

v1.0.0 design choices:
- Compatibility shim _normalize_tracker_data() supports both legacy trackers
  (so_what / red_lines top-level) AND v2.0+ trackers self-emitting top_signals[]
- Output emits canonical fields (top_signals, max_level, theatre_summary,
  region: 'western_hemisphere') for direct GPI consumption
- Top 5 signals per region (matches ME, Asia)
- WHA-specific cross-tracker signal: migration_cascade (Cuba+Haiti+Mexico+Venezuela
  outflow indicators converging) -- prepared but currently latent until 2+ trackers live
- Canonical signal categories: red_line_breached, theatre_high, us_pressure_high,
  regime_fracture, adversary_access, migration_surge, off_ramp_active

Author: RCGG / Asifah Analytics
"""

import os
import json
import traceback
from datetime import datetime, timezone
import requests


# ============================================================
# CONFIG
# ============================================================
UPSTASH_REDIS_URL   = os.environ.get('UPSTASH_REDIS_URL', '')
UPSTASH_REDIS_TOKEN = os.environ.get('UPSTASH_REDIS_TOKEN', '')

# Source caches (written by respective trackers)
TRACKER_KEYS = {
    'cuba':      'rhetoric:cuba:latest',
    'peru':      'rhetoric:peru:latest',
    'chile':     'rhetoric:chile:latest',
    'venezuela': 'rhetoric:venezuela:latest',  # v2.5 May 21 2026 — first contract-native tracker
    'us':        'rhetoric:us:latest',          # Jun 13 2026 — command-node anchor (writes rhetoric:us:latest, no TTL)
    # Future WHA trackers slot in here:
    # 'haiti':      'rhetoric:haiti:latest',
    # 'mexico':     'rhetoric:mexico:latest',
    # 'panama':     'rhetoric:panama:latest',
    # 'colombia':   'rhetoric:colombia:latest',
    # 'brazil':     'rhetoric:brazil:latest',
}

THEATRE_FLAGS = {
    'cuba':      '\U0001f1e8\U0001f1fa',  # 🇨🇺
    'peru':      '\U0001f1f5\U0001f1ea',  # 🇵🇪
    'chile':     '\U0001f1e8\U0001f1f1',  # 🇨🇱
    'venezuela': '\U0001f1fb\U0001f1ea',  # 🇻🇪
    'haiti':     '\U0001f1ed\U0001f1f9',  # 🇭🇹
    'mexico':    '\U0001f1f2\U0001f1fd',  # 🇲🇽
    'panama':    '\U0001f1f5\U0001f1e6',  # 🇵🇦
    'colombia':  '\U0001f1e8\U0001f1f4',  # 🇨🇴
    'brazil':    '\U0001f1e7\U0001f1f7',  # 🇧🇷
    'us':        '\U0001f1fa\U0001f1f8',  # 🇺🇸
}

THEATRE_DISPLAY = {
    'cuba':      'CUBA',
    'peru':      'PERU',
    'chile':     'CHILE',
    'venezuela': 'VENEZUELA',
    'haiti':     'HAITI',
    'mexico':    'MEXICO',
    'panama':    'PANAMA',
    'colombia':  'COLOMBIA',
    'brazil':    'BRAZIL',
    'us':        'UNITED STATES',
}

# Top-N signals emitted to GPI (matches ME / Asia pattern)
TOP_SIGNALS_COUNT = 12      # v2.4.0 May 21 2026 — bumped from 5; supports per-theatre quota
MAX_PER_THEATRE   = 3       # v2.4.0 May 21 2026 — per-tracker quota during selection

# Our synthesis cache
BLUF_CACHE_KEY    = 'rhetoric:wha:regional_bluf'
BLUF_CACHE_TTL    = 14 * 3600    # 14h -- outlasts any individual tracker TTL
BLUF_LASTGOOD_TTL   = 7 * 24 * 3600   # 7d ceiling for held last-known-good tracker snapshots (C)
BLUF_INCOMPLETE_TTL = 30 * 60         # 30min cache when the picture is incomplete (A: don't freeze gaps)

def _lastgood_key(theatre):
    """Durable last-known-good snapshot key for a tracker (C)."""
    return 'rhetoric:' + str(theatre) + ':lastgood'


# ============================================================
# ESCALATION + INFLUENCE LABELS (canonical across all regional BLUFs)
# ============================================================
ESCALATION_LABELS = {
    0: 'Monitoring',
    1: 'Rhetoric',
    2: 'Warning',
    3: 'Direct Threat',
    4: 'Incident',
    5: 'Active Conflict',
}

ESCALATION_COLORS = {
    0: '#6b7280',
    1: '#3b82f6',
    2: '#f59e0b',
    3: '#f97316',
    4: '#ef4444',
    5: '#dc2626',
}

# Forward-compat for future stability anchors (e.g., possible US dual-axis)
INFLUENCE_LABELS = {
    0: 'Standby',
    1: 'Engaged',
    2: 'Active',
    3: 'Mediation Engaged',
    4: 'High-Stakes Mediation',
    5: 'Crisis Mediation',
}

INFLUENCE_COLORS = {
    0: '#6b7280',
    1: '#a78bfa',
    2: '#8b5cf6',
    3: '#7c3aed',
    4: '#6d28d9',
    5: '#5b21b6',
}


# ============================================================
# REDIS HELPERS
# ============================================================
def _redis_get(key):
    if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
        return None
    try:
        resp = requests.get(
            f'{UPSTASH_REDIS_URL}/get/{key}',
            headers={'Authorization': f'Bearer {UPSTASH_REDIS_TOKEN}'},
            timeout=5
        )
        result = resp.json().get('result')
        return json.loads(result) if result else None
    except Exception as e:
        print(f'[WHA BLUF] Redis GET error ({key}): {e}')
        return None


def _redis_set(key, value, ttl=BLUF_CACHE_TTL):
    if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
        return False
    try:
        payload = json.dumps(value, default=str)
        params = {'EX': ttl} if ttl else {}
        resp = requests.post(
            f'{UPSTASH_REDIS_URL}/set/{key}',
            headers={
                'Authorization': f'Bearer {UPSTASH_REDIS_TOKEN}',
                'Content-Type': 'application/json'
            },
            data=payload,
            params=params,
            timeout=5
        )
        return resp.json().get('result') == 'OK'
    except Exception as e:
        print(f'[WHA BLUF] Redis SET error ({key}): {e}')
        return False


# ============================================================
# SAFE-ACCESS HELPERS (defensive)
# ============================================================
def _safe_dict(val):
    return val if isinstance(val, dict) else {}

def _safe_list(val):
    return val if isinstance(val, list) else []

def _safe_int(val, default=0):
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default

def _safe_str(val, default=''):
    return str(val) if val is not None else default


# ============================================================
# COMPATIBILITY SHIM -- v1.0 (mirrors ME / Asia v2.0+ pattern)
# ============================================================
def _normalize_tracker_data(theatre, raw_data):
    """
    Convert raw tracker cache into canonical shape regardless of version.
    """
    if not raw_data:
        return None

    flag = THEATRE_FLAGS.get(theatre, '')
    so_what    = _safe_dict(raw_data.get('so_what'))
    red_lines  = _safe_list(raw_data.get('red_lines'))

    # ---- THREAT LEVEL (Cuba uses 'theatre_level'; future trackers may differ) ----
    threat = _safe_int(raw_data.get('theatre_level',
                       raw_data.get('overall_level',
                       raw_data.get('threat_level', 0))))

    # ---- SCORE ----
    # Most trackers emit theatre_score (0-100); level-based trackers (e.g. Cuba's
    # 3-vector model) only emit theatre_level (0-5). Derive a 0-100 proxy by
    # multiplying level × 20 so the regional dashboard always has a usable score.
    score = _safe_int(raw_data.get('theatre_score',
                      raw_data.get('rhetoric_score',
                      raw_data.get('overall_score', 0))))
    if score == 0 and threat:
        score = int(threat) * 20

    # ---- INFLUENCE LEVEL (forward-ready; no current WHA tracker uses this) ----
    influence = raw_data.get('influence_level')

    # ---- DOMINANT AXIS ----
    threat_int    = int(threat or 0)
    influence_int = int(influence or 0)
    dominant_level = max(threat_int, influence_int)
    dominant_axis  = 'influence' if influence_int > threat_int else 'threat'

    # ---- TOP SIGNALS (v2.0+ self-emitted if present; else synthesize) ----
    if 'top_signals' in raw_data and isinstance(raw_data['top_signals'], list):
        top_signals = list(raw_data['top_signals'])
    else:
        top_signals = _synthesize_top_signals_legacy(
            theatre, raw_data, threat_int, score, so_what, red_lines
        )

    # ALWAYS augment with BLUF-level diplomatic signals (v3.2.0 — mirrors ME pattern).
    # WHA expansion roadmap: Venezuela has active diplomatic vectors (Maduro-opposition
    # talks, Norway/Mexico mediation, US sanctions negotiations). Cuba may eventually
    # have US re-engagement signals. This helper is forward-compatible — no-op when
    # trackers don't emit diplomatic_track yet, but new tracker emissions automatically
    # surface to GPI's diplomatic axis.
    diplomatic_sigs = _extract_diplomatic_signals(theatre, raw_data, threat_int)
    existing_categories = {s.get('category') for s in top_signals}
    for ds in diplomatic_sigs:
        if ds.get('category') not in existing_categories:
            top_signals.append(ds)

    return {
        'theatre':      theatre,
        'flag':         flag,
        'levels': {
            'threat':         threat_int,
            'influence':      influence_int if influence is not None else None,
            'green':          None,
            'dominant_axis':  dominant_axis,
            'dominant_level': dominant_level,
        },
        'score':        score,
        'so_what':      so_what,
        'red_lines':    red_lines,
        'top_signals':  top_signals,
        'scanned_at':   _safe_str(raw_data.get('scanned_at') or raw_data.get('timestamp', '')),
        'raw':          raw_data,
    }


def _extract_diplomatic_signals(theatre, raw_data, threat_int):
    """
    BLUF-level diplomatic signal extractor (v3.2.0 — mirrors ME pattern).

    Reads diplomatic_track + green_lines from a tracker's interpretation block.
    Forward-compatible no-op when trackers don't emit diplomatic data.

    WHA-specific note: Venezuela trackers (when added) will emit Maduro-opposition
    talks, Norway/Mexico mediation status, US-Venezuela sanctions negotiations.
    Cuba may emit US re-engagement signals. This helper surfaces them automatically.

    Returns list of signal dicts (possibly empty).
    """
    flag    = THEATRE_FLAGS.get(theatre, '')
    display = THEATRE_DISPLAY.get(theatre, theatre.upper())
    interp  = (raw_data.get('interpretation') or {}) if isinstance(raw_data.get('interpretation'), dict) else {}
    signals = []

    # Green lines / diplomatic de-escalation (UNGATED + dual-schema).
    green_lines = interp.get('green_lines') if interp else None
    if green_lines and isinstance(green_lines, dict):
        if 'count' in green_lines:
            gl_count = green_lines.get('count', 0)
        else:
            gl_count = green_lines.get('active_count', 0) + green_lines.get('signaled_count', 0)
        if gl_count >= 1:
            gl_priority = 6 + min(threat_int, 4)
            signals.append({
                'priority':       gl_priority,
                'category':       'green_line_active',
                'theatre':        theatre,
                'level':          min(threat_int, 4),
                'icon':           '✅',
                'color':          '#10b981',
                'pressure_type':  'diplomatic',
                'short_text':     f'{flag} {display}: De-escalation signals ({gl_count})',
                'long_text':      f'{flag} {display}: {gl_count} green-line de-escalation '
                                  f'trigger{"s" if gl_count != 1 else ""} active.',
            })

    # Diplomatic track — Venezuela mediation, Cuba re-engagement, etc.
    diplomatic_track = interp.get('diplomatic_track') if interp else None
    if diplomatic_track and isinstance(diplomatic_track, dict):
        active_count   = diplomatic_track.get('active_count', 0)
        signaled_count = diplomatic_track.get('signaled_count', 0)
        scenario       = diplomatic_track.get('scenario', '')
        score          = diplomatic_track.get('score', 0)
        if active_count + signaled_count > 0:
            dt_priority = 7 + min(threat_int, 4)
            short_status = 'ACTIVE' if active_count > 0 else 'SIGNALED'
            signals.append({
                'priority':       dt_priority,
                'category':       'diplomatic_track_active',
                'theatre':        theatre,
                'level':          min(threat_int, 4),
                'icon':           '🕊️',
                'color':          '#0ea5e9',
                'pressure_type':  'diplomatic',
                'short_text':     f'{flag} {display}: Diplomatic track {short_status} ({scenario[:40]})',
                'long_text':      f'{flag} {display} diplomatic track: {active_count} active + '
                                  f'{signaled_count} signaled off-ramp triggers (score {score}/100). '
                                  f'Scenario: {scenario}.',
                'diplomatic_active_count':   active_count,
                'diplomatic_signaled_count': signaled_count,
                'diplomatic_score':          score,
                'diplomatic_scenario':       scenario,
            })

    return signals


def _synthesize_top_signals_legacy(theatre, raw_data, threat_int, score, so_what, red_lines):
    """
    For trackers not yet upgraded to v2.0+. Synthesize top_signals[] from raw fields.
    """
    flag    = THEATRE_FLAGS.get(theatre, '')
    display = THEATRE_DISPLAY.get(theatre, theatre.upper())
    signals = []

    # Red lines breached
    for rl in red_lines:
        rl = _safe_dict(rl)
        status = _safe_str(rl.get('status'))
        label  = _safe_str(rl.get('label'))
        if status == 'BREACHED':
            signals.append({
                'priority':   12,
                'category':   'red_line_breached',
                'theatre':    theatre,
                'level':      threat_int,
                'icon':       rl.get('icon', '🚨'),
                'color':      '#dc2626',
                'short_text': f'{flag} {display}: BREACH — {label[:55]}',
                'long_text':  f'{flag} {display} red line breached at L{threat_int}: {label}.',
            })
        elif status == 'APPROACHING':
            signals.append({
                'priority':   8,
                'category':   'red_line_approaching',
                'theatre':    theatre,
                'level':      threat_int,
                'icon':       '🟠',
                'color':      '#f97316',
                'short_text': f'{flag} {display}: Approaching — {label[:50]}',
                'long_text':  f'{flag} {display} approaching red line: {label}.',
            })

    # Theatre at high level
    # L5 GATE (v1.1.0 — May 21 2026): Per platform L5 Reservation Contract,
    # L5 "Active Conflict" requires an explicit kinetic/humanitarian/economic/
    # diplomatic trigger. If tracker emits l5_gate dict, we honor its decision.
    # If tracker doesn't emit l5_gate (legacy trackers), we trust their level
    # as-is until they're upgraded per the weekend audit.
    # LABEL PRESERVATION: prefer tracker's own theatre_label + signal_text_short
    # if emitted. Falls back to ESCALATION_LABELS dict for legacy trackers.
    effective_level = threat_int
    l5_gate = raw_data.get('l5_gate')
    if threat_int >= 5 and isinstance(l5_gate, dict):
        # If tracker emits l5_gate, cap at L4 unless at least one axis gate is True
        if not any(l5_gate.get(axis) for axis in ('kinetic', 'humanitarian', 'economic', 'diplomatic')):
            effective_level = 4
            print(f"[WHA BLUF] L5 gate enforced: {theatre} capped at L4 "
                  f"(no l5_gate axes fired; tracker score {score})")

    if effective_level >= 4:
        # Prefer tracker's own label; fall back to canonical dict
        tracker_label = raw_data.get('theatre_label') or ESCALATION_LABELS.get(effective_level, '')
        signals.append({
            'priority':   9 + effective_level,
            'category':   'theatre_high',
            'theatre':    theatre,
            'level':      effective_level,
            'icon':       '🔴',
            'color':      ESCALATION_COLORS.get(effective_level, '#6b7280'),
            'short_text': raw_data.get('signal_text_short') or
                          f'{flag} {display} L{effective_level} — {tracker_label}',
            'long_text':  raw_data.get('signal_text_long') or
                          f'{flag} {display} at L{effective_level} {tracker_label} (score {score}/100)',
        })

    # CUBA-SPECIFIC vector signals (legacy fallback)
    if theatre == 'cuba':
        us_pressure      = _safe_int(so_what.get('us_pressure'))
        regime_fracture  = _safe_int(so_what.get('regime_fracture'))
        adversary_access = _safe_int(so_what.get('adversary_access'))

        if us_pressure >= 3:
            signals.append({
                'priority':   7 + us_pressure,
                'category':   'us_pressure_high',
                'theatre':    'cuba',
                'level':      us_pressure,
                'icon':       '🦅',
                'color':      '#f97316' if us_pressure < 4 else '#dc2626',
                'short_text': f'{flag} CUBA: U.S. pressure L{us_pressure}',
                'long_text':  f'CUBA U.S. pressure vector L{us_pressure} — sanctions/coercion language elevated.',
            })
        if regime_fracture >= 3:
            signals.append({
                'priority':   7 + regime_fracture,
                'category':   'regime_fracture',
                'theatre':    'cuba',
                'level':      regime_fracture,
                'icon':       '✊',
                'color':      '#f97316' if regime_fracture < 4 else '#dc2626',
                'short_text': f'{flag} CUBA: Regime fracture L{regime_fracture}',
                'long_text':  f'CUBA regime fracture L{regime_fracture} — dissident activity vs. baseline elevated.',
            })
        if adversary_access >= 3:
            signals.append({
                'priority':   8 + adversary_access,
                'category':   'adversary_access',
                'theatre':    'cuba',
                'level':      adversary_access,
                'icon':       '🤝',
                'color':      '#7c3aed' if adversary_access < 4 else '#dc2626',
                'short_text': f'{flag} CUBA: Adversary access L{adversary_access}',
                'long_text':  f'CUBA adversary access L{adversary_access} — RU/CN/IR axis activity detected.',
            })

    # PERU-SPECIFIC vector signals (4-vector frame)
    # Peru emits vector_levels {domestic_stability, resource_sector, us_alignment, china_alignment}
    # Map level strings to integers for BLUF priority math, then surface escalatory vectors.
    if theatre == 'peru':
        VECTOR_LVL_INT = {'low': 0, 'normal': 1, 'elevated': 2, 'high': 3, 'surge': 4}
        vector_levels  = _safe_dict(raw_data.get('vector_levels'))

        domestic_lvl = VECTOR_LVL_INT.get(vector_levels.get('domestic_stability'), 0)
        resource_lvl = VECTOR_LVL_INT.get(vector_levels.get('resource_sector'),   0)
        us_lvl       = VECTOR_LVL_INT.get(vector_levels.get('us_alignment'),      0)
        china_lvl    = VECTOR_LVL_INT.get(vector_levels.get('china_alignment'),   0)

        if domestic_lvl >= 2:   # elevated+
            signals.append({
                'priority':   7 + domestic_lvl,
                'category':   'peru_domestic_stability',
                'theatre':    'peru',
                'level':      domestic_lvl,
                'icon':       '🏛️',
                'color':      '#f59e0b' if domestic_lvl < 3 else '#dc2626',
                'short_text': f'{flag} PERU: Domestic stability L{domestic_lvl}',
                'long_text':  f'PERU domestic-stability vector L{domestic_lvl} — presidency / FFAA / VRAEM / Las Bambas channels signaling above baseline.',
            })

        if resource_lvl >= 2:
            signals.append({
                'priority':   8 + resource_lvl,   # resource ranks slightly higher (commodity coupling)
                'category':   'peru_resource_sector',
                'theatre':    'peru',
                'level':      resource_lvl,
                'icon':       '⛏️',
                'color':      '#f59e0b' if resource_lvl < 3 else '#dc2626',
                'short_text': f'{flag} PERU: Resource sector L{resource_lvl}',
                'long_text':  f'PERU resource-sector vector L{resource_lvl} — mining-sector + Las Bambas rhetoric coupled to global copper / silver supply.',
            })

        if us_lvl >= 2:
            signals.append({
                'priority':   6 + us_lvl,
                'category':   'peru_us_alignment',
                'theatre':    'peru',
                'level':      us_lvl,
                'icon':       '🦅',
                'color':      '#3b82f6' if us_lvl < 3 else '#dc2626',
                'short_text': f'{flag} PERU: U.S. alignment L{us_lvl}',
                'long_text':  f'PERU U.S.-alignment vector L{us_lvl} — Embassy Lima / INL / SOUTHCOM / FTA channel activity above baseline.',
            })

        if china_lvl >= 2:
            signals.append({
                'priority':   7 + china_lvl,
                'category':   'peru_china_alignment',
                'theatre':    'peru',
                'level':      china_lvl,
                'icon':       '🚢',
                'color':      '#dc2626' if china_lvl >= 3 else '#f59e0b',
                'short_text': f'{flag} PERU: China alignment L{china_lvl}',
                'long_text':  f'PERU China-alignment vector L{china_lvl} — Chancay megaport / BRI / Chinese mining-investment activity above baseline.',
            })

    # CHILE-SPECIFIC vector signals (4-vector frame, mirrors Peru pattern)
    # Chile-specific framing: copper #1 + lithium #2 globally; Mapuche conflict
    # replaces VRAEM; constitutional politics replaces FFAA; cautious China posture
    # (no Chancay-equivalent flagship — lithium dependency is structural).
    if theatre == 'chile':
        VECTOR_LVL_INT = {'low': 0, 'normal': 1, 'elevated': 2, 'high': 3, 'surge': 4}
        vector_levels  = _safe_dict(raw_data.get('vector_levels'))

        domestic_lvl = VECTOR_LVL_INT.get(vector_levels.get('domestic_stability'), 0)
        resource_lvl = VECTOR_LVL_INT.get(vector_levels.get('resource_sector'),   0)
        us_lvl       = VECTOR_LVL_INT.get(vector_levels.get('us_alignment'),      0)
        china_lvl    = VECTOR_LVL_INT.get(vector_levels.get('china_alignment'),   0)

        if domestic_lvl >= 2:
            signals.append({
                'priority':   7 + domestic_lvl,
                'category':   'chile_domestic_stability',
                'theatre':    'chile',
                'level':      domestic_lvl,
                'icon':       '🏛️',
                'color':      '#f59e0b' if domestic_lvl < 3 else '#dc2626',
                'short_text': f'{flag} CHILE: Domestic stability L{domestic_lvl}',
                'long_text':  f'CHILE domestic-stability vector L{domestic_lvl} — presidency / Mapuche conflict / constitutional-politics channels signaling above baseline.',
            })

        if resource_lvl >= 2:
            signals.append({
                'priority':   8 + resource_lvl,
                'category':   'chile_resource_sector',
                'theatre':    'chile',
                'level':      resource_lvl,
                'icon':       '⛏️',
                'color':      '#f59e0b' if resource_lvl < 3 else '#dc2626',
                'short_text': f'{flag} CHILE: Resource sector L{resource_lvl}',
                'long_text':  f'CHILE resource-sector vector L{resource_lvl} — Codelco / Escondida / SQM / Albemarle rhetoric coupled to global copper (#1) + lithium (#2) supply.',
            })

        if us_lvl >= 2:
            signals.append({
                'priority':   6 + us_lvl,
                'category':   'chile_us_alignment',
                'theatre':    'chile',
                'level':      us_lvl,
                'icon':       '🦅',
                'color':      '#3b82f6' if us_lvl < 3 else '#dc2626',
                'short_text': f'{flag} CHILE: U.S. alignment L{us_lvl}',
                'long_text':  f'CHILE U.S.-alignment vector L{us_lvl} — Embassy Santiago / SOUTHCOM / strategic-minerals dialog / FTA activity above baseline.',
            })

        if china_lvl >= 2:
            signals.append({
                'priority':   7 + china_lvl,
                'category':   'chile_china_alignment',
                'theatre':    'chile',
                'level':      china_lvl,
                'icon':       '🐉',
                'color':      '#dc2626' if china_lvl >= 3 else '#f59e0b',
                'short_text': f'{flag} CHILE: China alignment L{china_lvl}',
                'long_text':  f'CHILE China-alignment vector L{china_lvl} — Tianqi-SQM / BYD-Maricunga / Ganfeng-Codelco / FTA channel activity above baseline.',
            })

    signals.sort(key=lambda s: s['priority'], reverse=True)
    return signals


# ============================================================
# TRACKER READERS
# ============================================================
def _read_all_trackers():
    """Read all WHA tracker caches and normalize via shim.

    Cold-start resilience (Jun 13 2026 -- A/B/C):
      C: when a tracker's live cache is missing, fall back to a durable
         last-known-good snapshot (rhetoric:<x>:lastgood, 7d ceiling) so the
         country is HELD in the rollup rather than silently dropped.
      B: report which trackers are live / stale-fallback / fully absent.
    Returns (trackers, missing, stale).
    """
    trackers = {}
    missing  = []   # no live AND no last-known-good -> truly absent (honest)
    stale    = []   # served from last-known-good fallback
    for theatre, redis_key in TRACKER_KEYS.items():
        raw = _redis_get(redis_key)
        if raw:
            normalized = _normalize_tracker_data(theatre, raw)
            if normalized:
                normalized['freshness'] = 'live'
                trackers[theatre] = normalized
                _redis_set(_lastgood_key(theatre), raw, ttl=BLUF_LASTGOOD_TTL)
                lvls = normalized['levels']
                axis_str = (f"T{lvls['threat']}" +
                            (f"/I{lvls['influence']}" if lvls['influence'] is not None else ''))
                print(f'[WHA BLUF] {theatre}: loaded ({axis_str}, score={normalized["score"]})')
                continue
        lg = _redis_get(_lastgood_key(theatre))
        if lg:
            normalized = _normalize_tracker_data(theatre, lg)
            if normalized:
                normalized['freshness'] = 'stale'
                trackers[theatre] = normalized
                stale.append(theatre)
                print(f'[WHA BLUF] {theatre}: STALE fallback (last-known-good held)')
                continue
        missing.append(theatre)
        print(f'[WHA BLUF] {theatre}: no cache available (absent from rollup)')
    return trackers, missing, stale


# ============================================================
# REGIONAL POSTURE
# ============================================================
def _determine_regional_posture(trackers):
    """
    Roll up posture across all WHA trackers.
    """
    if not trackers:
        return {
            'label':            'BASELINE',
            'color':            '#6b7280',
            'peak_level':       0,
            'breached_count':   0,
            'theatres_at_l3plus': 0,
        }

    levels = [t['levels']['threat'] for t in trackers.values()]
    max_level = max(levels) if levels else 0

    # Count breached red lines across all trackers
    total_breached = 0
    for data in trackers.values():
        for rl in data.get('red_lines', []) or []:
            if isinstance(rl, dict) and rl.get('status') == 'BREACHED':
                total_breached += 1

    theatres_at_l3plus = sum(1 for l in levels if l >= 3)

    # Posture ladder
    if total_breached >= 2 or max_level >= 5:
        label, color = 'CRITICAL -- MULTI-BREACH OR ACTIVE CONFLICT', '#dc2626'
    elif total_breached >= 1 or max_level >= 4:
        label, color = 'ELEVATED -- RED LINE OR INCIDENT', '#ef4444'
    elif theatres_at_l3plus >= 2:
        label, color = 'ELEVATED -- MULTI-COUNTRY WARNING', '#f97316'
    elif max_level >= 3:
        label, color = 'WARNING -- DIRECT THREAT', '#f59e0b'
    elif max_level >= 2:
        label, color = 'MONITORING -- WARNING', '#fbbf24'
    elif max_level >= 1:
        label, color = 'MONITORING -- RHETORIC', '#3b82f6'
    else:
        label, color = 'BASELINE', '#6b7280'

    return {
        'label':              label,
        'color':              color,
        'peak_level':         max_level,
        'breached_count':     total_breached,
        'theatres_at_l3plus': theatres_at_l3plus,
    }


# ============================================================
# BLUF PROSE
# ============================================================
def _build_bluf_prose(posture, trackers):
    """Generate regional prose paragraph. 2-4 sentences."""
    date_str = datetime.now(timezone.utc).strftime('%b %d, %Y')
    parts = [f"Western Hemisphere Rhetoric Monitor ({date_str}):"]

    n_live = len(trackers)
    parts.append(
        f"Regional posture at {posture['label']} -- peak escalation L{posture['peak_level']} "
        f"across {n_live} live tracker{'s' if n_live != 1 else ''}."
    )

    # Per-tracker callouts (only for elevated theaters)
    for theatre, data in trackers.items():
        threat   = data['levels']['threat']
        so_what  = data.get('so_what', {})
        display  = THEATRE_DISPLAY.get(theatre, theatre.upper())

        if theatre == 'cuba' and threat >= 2:
            us_pressure      = _safe_int(so_what.get('us_pressure'))
            regime_fracture  = _safe_int(so_what.get('regime_fracture'))
            adversary_access = _safe_int(so_what.get('adversary_access'))
            scenario         = _safe_str(so_what.get('scenario'))
            cuba_desc = f"{display} composite L{threat}"
            vector_phrases = []
            if us_pressure >= 3:
                vector_phrases.append(f"U.S. pressure L{us_pressure}")
            if regime_fracture >= 3:
                vector_phrases.append(f"regime fracture L{regime_fracture}")
            if adversary_access >= 3:
                vector_phrases.append(f"adversary axis L{adversary_access}")
            if vector_phrases:
                cuba_desc += " — " + ", ".join(vector_phrases) + "."
            elif scenario:
                cuba_desc += f" — {scenario}."
            else:
                cuba_desc += " — composite pressure elevated."
            parts.append(cuba_desc)
        elif theatre == 'peru' and threat >= 2:
            # Peru uses 4-vector frame: domestic_stability, resource_sector, us_alignment, china_alignment
            VECTOR_LVL_INT = {'low': 0, 'normal': 1, 'elevated': 2, 'high': 3, 'surge': 4}
            raw           = data.get('raw', {}) or {}
            vector_levels = raw.get('vector_levels', {}) or {}
            domestic_lvl = VECTOR_LVL_INT.get(vector_levels.get('domestic_stability'), 0)
            resource_lvl = VECTOR_LVL_INT.get(vector_levels.get('resource_sector'),   0)
            us_lvl       = VECTOR_LVL_INT.get(vector_levels.get('us_alignment'),      0)
            china_lvl    = VECTOR_LVL_INT.get(vector_levels.get('china_alignment'),   0)

            peru_desc = f"{display} composite L{threat}"
            vector_phrases = []
            if domestic_lvl >= 2:
                vector_phrases.append(f"domestic stability L{domestic_lvl}")
            if resource_lvl >= 2:
                vector_phrases.append(f"resource sector L{resource_lvl}")
            if us_lvl >= 2:
                vector_phrases.append(f"U.S. alignment L{us_lvl}")
            if china_lvl >= 2:
                vector_phrases.append(f"China alignment L{china_lvl}")
            if vector_phrases:
                peru_desc += " — " + ", ".join(vector_phrases) + "."
            else:
                peru_desc += " — composite pressure elevated."
            parts.append(peru_desc)
        elif theatre == 'chile' and threat >= 2:
            # Chile uses 4-vector frame: domestic_stability, resource_sector, us_alignment, china_alignment
            # (Same shape as Peru — vector phrasing identical; domain context differs)
            VECTOR_LVL_INT = {'low': 0, 'normal': 1, 'elevated': 2, 'high': 3, 'surge': 4}
            raw           = data.get('raw', {}) or {}
            vector_levels = raw.get('vector_levels', {}) or {}
            domestic_lvl = VECTOR_LVL_INT.get(vector_levels.get('domestic_stability'), 0)
            resource_lvl = VECTOR_LVL_INT.get(vector_levels.get('resource_sector'),   0)
            us_lvl       = VECTOR_LVL_INT.get(vector_levels.get('us_alignment'),      0)
            china_lvl    = VECTOR_LVL_INT.get(vector_levels.get('china_alignment'),   0)

            chile_desc = f"{display} composite L{threat}"
            vector_phrases = []
            if domestic_lvl >= 2:
                vector_phrases.append(f"domestic stability L{domestic_lvl}")
            if resource_lvl >= 2:
                vector_phrases.append(f"resource sector L{resource_lvl}")
            if us_lvl >= 2:
                vector_phrases.append(f"U.S. alignment L{us_lvl}")
            if china_lvl >= 2:
                vector_phrases.append(f"China alignment L{china_lvl}")
            if vector_phrases:
                chile_desc += " — " + ", ".join(vector_phrases) + "."
            else:
                chile_desc += " — composite pressure elevated."
            parts.append(chile_desc)
        elif theatre == 'venezuela' and threat >= 2:
            # VZ uses 6-vector frame (v1.0.0 May 21 2026) — first contract-native tracker:
            #   us_pressure, regime_legitimacy, adversary_access, oil_extraction,
            #   migration_outflow, essequibo_dispute
            # PLUS ceasefire-aware kinetic gate via US-VZ détente (active = L5 suppressor).
            # VZ emits its own theatre_label/band ("Pressure Peak" at L4, "Active Crisis" at L5
            # under canonical bands STABLE/ACTIVE/VOLATILE/CRISIS).
            raw            = data.get('raw', {}) or {}
            vectors        = raw.get('vectors', {}) or {}
            l5_gate        = raw.get('l5_gate', {}) or {}
            diplomatic_lvl = _safe_int(raw.get('diplomatic_level'))

            us_pres_lvl    = _safe_int(vectors.get('us_pressure'))
            regime_lvl     = _safe_int(vectors.get('regime_legitimacy'))
            adversary_lvl  = _safe_int(vectors.get('adversary_access'))
            oil_lvl        = _safe_int(vectors.get('oil_extraction'))
            migration_lvl  = _safe_int(vectors.get('migration_outflow'))
            essequibo_lvl  = _safe_int(vectors.get('essequibo_dispute'))

            vz_desc = f"{display} composite L{threat}"
            vector_phrases = []
            if us_pres_lvl >= 2:
                vector_phrases.append(f"U.S. pressure L{us_pres_lvl}")
            if regime_lvl >= 2:
                vector_phrases.append(f"regime legitimacy L{regime_lvl}")
            if adversary_lvl >= 2:
                vector_phrases.append(f"adversary access L{adversary_lvl}")
            if oil_lvl >= 2:
                vector_phrases.append(f"oil sector L{oil_lvl}")
            if migration_lvl >= 2:
                vector_phrases.append(f"migration outflow L{migration_lvl}")
            if essequibo_lvl >= 3:
                vector_phrases.append(f"Essequibo L{essequibo_lvl}")
            if vector_phrases:
                vz_desc += " — " + ", ".join(vector_phrases) + "."
            else:
                vz_desc += " — composite pressure elevated."

            # Surface US-VZ détente status when active (acts as kinetic L5 suppressor)
            if diplomatic_lvl >= 3:
                vz_desc += f" US-VZ détente active (L{diplomatic_lvl}, de-escalator)."
            # Surface ceasefire suppression if applicable
            suppressed = l5_gate.get('l5_ceasefire_suppressed_sources') if isinstance(l5_gate, dict) else None
            if suppressed:
                vz_desc += " ⚠️ Underlying L5 pressure suppressed by détente."

            parts.append(vz_desc)
        elif threat >= 3:
            # Generic treatment for other future trackers
            parts.append(f"{display} L{threat} — {ESCALATION_LABELS.get(threat, 'elevated')}.")

    # Cascade flag
    if posture['theatres_at_l3plus'] >= 2:
        parts.append(
            f"⚠️ {posture['theatres_at_l3plus']} theaters at L3+ simultaneously -- "
            f"WHA cascade risk: migration, sanctions, and adversary access vectors converging."
        )
    elif posture['breached_count'] >= 1:
        parts.append(
            f"{posture['breached_count']} red line(s) breached across WHA trackers -- "
            f"adjacent categories warrant elevated monitoring."
        )

    return ' '.join(parts)


# ════════════════════════════════════════════════════════════════════════
# BLUF PROSE v2 — Human-language regional analytical summary
# Added: May 22 2026
# ────────────────────────────────────────────────────────────────────────
# Design goals (per editorial decisions May 22 2026 session):
#   Q1: Lead with regional posture, then dive into most-volatile theater
#   Q2: Pull each tracker's so_what.factor into the prose (best signal)
#   Q3: Add directional language ("up from L3 last cycle") via history reads
#
# Data contract (May 22 2026 reconciled schema):
#   Each tracker writes 4 canonical fields to {tracker}:history Redis list:
#     theatre_level, theatre_score, scanned_at, red_lines_count
#   + tracker-specific vector levels (read by prose_v2 only when present)
#
# Graceful degradation:
#   - Tracker has no history -> no direction language for that tracker
#   - Tracker missing so_what.factor -> falls back to vector enumeration
#   - All trackers missing data -> emits "data not available" version
#
# Reusability:
#   This block is portable to me_regional_bluf, asia_regional_bluf,
#   europe_regional_bluf with only theatre-name lookups customized.
# ════════════════════════════════════════════════════════════════════════

# Theatre-display names for prose (proper-noun capitalization).
THEATRE_DISPLAY_NAMES = {
    'cuba':      'Cuba',
    'peru':      'Peru',
    'chile':     'Chile',
    'venezuela': 'Venezuela',
    'haiti':     'Haiti',
    'mexico':    'Mexico',
    'panama':    'Panama',
    'colombia':  'Colombia',
    'brazil':    'Brazil',
    'us':        'the United States',
}


def _read_history_snapshot(theatre, depth=3):
    """
    Read the last N history snapshots for a theatre from Redis.

    Returns a list of snapshot dicts (most recent first), or [] on miss/error.
    Each snapshot is guaranteed to be a dict with at least 'theatre_level' if
    the tracker is on the canonical (May 22 2026) schema.
    """
    if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
        return []
    history_key = f'rhetoric:{theatre}:history'
    try:
        # LRANGE 0..depth-1 returns most recent snapshots first
        url = f"{UPSTASH_REDIS_URL}/lrange/{history_key}/0/{depth - 1}"
        resp = requests.get(
            url,
            headers={'Authorization': f'Bearer {UPSTASH_REDIS_TOKEN}'},
            timeout=5,
        )
        if resp.status_code != 200:
            return []
        result = resp.json().get('result', [])
        snapshots = []
        for entry in result or []:
            try:
                snap = json.loads(entry) if isinstance(entry, str) else entry
                if isinstance(snap, dict):
                    snapshots.append(snap)
            except (json.JSONDecodeError, TypeError):
                continue
        return snapshots
    except Exception as e:
        print(f"[WHA BLUF v2] History read error for {theatre}: {str(e)[:120]}")
        return []


def _compute_direction(current_level, history_snapshots):
    """
    Compare current theatre_level vs. the previous snapshot's level.

    Returns dict with:
        direction: 'up' | 'down' | 'steady' | 'first_scan' | 'no_history'
        delta:     int (current - previous)
        previous:  int previous level (or None)
        phrase:    short human phrase for inline prose
    """
    if not history_snapshots:
        return {'direction': 'no_history', 'delta': 0, 'previous': None, 'phrase': ''}

    # Snapshots are stored most-recent-first via LPUSH.
    # Index 0 IS the current scan, index 1 is the previous one.
    if len(history_snapshots) < 2:
        return {'direction': 'first_scan', 'delta': 0, 'previous': None, 'phrase': ''}

    previous = history_snapshots[1]
    prev_level = previous.get('theatre_level')
    if prev_level is None:
        return {'direction': 'no_history', 'delta': 0, 'previous': None, 'phrase': ''}

    delta = current_level - prev_level

    if delta > 0:
        return {'direction': 'up', 'delta': delta, 'previous': prev_level,
                'phrase': f'up from L{prev_level} last cycle'}
    elif delta < 0:
        return {'direction': 'down', 'delta': delta, 'previous': prev_level,
                'phrase': f'down from L{prev_level} last cycle'}
    else:
        return {'direction': 'steady', 'delta': 0, 'previous': prev_level,
                'phrase': f'steady at L{current_level}'}


def _extract_so_what_phrase(raw_data):
    """
    Pull a short analytical phrase from a tracker's so_what dict.

    Normalizes 3 different so_what shapes:
        - {factor, scenario, description, watch_for}  (VZ/Peru/Chile)
        - {scenario, ...}                              (Cuba legacy)
        - missing -> return ''
    """
    if not isinstance(raw_data, dict):
        return ''
    so_what = raw_data.get('so_what')
    if not isinstance(so_what, dict):
        return ''

    factor = so_what.get('factor')
    if factor and isinstance(factor, str) and factor.strip():
        return factor.strip()

    scenario = so_what.get('scenario')
    if scenario and isinstance(scenario, str) and scenario.strip():
        # snake_case -> readable
        return scenario.replace('_', ' ').strip()

    return ''


def _extract_active_vectors(raw_data, threshold=2):
    """
    Return vector-level fields at or above threshold as (display_name, level) tuples.

    Normalizes 3 different vector shapes:
        - VZ:    raw['vectors'] = {us_pressure: 3, ...}                   (int)
        - Peru:  raw['vector_levels'] = {'domestic_stability': 'high', ...} (string)
        - Chile: raw['vector_levels'] = {...}                              (string)
        - Cuba:  raw['us_pressure'] = 3 (flat top-level)                   (int)
    """
    if not isinstance(raw_data, dict):
        return []

    VECTOR_LVL_INT = {'low': 0, 'normal': 1, 'elevated': 2, 'high': 3, 'surge': 4}

    VECTOR_DISPLAY = {
        'us_pressure':         'U.S. pressure',
        'regime_legitimacy':   'regime legitimacy',
        'regime_fracture':     'regime fracture',
        'adversary_access':    'adversary access',
        'oil_extraction':      'oil sector',
        'migration_outflow':   'migration outflow',
        'essequibo_dispute':   'Essequibo dispute',
        'domestic_stability':  'domestic stability',
        'resource_sector':     'resource sector',
        'us_alignment':        'U.S. alignment',
        'china_alignment':     'China alignment',
    }

    active = []

    # VZ pattern (raw.vectors, int values)
    vectors = raw_data.get('vectors')
    if isinstance(vectors, dict):
        for key, val in vectors.items():
            try:
                lvl = int(val)
                if lvl >= threshold:
                    active.append((VECTOR_DISPLAY.get(key, key.replace('_', ' ')), lvl))
            except (ValueError, TypeError):
                continue
        return sorted(active, key=lambda x: -x[1])

    # Peru/Chile pattern (raw.vector_levels, string OR int)
    vector_levels = raw_data.get('vector_levels')
    if isinstance(vector_levels, dict):
        for key, val in vector_levels.items():
            if isinstance(val, str):
                lvl = VECTOR_LVL_INT.get(val, 0)
            elif isinstance(val, int):
                lvl = val
            else:
                lvl = 0
            if lvl >= threshold:
                active.append((VECTOR_DISPLAY.get(key, key.replace('_', ' ')), lvl))
        return sorted(active, key=lambda x: -x[1])

    # Cuba pattern (flat top-level)
    for key in ['us_pressure', 'regime_fracture', 'adversary_access']:
        val = raw_data.get(key)
        try:
            lvl = int(val) if val is not None else 0
            if lvl >= threshold:
                active.append((VECTOR_DISPLAY.get(key, key.replace('_', ' ')), lvl))
        except (ValueError, TypeError):
            continue
    return sorted(active, key=lambda x: -x[1])


def _build_bluf_prose_v2(posture, trackers):
    """
    BLUF prose v2 — human-language regional analytical summary.

    Structure (per editorial decisions May 22 2026):
        Para 1: Regional posture headline + theater count + most-volatile theater dive
                with so_what.factor + active vectors + directional language
        Para 2: Soft-name the other elevated theaters (L2+) with brief factor
        Para 3: Cascade closer

    Graceful degradation: missing data fields adapt the prose, never error.
    """
    if not trackers:
        return ('Western Hemisphere Rhetoric Monitor: no live tracker data '
                'available at this scan. BLUF will populate as trackers come online.')

    today = datetime.now(timezone.utc).strftime('%B %d, %Y')
    posture_label = posture.get('label', 'BASELINE')
    peak_level = posture.get('peak_level', 0)
    theatres_at_l3plus = posture.get('theatres_at_l3plus', 0)
    breached = posture.get('breached_count', 0)

    # Sort trackers by threat level descending (most-volatile first)
    sorted_theatres = sorted(
        trackers.items(),
        key=lambda kv: -kv[1].get('levels', {}).get('threat', 0),
    )

    # ════════ PARA 1: Posture + most-volatile theater dive ════════
    para1_parts = [f"**Western Hemisphere -- {today}**"]

    n_live = len(trackers)
    if theatres_at_l3plus >= 2:
        posture_sentence = (
            f"Regional posture at {posture_label}, with {theatres_at_l3plus} theaters "
            f"at L3 or higher simultaneously across {n_live} live trackers."
        )
    elif peak_level >= 3:
        posture_sentence = (
            f"Regional posture at {posture_label}, with peak escalation L{peak_level} "
            f"across {n_live} live trackers."
        )
    else:
        posture_sentence = (
            f"Regional posture at {posture_label} -- {n_live} live trackers, "
            f"peak L{peak_level} (baseline range)."
        )
    if breached >= 1:
        posture_sentence += f" {breached} red line{'s' if breached > 1 else ''} breached."

    para1_parts.append(posture_sentence)

    # Dive into top theater
    top_theatre, top_data = sorted_theatres[0]
    top_level = top_data.get('levels', {}).get('threat', 0)
    top_name = THEATRE_DISPLAY_NAMES.get(top_theatre, top_theatre.title())
    top_raw = top_data.get('raw', {}) or {}

    top_history = _read_history_snapshot(top_theatre, depth=3)
    top_direction = _compute_direction(top_level, top_history)
    top_factor = _extract_so_what_phrase(top_raw)
    top_vectors = _extract_active_vectors(top_raw, threshold=2)

    if top_level >= 3:
        dive = f"The most volatile theater is **{top_name}** (composite L{top_level}"
        if top_direction.get('phrase'):
            dive += f", {top_direction['phrase']}"
        dive += ")"
        if top_factor:
            dive += f" -- analytical read: {top_factor}."
        else:
            dive += "."
        if top_vectors:
            top_3 = top_vectors[:3]
            vec_phrases = [f"{name} L{lvl}" for name, lvl in top_3]
            dive += f" Active vectors: {', '.join(vec_phrases)}."
        para1_parts.append(dive)
    elif top_level >= 1:
        dive = f"Highest tracker is **{top_name}** at L{top_level}"
        if top_direction.get('phrase'):
            dive += f" ({top_direction['phrase']})"
        if top_factor:
            dive += f" -- {top_factor}."
        else:
            dive += "."
        para1_parts.append(dive)

    # ════════ PARA 2: Other elevated theaters + baselines ════════
    para2_parts = []
    other_elevated = [
        (t, d) for t, d in sorted_theatres[1:]
        if d.get('levels', {}).get('threat', 0) >= 2
    ]
    baseline_theatres = [
        t for t, d in sorted_theatres[1:]
        if d.get('levels', {}).get('threat', 0) < 2
    ]

    for theatre, data in other_elevated:
        level = data.get('levels', {}).get('threat', 0)
        name = THEATRE_DISPLAY_NAMES.get(theatre, theatre.title())
        raw = data.get('raw', {}) or {}
        history = _read_history_snapshot(theatre, depth=3)
        direction = _compute_direction(level, history)
        factor = _extract_so_what_phrase(raw)

        sent = f"**{name}** registers L{level}"
        if direction.get('phrase'):
            sent += f" ({direction['phrase']})"
        if factor:
            sent += f" -- {factor}."
        else:
            vecs = _extract_active_vectors(raw, threshold=2)
            if vecs:
                sent += f" -- {vecs[0][0]} elevated at L{vecs[0][1]}."
            else:
                sent += "."
        para2_parts.append(sent)

    if baseline_theatres:
        names = [THEATRE_DISPLAY_NAMES.get(t, t.title()) for t in baseline_theatres]
        if len(names) == 1:
            para2_parts.append(f"{names[0]} remains at baseline.")
        elif len(names) == 2:
            para2_parts.append(f"{names[0]} and {names[1]} remain at baseline.")
        else:
            para2_parts.append(f"{', '.join(names[:-1])}, and {names[-1]} remain at baseline.")

    # ════════ PARA 3: Cascade closer ════════
    para3_parts = []
    if theatres_at_l3plus >= 3:
        para3_parts.append(
            f"**Why this matters:** {theatres_at_l3plus} simultaneous L3+ theaters in the "
            "Western Hemisphere is a structurally rare convergence. Concrete cascade risks "
            "across migration corridors, sanctions-evasion routes (oil/gold/wheat), and "
            "adversary-access vectors (Russia/China/Iran) are now active simultaneously."
        )
    elif theatres_at_l3plus == 2:
        para3_parts.append(
            "**Why this matters:** Two simultaneous L3+ theaters create real migration and "
            "sanctions cascade risk. Monitor for adversary-axis amplification."
        )
    elif peak_level >= 4:
        para3_parts.append(
            "**Why this matters:** A single L4+ theater is the floor for cross-region cascade "
            "concerns -- particularly when red lines have been breached."
        )
    elif peak_level >= 3:
        para3_parts.append(
            "**Why this matters:** L3 pressure represents direct-threat language. "
            "Single-theater dynamics, but trajectory bears watching."
        )

    # Assemble paragraphs (separated by blank lines for frontend rendering)
    paragraphs = [' '.join(para1_parts)]
    if para2_parts:
        paragraphs.append(' '.join(para2_parts))
    if para3_parts:
        paragraphs.append(' '.join(para3_parts))
    return '\n\n'.join(paragraphs)


# ============================================================
# TOP SIGNALS COLLECTOR
# ============================================================
def _build_signals(posture, trackers):
    """
    Collect all top_signals[] from normalized trackers, dedupe, return top N.
    Adds WHA-specific cross-tracker signals.
    """
    all_signals = []
    for theatre, data in trackers.items():
        for sig in data.get('top_signals', []):
            sig.setdefault('priority', 5)
            sig.setdefault('category', 'unknown')
            sig.setdefault('theatre', theatre)
            sig.setdefault('icon', '•')
            sig.setdefault('color', '#6b7280')
            sig.setdefault('short_text', '')
            sig.setdefault('long_text', sig.get('short_text', ''))
            all_signals.append(sig)

    # WHA cross-tracker signal: simultaneous multi-country elevation (>=2 at L3+)
    if posture.get('theatres_at_l3plus', 0) >= 2:
        elevated_theatres = [
            t for t, d in trackers.items()
            if d['levels']['threat'] >= 3
        ]
        all_signals.append({
            'priority':   13,
            'category':   'wha_cascade',
            'theatre':    'regional',
            'level':      posture.get('peak_level', 0),
            'icon':       '🌀',
            'color':      '#dc2626',
            'short_text': f'WHA CASCADE: {len(elevated_theatres)} theaters L3+',
            'long_text':  f'WHA cross-country elevation — {", ".join(t.upper() for t in elevated_theatres)} '
                          f'simultaneously at L3+; migration, sanctions, and adversary-access vectors converging.',
        })

    # Global sort
    all_signals.sort(key=lambda x: x.get('priority', 0), reverse=True)

    # Dedupe by (theatre, category) AND enforce per-theatre quota (v2.4.0 May 21 2026)
    # Per-tracker quota: max MAX_PER_THEATRE signals per country tracker.
    # Cross-tracker signals (theatre='regional', e.g. wha_cascade) bypass the
    # quota — they're platform-level convergence signals, not per-country emissions.
    seen           = set()
    theatre_counts = {}
    deduped        = []
    for s in all_signals:
        theatre = s.get('theatre', '')
        key     = f'{theatre}:{s.get("category", "")}'
        if key in seen:
            continue
        if theatre != 'regional' and theatre_counts.get(theatre, 0) >= MAX_PER_THEATRE:
            continue
        seen.add(key)
        theatre_counts[theatre] = theatre_counts.get(theatre, 0) + 1
        deduped.append(s)

    if not deduped:
        deduped.append({
            'priority':   1,
            'category':   'baseline',
            'theatre':    'regional',
            'level':      0,
            'icon':       '🌎',
            'color':      '#6b7280',
            'short_text': 'WHA at baseline',
            'long_text':  'All Western Hemisphere theaters at baseline — monitoring for cascade triggers.',
        })

    return deduped     # v2.3.0: full deduped pool (caller caps for display)


# ============================================================
# MAIN BUILD FUNCTION
# ============================================================
# ── Approach B: structured blocks + multi-axis tagging (Jun 13 2026) ──
_WHA_REGIONAL_AXIS_SETS = {
    'kinetic_pressure': ['kinetic'], 'red_line_breached': ['kinetic'],
    'theatre_high': ['kinetic'], 'theatre_active': ['kinetic'],
    'wha_cascade': ['humanitarian', 'economic'], 'kinetic_threshold': ['kinetic'],
    'coalition_threat': ['kinetic', 'diplomatic'],
    'commodity': ['economic'], 'commodity_coupling': ['economic'],
    'economic_stress': ['economic'], 'sovereign_default': ['economic'],
    'election': ['diplomatic'], 'election_watch': ['diplomatic'],
    'green_line_active': ['diplomatic'], 'diplomatic_track_active': ['diplomatic'],
    'diplomatic_active': ['diplomatic'], 'mediation': ['diplomatic'],
    'humanitarian': ['humanitarian'], 'displacement': ['humanitarian'],
    'migration': ['humanitarian'], 'health_emergency': ['humanitarian'],
}
_WHA_AXIS_KEYWORD_HINTS = [
    ('economic', ['economic', 'commodity', 'copper', 'silver', 'oil', 'default', 'reserves', 'sanction', 'mining']),
    ('humanitarian', ['humanitarian', 'displace', 'refugee', 'migration', 'famine']),
    ('diplomatic', ['diplomatic', 'election', 'runoff', 'mediation', 'negotiat', 'coalition', 'sanction']),
]

def _wha_axes_for_signal(sig):
    sig = sig if isinstance(sig, dict) else {}
    pt = sig.get('pressure_type')
    cat = str(sig.get('category') or '').lower()
    if cat in _WHA_REGIONAL_AXIS_SETS:
        axes = list(_WHA_REGIONAL_AXIS_SETS[cat])
        if pt and pt in ('kinetic','economic','diplomatic','humanitarian') and pt not in axes:
            axes.insert(0, pt)
        return axes
    if pt and pt in ('kinetic','economic','diplomatic','humanitarian'):
        return [pt]
    blob = (cat + ' ' + str(sig.get('short_text') or '') + ' ' + str(sig.get('long_text') or '')).lower()
    for axis, kws in _WHA_AXIS_KEYWORD_HINTS:
        if any(k in blob for k in kws):
            return [axis]
    return ['kinetic']

def _wha_tag_signal_axes(signals):
    out = []
    for s in (signals or []):
        s2 = dict(s)
        axes = _wha_axes_for_signal(s2)
        s2['axes'] = axes
        s2.setdefault('pressure_type', axes[0])
        out.append(s2)
    return out

def _wha_prose_v2_to_blocks(md):
    """Parse markdown prose_v2 into {label,text} blocks. Header is
    '**Western Hemisphere -- date**'; posture 'Regional posture at ...';
    closer '**Why this matters:**'. Mirrors the ME converter."""
    if not md or not isinstance(md, str):
        return []
    import re as _re
    paras = [p.strip() for p in md.split('\n\n') if p.strip()]
    blocks = []
    for i, para in enumerate(paras):
        hm = _re.match(r'^\*\*([^*]+)\*\*\s*(.*)$', para, _re.S)
        if i == 0 and hm:
            blocks.append({'label': hm.group(1).strip(), 'text': ''})
            rest = hm.group(2).strip()
            if rest:
                pm = _re.match(r'^(Regional posture[^.]*\.(?:\s+\d+\s+red line[^.]*\.)?)\s*([\s\S]*)$', rest)
                if pm:
                    posture_txt = pm.group(1).strip()
                    dive_txt = pm.group(2).strip()
                    if posture_txt.lower().startswith('regional posture'):
                        posture_txt = posture_txt[len('Regional posture'):].lstrip(' at').strip()
                        posture_txt = posture_txt[0].upper() + posture_txt[1:] if posture_txt else posture_txt
                    blocks.append({'label': 'Regional Posture', 'text': posture_txt})
                    if dive_txt:
                        blocks.append({'label': 'Theatre Reads', 'text': dive_txt})
                else:
                    blocks.append({'label': 'Regional Posture', 'text': rest})
            continue
        wm = _re.match(r'^\*\*Why this matters:\*\*\s*([\s\S]*)$', para)
        if wm:
            blocks.append({'label': 'Why This Matters', 'text': wm.group(1).strip()})
            continue
        clean = _re.sub(r'\*\*', '', para)
        blocks.append({'label': 'Theatre Reads', 'text': clean})
    return blocks


def build_regional_bluf(force=False):
    """
    Build the WHA regional BLUF. Reads all WHA caches, synthesizes,
    caches result in Redis. Returns dict.
    Cache check is inside this function (matches ME / Asia pattern).
    """
    if not force:
        cached = _redis_get(BLUF_CACHE_KEY)
        if cached and cached.get('generated_at'):
            try:
                age = (datetime.now(timezone.utc) -
                       datetime.fromisoformat(cached['generated_at'])).total_seconds()
                if age < BLUF_CACHE_TTL:
                    cached['from_cache'] = True
                    return cached
            except Exception:
                pass

    print('[WHA BLUF v1.0] Building regional BLUF from all WHA tracker caches...')

    try:
        trackers, trackers_missing, trackers_stale = _read_all_trackers()

        if not trackers:
            return {
                'success': False,
                'error':   'No tracker data available',
                'bluf':    'BLUF unavailable -- no WHA tracker caches loaded.',
                'signals': [],
                'top_signals': [],
                'posture_label': 'UNAVAILABLE',
                'posture_color': '#6b7280',
            }

        posture     = _determine_regional_posture(trackers)
        bluf        = _build_bluf_prose(posture, trackers)
        # ── prose_v2 (May 22 2026) — richer human-language synthesis ──
        # Hybrid rollout: emit both 'bluf' (legacy) and 'bluf_v2' (new).
        # Frontend prefers bluf_v2 if present, falls back to bluf.
        try:
            bluf_v2_md = _build_bluf_prose_v2(posture, trackers)
            bluf_v2 = _wha_prose_v2_to_blocks(bluf_v2_md)   # approach B blocks
        except Exception as e:
            print(f"[WHA BLUF v2] prose_v2 build failed (falling back to legacy): {e}")
            bluf_v2_md = None
            bluf_v2 = []
        all_signals = _build_signals(posture, trackers)            # v2.3.0: full pool — for GPI axis aggregation
        all_signals = _wha_tag_signal_axes(all_signals)            # Jun 13 2026: multi-axis pills
        top_signals = all_signals[:TOP_SIGNALS_COUNT]                # v2.3.0: capped for display

        trackers_live = len(trackers)

        # Per-theatre summary (canonical)
        theatre_summary = {}
        for t, data in trackers.items():
            lvls       = data.get('levels', {})
            threat_lvl = lvls.get('threat', 0)
            infl_lvl   = lvls.get('influence')
            theatre_summary[t] = {
                'level':            threat_lvl,
                'label':            ESCALATION_LABELS.get(threat_lvl, 'Unknown'),
                'color':            ESCALATION_COLORS.get(threat_lvl, '#6b7280'),
                'score':            data.get('score', 0),
                'flag':             data.get('flag', THEATRE_FLAGS.get(t, '')),
                'timestamp':        data.get('scanned_at', ''),
                'threat_level':     threat_lvl,
                'influence_level':  infl_lvl,
                'green_level':      lvls.get('green'),
                'dominant_axis':    lvls.get('dominant_axis', 'threat'),
                'dominant_level':   lvls.get('dominant_level', threat_lvl),
                'is_dual_axis':     infl_lvl is not None,
                'influence_label':  INFLUENCE_LABELS.get(infl_lvl, '') if infl_lvl is not None else None,
                'influence_color':  INFLUENCE_COLORS.get(infl_lvl, '#6b7280') if infl_lvl is not None else None,
            }

        scores = [t.get('score', 0) for t in theatre_summary.values()]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        result = {
            'success':            True,
            'from_cache':         False,
            'bluf':               bluf,
            'bluf_v2':            bluf_v2,  # Jun 13 2026 — {label,text} block array (approach B)
            'bluf_v2_md':         bluf_v2_md,  # original markdown prose (preserved)
            'signals':            all_signals,                # v2.3.0: FULL signal pool — for GPI axis aggregation
            'top_signals':        top_signals,                # v2.3.0: capped — for display + prose synthesis
            'posture_label':      posture['label'],
            'posture_color':      posture['color'],
            'peak_level':         posture['peak_level'],      # legacy alias
            'max_level':          posture['peak_level'],      # canonical
            'avg_score':          avg_score,
            'red_lines_breached': posture['breached_count'],
            'trackers_live':      trackers_live,
            'theatres_live':      trackers_live,              # canonical alias
            'theatres_at_l3plus': posture['theatres_at_l3plus'],
            'trackers_total':     len(TRACKER_KEYS),
            'trackers_stale':     trackers_stale,    # B: served from last-known-good
            'trackers_missing':   trackers_missing,  # B: no live AND no last-known-good
            'picture_complete':   (len(trackers_missing) == 0),
            'theatre_summary':    theatre_summary,
            'generated_at':       datetime.now(timezone.utc).isoformat(),
            'version':            '1.0.0',
            'region':             'western_hemisphere',
            'top_signals_count':  len(top_signals),
        }

        _bluf_ttl = BLUF_INCOMPLETE_TTL if (trackers_missing or trackers_stale) else BLUF_CACHE_TTL
        _redis_set(BLUF_CACHE_KEY, result, ttl=_bluf_ttl)
        print(f"[WHA BLUF v1.0] Built: posture={posture['label']}, "
              f"max_level=L{posture['peak_level']}, "
              f"breached={posture['breached_count']}, "
              f"signals={len(top_signals)}, "
              f"theaters_live={trackers_live}")
        return result

    except Exception as e:
        print(f"[WHA BLUF] SYNTHESIS EXCEPTION: {e}")
        print(f"[WHA BLUF] Traceback follows:")
        print(traceback.format_exc())
        return {
            'success': False,
            'error':   f'{type(e).__name__}: {str(e)[:300]}',
            'bluf':    'BLUF synthesis failed -- check backend logs for traceback.',
            'signals': [],
            'top_signals': [],
            'posture_label': 'ERROR',
            'posture_color': '#6b7280',
        }


# ============================================================
# ROUTE REGISTRATION
# ============================================================
def register_wha_bluf_routes(app):
    """Register WHA BLUF endpoints on the given Flask app."""
    from flask import jsonify, request as flask_request

    @app.route('/api/rhetoric/wha/bluf', methods=['GET'])
    def get_wha_bluf():
        force = flask_request.args.get('force', 'false').lower() == 'true'
        result = build_regional_bluf(force=force)
        return jsonify(result)

    @app.route('/api/rhetoric/wha/bluf/debug', methods=['GET'])
    def get_wha_bluf_debug():
        """Direct Redis cache inspection -- for triage."""
        cached = _redis_get(BLUF_CACHE_KEY)
        return jsonify({
            'cache_present':  cached is not None,
            'cache_data':     cached,
        })

    print('[WHA BLUF] Routes registered: /api/rhetoric/wha/bluf, /bluf/debug')


# ============================================================
# STANDALONE TEST
# ============================================================
if __name__ == '__main__':
    print("WHA Regional BLUF Engine -- standalone test")
    print("(Requires Redis env vars to actually read tracker caches)")
    print()
    result = build_regional_bluf(force=True)
    print('BLUF:')
    print(result.get('bluf', '(no BLUF)'))
    print()
    print('TOP SIGNALS:')
    for s in result.get('top_signals', []):
        print(f'  {s.get("icon", "•")} {s.get("short_text", "")}')
    print()
    print(f'POSTURE: {result.get("posture_label", "")}')
    print(f'MAX LEVEL: L{result.get("max_level", 0)}')
    print(f'TRACKERS LIVE: {result.get("trackers_live", 0)}/{result.get("trackers_total", 0)}')
