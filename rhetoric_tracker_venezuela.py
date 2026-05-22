"""
Venezuela Rhetoric Tracker — v1.0.0 (May 21 2026)

Hybrid command-node + absorber tracker for Venezuela.
First tracker built CONTRACT-NATIVE — L5 Reservation Contract baked in
from day 1 (no retrofit). 16 actors, 6 vectors.

═══════════════════════════════════════════════════════════════════
REALITY CONTEXT (May 2026)
═══════════════════════════════════════════════════════════════════
- Maduro: US federal detention (Brooklyn MDC) since Jan 3 2026 raid
  ("Operation Absolute Resolve"). Pre-trial. Pleaded not guilty.
  Argentina extradition request pending.
- Delcy Rodríguez: Acting president since Jan 5 2026. 90-day cap
  expired May 4 — legal continuity unresolved by Maduro-aligned NA.
- US-VZ DÉTENTE: Embassy reopened, Delcy delisted from SDN (Apr 2),
  political prisoner releases (621+), Treasury issuing new licenses.
- US Chargé d'Affaires: John M. Barrett (since Apr 23 2026).
  DCM: Mike Garcia.
- VZ rep in DC: Felix Plasencia.
- VZ Foreign Minister: Yvan Gil.
- Diosdado Cabello: Interior Minister AND only remaining fugitive
  co-defendant in Maduro indictment.
- Padrino López: Defense Minister, LOYAL not parallel.
- Opposition: Machado (Nobel Prize), Edmundo González (won 2024 vote).
- Active ICJ case with Guyana on Essequibo territory.

═══════════════════════════════════════════════════════════════════
L5 RESERVATION CONTRACT (v1.0.0 — May 21 2026)
═══════════════════════════════════════════════════════════════════
Per platform contract, L5 "Active Conflict" requires explicit axis
trigger across kinetic / humanitarian / economic / diplomatic.

VZ has REAL detection for 3 of 4 axes (kinetic uses ceasefire-aware
logic mirroring US tracker; humanitarian uses migration surge +
civilian pressure; economic uses currency/PDVSA tripwires).
Diplomatic axis is SCAFFOLD for weekend audit.

US-VZ DÉTENTE acts as kinetic L5 suppressor — when Trump cooperation
signals are active AND no kinetic tripwires fired, kinetic stays L4.
If détente breaks (Trump reverses, second-wave strikes threatened,
US embassy withdrawn), kinetic L5 fires.

═══════════════════════════════════════════════════════════════════
ARCHITECTURE
═══════════════════════════════════════════════════════════════════
- Backend: asifah-wha-backend
- Cache keys: rhetoric:venezuela:latest, :summary, :history
- Fingerprint key: fingerprint:venezuela:current
- Cross-theater reads: US, Cuba, Iran, Russia, China
- Sources: TeleSur, Reuters, El País, Caracas Chronicles,
  Efecto Cocuyo, Tal Cual, Provea, El Pitazo, OVCS, Reddit r/vzla,
  Brave, Telegram

Author: Asifah Analytics
"""

import os
import json
import time
import threading
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from flask import request, jsonify

# ── Signal interpreter (red lines + so-what + executive summary) ──
try:
    from venezuela_signal_interpreter import interpret_venezuela_signals
    INTERPRETER_AVAILABLE = True
except ImportError:
    print('[VZ Rhetoric] WARNING: venezuela_signal_interpreter not available')
    INTERPRETER_AVAILABLE = False

# ── Commodity proxy (pulls oil/gold/wheat pressure from ME backend) ──
try:
    from commodity_proxy_wha import (
        get_commodity_pressure,
        get_commodity_fingerprints_for_country,
    )
    COMMODITY_PROXY_AVAILABLE = True
except ImportError:
    print('[VZ Rhetoric] WARNING: commodity_proxy_wha not available')
    COMMODITY_PROXY_AVAILABLE = False

# ════════════════════════════════════════════════════════════════════
# REDIS CONFIG
# ════════════════════════════════════════════════════════════════════
UPSTASH_URL    = os.environ.get('UPSTASH_REDIS_REST_URL', '')
UPSTASH_TOKEN  = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')

RHETORIC_CACHE_KEY  = 'rhetoric:venezuela:latest'
SUMMARY_CACHE_KEY   = 'rhetoric:venezuela:summary'
HISTORY_KEY         = 'rhetoric:venezuela:history'
FINGERPRINT_KEY     = 'fingerprint:venezuela:current'

# 12-hour refresh cadence (matches Cuba + other WHA trackers)
SCAN_INTERVAL_HOURS = 12
CACHE_TTL           = SCAN_INTERVAL_HOURS * 3600  # 43200 = 12 hours

# ════════════════════════════════════════════════════════════════════
# API KEYS
# ════════════════════════════════════════════════════════════════════
NEWSAPI_KEY     = os.environ.get('NEWSAPI_KEY', '')
BRAVE_API_KEY   = os.environ.get('BRAVE_API_KEY', '')

# ════════════════════════════════════════════════════════════════════
# ESCALATION LEVELS (canonical platform schema)
# ════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════
# ESCALATION LEVELS — canonical band/level vocabulary (v1.1 May 21 2026)
# ════════════════════════════════════════════════════════════════════
# Bands harmonize across trackers (STABLE / ACTIVE / VOLATILE / CRISIS).
# Tracker-specific level names preserve analytical voice.
# Phase 4b platform reconciliation: canonical target = US tracker vocab.
ESCALATION_LEVELS = {
    0: {'label': 'Stable',            'band': 'STABLE',   'color': '#6b7280', 'icon': '🟢'},
    1: {'label': 'Active',            'band': 'ACTIVE',   'color': '#3b82f6', 'icon': '🟢'},
    2: {'label': 'Active+',           'band': 'ACTIVE',   'color': '#f59e0b', 'icon': '🟡'},
    3: {'label': 'Pressure Building', 'band': 'VOLATILE', 'color': '#f97316', 'icon': '🟠'},
    4: {'label': 'Pressure Peak',     'band': 'VOLATILE', 'color': '#ef4444', 'icon': '🔴'},
    5: {'label': 'Active Crisis',     'band': 'CRISIS',   'color': '#7f1d1d', 'icon': '🔴'},
}

THEATRE_LABELS = {
    0: 'Stable',
    1: 'Active',
    2: 'Active+',
    3: 'Pressure Building',
    4: 'Pressure Peak',
    5: 'Active Crisis',
}

# Convenience lookup: level → band (for cross-tracker aggregation)
THEATRE_BANDS = {
    0: 'STABLE',
    1: 'ACTIVE',
    2: 'ACTIVE',
    3: 'VOLATILE',
    4: 'VOLATILE',
    5: 'CRISIS',
}

# ════════════════════════════════════════════════════════════════════
# L5 RESERVATION CONTRACT CONSTANTS
# ════════════════════════════════════════════════════════════════════
#
# CEASEFIRE_PARTNERS: theaters where VZ has an active diplomatic/ceasefire
# track. Today: US-VZ détente is the analog of a ceasefire. When kinetic
# L5 conditions are detected AND détente is active, the L5 trigger is
# SUPPRESSED. If détente collapses, gate auto-fires.
#
# Mirror of US tracker pattern (v1.1.0 May 21 2026).
CEASEFIRE_PARTNERS  = ['us']
CEASEFIRE_THRESHOLD = 3  # ceasefire_level >= 3 = framework agreed or better

SOURCE_CLASS = 'hybrid'  # command-node + absorber

# ════════════════════════════════════════════════════════════════════
# ACTOR DISPLAY ORDER (frontend UI hint)
# ════════════════════════════════════════════════════════════════════
ACTOR_DISPLAY_ORDER = [
    # US side
    'us_government',
    'us_sanctions_regulatory',
    'us_military_posture',
    'us_vz_envoys',
    # VZ government
    'vz_delcy_rodriguez',
    'vz_jorge_rodriguez',
    'vz_yvan_gil',
    'vz_diosdado_cabello',
    'vz_internal_security',
    # VZ opposition
    'vz_opposition',
    # Chavismo residual
    'vz_chavismo_residual',
    # Adversary axes
    'russia_vz_axis',
    'china_vz_axis',
    'iran_vz_axis',
    # Special watch + territorial
    'hizballah_vz_signals',
    'essequibo_guyana_dispute',
]


# ════════════════════════════════════════════════════════════════════
# ACTORS DICT (16 actors)
# ════════════════════════════════════════════════════════════════════
ACTORS = {

    # ══════════════════════════════════════════════════════════════
    # US SIDE (4 actors)
    # ══════════════════════════════════════════════════════════════

    'us_government': {
        'name':  'U.S. Government',
        'flag':  '🇺🇸',
        'icon':  '🏛️',
        'color': '#2563eb',
        'role':  'WH / State / Treasury — Political Rhetoric Toward Venezuela',
        'butterfly_boost': 'Phase 6 upstream signal (+1)',
        'description': (
            'US executive branch political rhetoric toward Venezuela. Currently '
            'in DÉTENTE posture (May 2026) — Trump statements oscillate between '
            'cooperation praise ("they\'ve given us everything") and conditional '
            'threats. Watch for: regime change rhetoric returning, Rubio (Cuban-'
            'American, hawkish) statements, State Department briefings on Caracas, '
            'Treasury announcements on sanctions easing or re-tightening.'
        ),
        'keywords': [
            'trump venezuela', 'trump maduro', 'trump caracas',
            'trump delcy', 'trump rodriguez venezuela',
            'rubio venezuela', 'rubio maduro', 'rubio caracas',
            'state department venezuela', 'state dept venezuela',
            'white house venezuela', 'wh venezuela',
            'treasury venezuela', 'treasury maduro',
            'us venezuela policy', 'venezuela policy',
            'venezuela detente', 'us venezuela cooperation',
            'venezuela regime change', 'venezuela transition',
        ],
        'tripwires': [
            'trump threatens venezuela', 'second wave venezuela',
            'us reverses venezuela', 'detente collapse',
            'venezuela ultimatum', 'regime change ordered',
            'rubio escalates venezuela', 'us threatens delcy',
        ],
        'baseline_statements_per_week': 30,
    },

    'us_sanctions_regulatory': {
        'name':  'U.S. Sanctions & Regulatory',
        'flag':  '🇺🇸',
        'icon':  '⚖️',
        'color': '#1e40af',
        'role':  'OFAC / Commerce / Treasury — Specific Regulatory Actions on Venezuela',
        'butterfly_boost': 'Phase 6 upstream signal (+1)',
        'description': (
            'Named sanctions, designations, regulatory actions. Currently in EASING '
            'cycle (May 2026) — Delcy delisted Apr 2, Treasury issuing new licenses, '
            'Chevron license modified. Watch for: OFAC SDN additions/removals, '
            'Chevron license renewals or revocations, PDVSA-related licenses, '
            'secondary sanctions threats, oil services waivers, gold sanctions.'
        ),
        'keywords': [
            'ofac venezuela', 'treasury sanctions venezuela',
            'chevron venezuela', 'chevron license', 'chevron waiver',
            'pdvsa sanctions', 'venezuela sanctions',
            'venezuela oil license', 'venezuela license',
            'venezuela sdn list', 'delcy sdn',
            'venezuela gold sanctions', 'arco minero sanctions',
            'venezuela oil waiver', 'venezuela secondary sanctions',
            'venezuela financial sanctions', 'venezuela banking',
            # May 22 2026: Oil-major activity (Exxon, Repsol, ENI, Shell, Maurel)
            'exxon venezuela', 'exxonmobil venezuela', 'exxon pdvsa', 'exxon pump oil',
            'repsol venezuela', 'eni venezuela', 'shell venezuela',
            'maurel prom venezuela', 'reliance venezuela',
            'venezuela oil deal', 'venezuela oil pump', 'venezuela mineral deal',
            'pdvsa joint venture', 'venezuela crude exports',
            'jose terminal', 'orinoco crude', 'heavy crude venezuela',
            'venezuela oil recovery', 'venezuela oil flow',
            # White House / Trump VZ direct statements (May 2026)
            'white house venezuela', 'trump venezuela oil',
            'venezuela mineral white house', 'venezuela oil flowing',
        ],
        'tripwires': [
            'sanctions reimposed', 'license revoked', 'sdn added',
            'chevron revoked', 'pdvsa relisted', 'secondary sanctions venezuela',
            'sanctions snap back', 'gold sanctions tightened',
        ],
        'baseline_statements_per_week': 15,
    },

    'us_military_posture': {
        'name':  'U.S. Military Posture',
        'flag':  '🇺🇸',
        'icon':  '⚓',
        'color': '#0891b2',
        'role':  'SOUTHCOM / Navy / Joint Forces — Kinetic Posture Toward Venezuela',
        'description': (
            'US military posture toward Venezuela. Operation "Absolute Resolve" '
            '(Jan 3 2026) captured Maduro; Trump cancelled second-wave Jan 9. '
            'Currently QUIET (May 2026) but watch for: SOUTHCOM exercises in '
            'Caribbean, USS Nimitz movements, second-wave threats, Delta Force '
            'rumors, troop posture announcements, Caribbean naval positioning.'
        ),
        'keywords': [
            'southcom venezuela', 'us southern command venezuela',
            'uss nimitz venezuela', 'nimitz caribbean',
            'us military venezuela', 'us troops venezuela',
            'us strike venezuela', 'us forces venezuela',
            'operation absolute resolve', 'absolute resolve venezuela',
            'caribbean naval', 'caribbean exercise',
            'us military caracas', 'delta force venezuela',
            'second wave venezuela', 'second strike venezuela',
        ],
        'tripwires': [
            'us troops to venezuela', 'us forces deploy venezuela',
            'second strike venezuela', 'venezuela strike imminent',
            'us military escalation venezuela', 'pentagon escalates venezuela',
            'carrier deploys caribbean', 'us forces engage venezuela',
        ],
        'baseline_statements_per_week': 10,
    },

    'us_vz_envoys': {
        'name':  'U.S.-Venezuela Diplomatic Channel',
        'flag':  '🇺🇸',
        'icon':  '🤝',
        'color': '#0284c7',
        'role':  'Charge d\'Affaires / DCM / Embassy Caracas / VZ Rep in DC',
        'description': (
            'Diplomatic channel between Washington and Caracas. US CdA: '
            'John M. Barrett (since Apr 23 2026, took over from Amb. Laura F. Dogu '
            'who oversaw embassy reopening). DCM: Mike Garcia. VZ rep in '
            'Washington: Felix Plasencia. Watch for: Barrett public statements, '
            'embassy press releases, Plasencia engagements, channel disruptions.'
        ),
        'keywords': [
            'john barrett venezuela', 'cda barrett', 'charge daffaires venezuela',
            'mike garcia venezuela', 'dcm garcia venezuela',
            'felix plasencia', 'plasencia washington',
            'us embassy caracas', 'embassy reopen venezuela',
            'us vz channel', 'us venezuela diplomacy',
            'laura dogu', 'ambassador dogu venezuela',
            'venezuela rep washington', 'venezuela us channel',
        ],
        'tripwires': [
            'embassy closed', 'embassy withdrawn', 'barrett expelled',
            'cda withdrawn', 'venezuela rep expelled', 'channel broken',
            'plasencia recalled', 'embassy staff withdrawn',
        ],
        'baseline_statements_per_week': 5,
    },

    # ══════════════════════════════════════════════════════════════
    # VZ GOVERNMENT (5 actors)
    # ══════════════════════════════════════════════════════════════

    'vz_delcy_rodriguez': {
        'name':  'Delcy Rodríguez',
        'flag':  '🇻🇪',
        'icon':  '👑',
        'color': '#dc2626',
        'role':  'Acting President of Venezuela',
        'description': (
            'Acting President of Venezuela since Jan 5 2026. Former VP, oil '
            'minister. 90-day cap expired May 4 — legal continuity question '
            'unresolved. Performing cooperation with US per détente arrangement '
            'while preserving Chavismo. Sister of Jorge Rodríguez (NA head). '
            'First international trip: The Hague May 9 (Essequibo ICJ case). '
            'Watch for: speeches, council of ministers actions, US-cooperation '
            'language, sanctions relief asks, oil reform announcements.'
        ),
        'keywords': [
            # Domestic identity (existing)
            'delcy rodriguez', 'delcy rodríguez', 'presidenta delcy',
            'acting president venezuela', 'interim president venezuela',
            'venezuela acting president', 'presidenta encargada',
            'delcy speech', 'delcy announces', 'delcy declares',
            'venezuela president', 'rodriguez caracas',
            'miraflores delcy', 'delcy miraflores',
            'venezuela cabinet', 'consejo de ministros venezuela',
            'venezuela oil minister', 'delcy oil',
            # May 22 2026: Rodriguez foreign engagement + oil-pivot diplomacy
            'rodriguez india', 'rodriguez visit india', 'delcy india',
            'venezuela india oil', 'venezuela india oil supply',
            'rodriguez china visit', 'rodriguez beijing',
            'rodriguez moscow', 'rodriguez russia visit',
            'rodriguez tehran', 'rodriguez iran visit',
            'delcy foreign trip', 'delcy travel',
            'venezuela oil diplomacy', 'rodriguez oil agenda',
        ],
        'tripwires': [
            'delcy steps down', 'delcy resigns', 'delcy removed',
            'delcy defies us', 'delcy breaks détente', 'delcy arrested',
            'delcy challenges trump', 'rodriguez ousted',
        ],
        'baseline_statements_per_week': 20,
    },

    'vz_jorge_rodriguez': {
        'name':  'Jorge Rodríguez',
        'flag':  '🇻🇪',
        'icon':  '📜',
        'color': '#b91c1c',
        'role':  'President of National Assembly — Legislative Parallel Power',
        'description': (
            'Head of Venezuela National Assembly. Brother of Delcy Rodríguez. '
            'Swore his sister in as acting president Jan 5. Maduro-aligned NA '
            'controls whether Delcy\'s acting term gets formalized past 90-day '
            'cap (expired May 4) — KEY constitutional decision. Watch for: '
            'legislative votes on extending Delcy term, sibling coordination '
            'signals, NA pronouncements on US-VZ relations, election scheduling.'
        ),
        'keywords': [
            'jorge rodriguez', 'jorge rodríguez',
            'asamblea nacional venezuela', 'venezuela national assembly',
            'venezuela legislature', 'venezuela parliament',
            'national assembly caracas', 'venezuela na president',
            'venezuela assembly speaker', 'rodriguez assembly',
            'venezuela legislative', 'venezuela parliamentary',
            'venezuela elections schedule', 'snap election venezuela',
        ],
        'tripwires': [
            'na declares vacancy', 'snap election called',
            'na refuses extension', 'assembly dissolves',
            'jorge breaks with delcy', 'siblings split',
            'permanently vacant venezuela', 'na votes maduro out',
        ],
        'baseline_statements_per_week': 8,
    },

    'vz_yvan_gil': {
        'name':  'Yvan Gil',
        'flag':  '🇻🇪',
        'icon':  '🌐',
        'color': '#991b1b',
        'role':  'Foreign Minister — Diplomatic Operations',
        'description': (
            'Venezuela Foreign Minister. Manages diplomatic engagements, '
            'particularly US-VZ channel (announced Plasencia appointment Feb 3). '
            'Watch for: bilateral meeting readouts, UN positioning, statements '
            'on Essequibo dispute, sanctions-relief diplomacy, sponsor-axis '
            '(RU/CN/IR) coordination signals.'
        ),
        'keywords': [
            'yvan gil', 'foreign minister venezuela',
            'venezuela foreign ministry', 'cancilleria venezuela',
            'mre venezuela', 'venezuela mre',
            'gil venezuela diplomat', 'venezuela un envoy',
            'venezuela diplomacy', 'venezuela bilateral',
            'venezuela meeting', 'venezuela treaty',
        ],
        'tripwires': [
            'gil resigns', 'gil withdrawn', 'venezuela severs ties',
            'venezuela expels diplomat', 'venezuela un walkout',
            'venezuela declares persona non grata', 'gil emergency',
        ],
        'baseline_statements_per_week': 6,
    },

    'vz_diosdado_cabello': {
        'name':  'Diosdado Cabello',
        'flag':  '🇻🇪',
        'icon':  '🪖',
        'color': '#7f1d1d',
        'role':  'Interior Minister + Indicted Co-Defendant (Fugitive)',
        'description': (
            'DUAL ROLE: Sitting Interior Minister AND only remaining at-large '
            'co-defendant in Maduro\'s SDNY indictment (per State Dept Apr 2026). '
            'Daughter Daniella Cabello appointed Tourism Minister Feb 2 — family '
            'embedded in Delcy government. Long-suspected of Cartel de los Soles '
            'leadership. Critical signal source for whether US détente extends '
            'to him or eventually targets him. Watch for: Cabello public '
            'appearances, daughter\'s ministry activity, US extradition signals, '
            'Cabello\'s relationship with Delcy, internal-security orders.'
        ),
        'keywords': [
            'diosdado cabello', 'diosdado', 'cabello venezuela',
            'cabello interior', 'venezuela interior minister',
            'cabello psuv', 'cabello strongman',
            'daniella cabello', 'cabello daughter',
            'venezuela interior ministry', 'mij venezuela',
            'cartel de los soles', 'cartel of the suns',
            'cabello indictment', 'cabello fugitive',
        ],
        'tripwires': [
            'cabello arrested', 'cabello extradited', 'cabello flees',
            'cabello defies delcy', 'cabello coup', 'cabello detention',
            'us targets cabello', 'cabello sanctioned',
        ],
        'baseline_statements_per_week': 10,
    },

    'vz_internal_security': {
        'name':  'VZ Internal Security & FANB',
        'flag':  '🇻🇪',
        'icon':  '🛡️',
        'color': '#450a0a',
        'role':  'SEBIN / FAES / FANB — Padrino López + Coercive Apparatus',
        'description': (
            'Venezuela security/intelligence apparatus + military command. '
            'Includes SEBIN (intelligence), FAES (special action force), FANB '
            '(armed forces), DGCIM (military counter-intel). Defense Minister '
            'Padrino López publicly handed Delcy military command Feb 2 ceremony '
            '(sword + golden baton) — LOYAL not parallel power. Watch for: '
            'suppression intensity (post-prisoner-release dynamic), protest '
            'response, Padrino statements, FANB exercises, mass arrest reports.'
        ),
        'keywords': [
            'padrino lopez', 'vladimir padrino', 'padrino venezuela',
            'fanb venezuela', 'venezuela armed forces',
            'venezuela military', 'venezuela army',
            'sebin venezuela', 'faes venezuela', 'dgcim venezuela',
            'venezuela intelligence', 'venezuela security forces',
            'venezuela defense minister', 'venezuela defense ministry',
            'venezuela mass arrest', 'venezuela protest crackdown',
        ],
        'tripwires': [
            'padrino resigns', 'padrino arrested', 'fanb defects',
            'military coup venezuela', 'padrino defies delcy',
            'mass arrests venezuela', 'sebin crackdown',
            'soldiers fire on civilians', 'venezuela military uprising',
        ],
        'baseline_statements_per_week': 12,
    },

    # ══════════════════════════════════════════════════════════════
    # VZ OPPOSITION (1 actor)
    # ══════════════════════════════════════════════════════════════

    'vz_opposition': {
        'name':  'Venezuelan Opposition',
        'flag':  '🇻🇪',
        'icon':  '✊',
        'color': '#f59e0b',
        'role':  'Machado / González / MUD — INVERSE INDICATOR',
        'butterfly_boost': 'Phase 6 upstream signal (+1)',
        'description': (
            'INVERSE INDICATOR: opposition strength = government weakness. '
            'María Corina Machado (Nobel Peace Prize laureate) and Edmundo '
            'González (won 2024 election per opposition tally) leading. Currently '
            'pressing for: deeper political prisoner releases (~500+ remain), '
            'snap elections, expansion of détente. Watch for: Machado statements, '
            'González positioning, MUD coalition activity, US recognition signals, '
            'diaspora mobilization, named prisoner releases.'
        ),
        'keywords': [
            'maria corina machado', 'machado venezuela',
            'edmundo gonzalez', 'gonzalez venezuela',
            'venezuela opposition', 'mud venezuela',
            'venezuela nobel', 'machado nobel',
            'venezuela civil society', 'foro penal',
            'venezuela human rights', 'venezuela political prisoners',
            'venezuela diaspora', 'venezuela exiles',
            'plataforma unitaria', 'unitary platform venezuela',
            'guanipa', 'juan pablo guanipa',
        ],
        'tripwires': [
            'machado arrested', 'machado detained', 'gonzalez detained',
            'opposition leader killed', 'machado exile',
            'mass opposition rally', 'general strike venezuela',
            'opposition declares victory', 'parallel government venezuela',
        ],
        'baseline_statements_per_week': 18,
    },

    # ══════════════════════════════════════════════════════════════
    # CHAVISMO RESIDUAL (1 actor)
    # ══════════════════════════════════════════════════════════════

    'vz_chavismo_residual': {
        'name':  'Chavismo Residual',
        'flag':  '🇻🇪',
        'icon':  '⛓️',
        'color': '#581c87',
        'role':  'Maduro Detention + Nicolasito + Extradition + Loyalist Signals',
        'description': (
            'Residual Chavismo signals around Maduro\'s US detention. Includes: '
            'Maduro court appearances (next dates, motions, "prisoner of war" '
            'rhetoric); his son Nicolás Maduro Guerra ("Nicolasito", NA legislator) '
            'speaking for him; defense legal fees fight; Argentina extradition '
            'request; Cilia Flores (wife, co-detained); remaining loyalist '
            'lawmakers; Hugo Chávez legacy invocations. Watch for: trial date set, '
            'plea changes, hunger strikes, Nicolasito public appearances, Argentina '
            'extradition rulings, family member sanctions.'
        ),
        'keywords': [
            'nicolas maduro', 'maduro court', 'maduro trial', 'maduro brooklyn',
            'maduro detention', 'maduro custody', 'maduro mdc',
            'maduro prisoner of war', 'maduro kidnapped',
            'cilia flores', 'flores venezuela',
            'nicolas maduro guerra', 'nicolasito', 'maduro guerra',
            'argentina maduro extradition', 'maduro extradition',
            'maduro defense', 'maduro lawyer', 'pollack maduro',
            'maduro legal fees', 'maduro defense fund',
            'chavez legacy', 'chavismo', 'bolivarian',
        ],
        'tripwires': [
            'maduro dies in custody', 'maduro hunger strike',
            'maduro convicted', 'maduro acquitted',
            'maduro plea deal', 'maduro extradited argentina',
            'cilia flores released', 'nicolasito arrested',
            'maduro family sanctioned',
        ],
        'baseline_statements_per_week': 12,
    },

    # ══════════════════════════════════════════════════════════════
    # ADVERSARY AXES (3 actors)
    # ══════════════════════════════════════════════════════════════

    'russia_vz_axis': {
        'name':  'Russia-Venezuela Axis',
        'flag':  '🇷🇺',
        'icon':  '🤝',
        'color': '#7c3aed',
        'role':  'Kremlin-Caracas Cooperation — Debt / Rosneft / Military',
        'butterfly_boost': 'Phase 6 upstream signal (+1)',
        'description': (
            'Russian cooperation signals with Venezuela. Likely RECEDING given '
            'US-VZ détente — Delcy unlikely to lean visibly on Moscow while '
            'performing cooperation with Washington. Watch for: Lavrov/Medvedev '
            'visits, Rosneft activity, debt restructuring announcements, military '
            'cooperation signals, Russian advisor presence, Russia abstaining on '
            'UN VZ resolutions, Putin statements on Maduro detention.'
        ),
        'keywords': [
            'russia venezuela', 'lavrov venezuela', 'medvedev venezuela',
            'putin venezuela', 'rosneft venezuela',
            'russia caracas', 'russian advisors venezuela',
            'venezuela russia debt', 'russia venezuela cooperation',
            'kremlin venezuela', 'russia venezuela military',
            'russia oil venezuela', 'russia gas venezuela',
            'russia venezuela summit',
        ],
        'tripwires': [
            'russian troops venezuela', 'russia recognizes delcy',
            'rosneft expanded venezuela', 'putin visits caracas',
            'russia bases venezuela', 'lavrov caracas summit',
            'russia condemns us venezuela',
        ],
        'baseline_statements_per_week': 4,
    },

    'china_vz_axis': {
        'name':  'China-Venezuela Axis',
        'flag':  '🇨🇳',
        'icon':  '🤝',
        'color': '#be185d',
        'role':  'Beijing-Caracas — Belt & Road / CITIC / CNPC',
        'description': (
            'Chinese cooperation signals with Venezuela. Belt and Road inclusion, '
            'oil-for-debt arrangements (CITIC, CNPC), infrastructure investment. '
            'Watch for: Xi/Wang Yi statements on Venezuela, CNPC oil shipments, '
            'CITIC debt extensions, Huawei/ZTE infrastructure activity, BRI '
            'announcements, Chinese ambassador statements, Mandarin-language '
            'VZ coverage signals.'
        ),
        'keywords': [
            'china venezuela', 'xi jinping venezuela',
            'wang yi venezuela', 'beijing venezuela',
            'cnpc venezuela', 'citic venezuela',
            'china oil venezuela', 'china loans venezuela',
            'china venezuela belt road', 'belt road venezuela',
            'huawei venezuela', 'zte venezuela',
            'china venezuela infrastructure', 'china caracas',
            'china venezuela debt',
        ],
        'tripwires': [
            'china recognizes delcy', 'cnpc expands venezuela',
            'china military venezuela', 'china port venezuela',
            'china naval venezuela', 'xi visits caracas',
            'china condemns us venezuela',
        ],
        'baseline_statements_per_week': 3,
    },

    'iran_vz_axis': {
        'name':  'Iran-Venezuela Axis',
        'flag':  '🇮🇷',
        'icon':  '🤝',
        'color': '#059669',
        'role':  'Tehran-Caracas — IRGC / Oil / Refinery',
        'butterfly_boost': 'Phase 6 upstream signal (+1)',
        'description': (
            'Iranian cooperation signals with Venezuela. Historical: IRGC '
            'presence, refinery rehab projects, oil tanker traffic, gasoline '
            'shipments (paradox: oil exporter needing imports), Tareck El '
            'Aissami connection (now arrested 2024). Watch for: Iranian tanker '
            'arrivals/departures, IRGC delegations, Khamenei/Pezeshkian statements '
            'on VZ, refinery technical cooperation, gold-for-gasoline trades, '
            'persistent IR-VZ-CU triangle signaling.'
        ),
        'keywords': [
            'iran venezuela', 'iranian venezuela',
            'irgc venezuela', 'tehran venezuela',
            'pezeshkian venezuela', 'khamenei venezuela',
            'iranian tanker venezuela', 'iran oil venezuela',
            'iran refinery venezuela', 'paraguana refinery',
            'iran gasoline venezuela', 'iranian gasoline caracas',
            'iran venezuela cooperation', 'iran venezuela trade',
            'tareck el aissami', 'el aissami iran',
        ],
        'tripwires': [
            'iranian troops venezuela', 'irgc deployed venezuela',
            'iran missiles venezuela', 'iran nuclear venezuela',
            'iranian tanker docks venezuela', 'iran condemns us venezuela',
        ],
        'baseline_statements_per_week': 4,
    },

    # ══════════════════════════════════════════════════════════════
    # SPECIAL WATCH + TERRITORIAL (2 actors)
    # ══════════════════════════════════════════════════════════════

    'hizballah_vz_signals': {
        'name':  'Hezbollah-Venezuela Watch',
        'flag':  '🇱🇧',
        'icon':  '🕵️',
        'color': '#facc15',
        'role':  'Margarita Island / Financial Flows / Latam Network',
        'description': (
            'Dedicated watch for Hezbollah-Venezuela linkages. Historical concern '
            'centered on Margarita Island (Nueva Esparta state), Lebanese-VZ '
            'diaspora financial flows, Tareck El Aissami operation (Tareck arrested '
            '2024 — residual network status unclear). Watch for: Margarita Island '
            'activity, named operatives, sanctions designations citing Hezbollah-VZ '
            'link, alleged uranium/dual-use trafficking routes, OFAC '
            'counter-terrorism designations involving VZ entities, US intelligence '
            'community reports.'
        ),
        'keywords': [
            'hezbollah venezuela', 'hizballah venezuela',
            'hezbollah caracas', 'hezbollah margarita',
            'margarita island', 'isla margarita',
            'nueva esparta hezbollah', 'lebanese venezuela',
            'venezuela uranium', 'venezuela illicit finance',
            'hezbollah latin america', 'hezbollah latam',
            'venezuela terror finance', 'venezuela ct designation',
            'tareck el aissami hezbollah',
        ],
        'tripwires': [
            'hezbollah cell arrested venezuela',
            'hezbollah attack venezuela', 'hezbollah uranium venezuela',
            'us designates hezbollah venezuela', 'margarita raid',
            'hezbollah operative captured venezuela',
        ],
        'baseline_statements_per_week': 2,
    },

    'essequibo_guyana_dispute': {
        'name':  'Essequibo-Guyana Territorial Dispute',
        'flag':  '🇬🇾',
        'icon':  '🗺️',
        'color': '#16a34a',
        'role':  'ICJ Case / Territorial Claim / Oil Block Tensions',
        'description': (
            'Active territorial dispute between Venezuela and Guyana over '
            'Essequibo region (~⅔ of Guyana\'s current territory). At '
            'International Court of Justice (ICJ). Delcy Rodríguez attended in '
            'Hague May 9, 2026 (her first international trip). Region overlaps '
            'with major ExxonMobil/Hess oil blocks (Stabroek). Watch for: ICJ '
            'hearings/rulings, VZ referendum revival, Guyana statements, oil '
            'block development announcements, CARICOM positioning, US/UK military '
            'posture toward Guyana.'
        ),
        'keywords': [
            'essequibo', 'esequibo',
            'guyana venezuela', 'venezuela guyana',
            'icj guyana venezuela', 'international court guyana venezuela',
            'stabroek block', 'exxon guyana', 'exxonmobil guyana',
            'hess guyana', 'guyana oil block',
            'caricom guyana venezuela', 'guyana territorial',
            'venezuela claims guyana', 'irfaan ali venezuela',
            'guyana defense', 'guyana military',
            'venezuela referendum essequibo',
        ],
        'tripwires': [
            'venezuela invades guyana', 'venezuela seizes essequibo',
            'venezuela troops essequibo', 'guyana mobilizes',
            'icj rules venezuela', 'icj rules guyana',
            'us troops guyana', 'uk troops guyana',
            'oil block seized', 'exxon evacuates guyana',
        ],
        'baseline_statements_per_week': 6,
    },

}


# ════════════════════════════════════════════════════════════════════
# BIDIRECTIONAL MIGRATION MODEL
# Canonical platform pattern (Apr 25 2026): out flows = escalatory,
# return flows = de-escalatory. Net = sum.
# ════════════════════════════════════════════════════════════════════
MIGRATION_OUT_TRIGGERS = {
    1: ['migration venezuela', 'venezolanos huyen', 'venezolanos exodo',
        'venezuelan exodus', 'venezuela emigration',
        'venezolanos colombia', 'venezolanos peru', 'venezolanos brasil',
        'venezuelan refugees colombia'],
    2: ['venezuela mass migration', 'venezuelan migration surge',
        'emigracion masiva venezuela', 'exodus surge venezuela',
        'darien gap surge', 'venezuelan caravan',
        'venezuela border crossings surge'],
    3: ['venezuela exodus crisis', 'crisis migratoria venezuela',
        'venezuelan refugee crisis', 'massive exodus venezuela',
        'darien gap venezuela record', 'venezuela border crisis'],
    4: ['venezuela mass exodus', 'crisis humanitaria venezuela',
        'venezuela humanitarian emergency', 'venezuela refugee emergency',
        'darien gap chaos venezuela'],
    5: ['venezuela total exodus', 'venezuela collapse migration',
        'venezuela state collapse migration', 'mass evacuation venezuela',
        'venezuela border emergency declared'],
}

MIGRATION_RETURN_TRIGGERS = {
    1: ['venezolanos regresan', 'venezuelan return', 'retornados venezuela',
        'venezuela return migration'],
    2: ['venezuelan returnees surge', 'retorno masivo venezuela',
        'venezuelan deportation returns', 'venezuela voluntary return'],
    3: ['venezuelan mass return', 'retorno masivo venezolanos',
        'venezuela reintegration program'],
    4: ['venezuela receives mass return', 'venezuelan exodus reversed',
        'venezuela reverse migration'],
    5: ['venezuelan mass repatriation', 'reverse exodus venezuela'],
}

# ════════════════════════════════════════════════════════════════════
# CIVILIAN PRESSURE TRIGGERS
# Detects stability signals: blackouts, scarcity, hyperinflation,
# healthcare collapse, food crisis
# ════════════════════════════════════════════════════════════════════
CIVILIAN_PRESSURE_TRIGGERS = {
    1: ['venezuela power outage', 'venezuela apagón', 'venezuela cortes luz',
        'venezuela inflation', 'venezuela inflación',
        'venezuela shortage', 'venezuela escasez',
        'venezuela bolívar', 'bolívar caída', 'bolivar fall'],
    2: ['venezuela blackout', 'venezuela apagón nacional', 'venezuela protests',
        'venezuela protests scarcity', 'venezuela protestas escasez',
        'venezuela hyperinflation', 'venezuela hiperinflación',
        'venezuela food shortage', 'venezuela escasez alimentos',
        'venezuela medicine shortage', 'venezuela escasez medicinas'],
    3: ['venezuela widespread blackout', 'venezuela apagón generalizado',
        'venezuela bread lines', 'venezuela colas pan',
        'venezuela hunger', 'venezuela hambre',
        'venezuela healthcare collapse', 'venezuela colapso salud',
        'venezuela mass protests'],
    4: ['venezuela rolling blackouts', 'venezuela apagones rotativos',
        'venezuela bread riots', 'venezuela bolivar collapse',
        'venezuela currency collapse', 'venezuela colapso moneda',
        'venezuela famine signals', 'venezuela hambruna'],
    5: ['venezuela total grid collapse', 'venezuela colapso eléctrico total',
        'venezuela famine declared', 'venezuela hambruna declarada',
        'venezuela hyperinflation spike', 'venezuela bolivar zero',
        'venezuela currency total collapse', 'venezuela healthcare implodes'],
}

# ════════════════════════════════════════════════════════════════════
# OIL EXTRACTION TRIGGERS
# PDVSA production, sanctions, Chevron license, dark fleet
# ════════════════════════════════════════════════════════════════════
OIL_EXTRACTION_TRIGGERS = {
    1: ['pdvsa production', 'venezuela oil output',
        'chevron venezuela', 'venezuela barrels',
        'venezuela petroleum', 'venezuela petróleo'],
    2: ['pdvsa production drop', 'venezuela oil decline',
        'chevron license modified', 'chevron license renewed',
        'venezuela tanker', 'venezuela petrolero',
        'venezuela oil exports'],
    3: ['pdvsa production crisis', 'venezuela oil sector collapse signals',
        'chevron license revoked', 'chevron leaves venezuela',
        'venezuela dark fleet expansion', 'venezuela shadow fleet',
        'pdvsa refinery failure'],
    4: ['pdvsa halt', 'pdvsa shutdown',
        'venezuela oil exports halted', 'venezuela oil zero',
        'venezuela secondary sanctions oil',
        'pdvsa default oil',
        'venezuela refinery total failure'],
    5: ['pdvsa total halt', 'pdvsa cease operations',
        'venezuela oil sector collapse', 'venezuela oil industry implodes',
        'venezuela sovereign default oil',
        'pdvsa bankruptcy', 'venezuela oil zero production'],
}

# ════════════════════════════════════════════════════════════════════
# ESSEQUIBO TRIGGERS
# Territorial dispute escalation signals
# ════════════════════════════════════════════════════════════════════
ESSEQUIBO_TRIGGERS = {
    1: ['essequibo dispute', 'guyana venezuela border',
        'icj guyana venezuela', 'caricom essequibo',
        'guyana venezuela claim'],
    2: ['venezuela essequibo claim', 'venezuela referendum essequibo',
        'guyana defense essequibo', 'icj proceeds essequibo',
        'stabroek venezuela'],
    3: ['venezuela essequibo forces', 'venezuela troops border guyana',
        'guyana mobilizes essequibo', 'venezuela rejects icj',
        'exxon evacuates partial guyana'],
    4: ['venezuela seizes essequibo block', 'venezuela enters essequibo',
        'guyana defense activation', 'us troops guyana',
        'uk troops guyana', 'caricom emergency essequibo'],
    5: ['venezuela invades guyana', 'venezuela annexes essequibo',
        'venezuelan military essequibo', 'guyana under attack',
        'caribbean war', 'oil blocks seized'],
}

# ════════════════════════════════════════════════════════════════════
# DIPLOMATIC / DÉTENTE TRIGGERS (US-VZ ceasefire-analog)
# Mirrors Iran/Israel/Lebanon canonical schema. Writes
# diplomatic_active + ceasefire_level + diplomatic_modifier
# to fingerprint so other trackers (and L5 gate) can read.
# ════════════════════════════════════════════════════════════════════
DIPLOMATIC_TRIGGERS = {
    1: ['us venezuela talks', 'venezuela us cooperation',
        'venezuela diplomatic outreach',
        'plasencia dialogue', 'barrett caracas'],
    2: ['us venezuela direct talks', 'plasencia barrett meeting',
        'venezuela detente signals', 'venezuela us channel',
        'us venezuela engagement', 'venezuela cooperation rhetoric'],
    3: ['us venezuela framework', 'venezuela us understanding',
        'detente venezuela framework', 'venezuela us accord',
        'delcy us cooperation', 'venezuela sanctions easing',
        'chevron license renewed', 'delcy delisted sdn'],
    4: ['us venezuela detente confirmed', 'venezuela us agreement signed',
        'venezuela sanctions relief major', 'us embassy reopens caracas',
        'us venezuela ambassadorial', 'venezuela us comprehensive',
        'us venezuela cooperation deal'],
    5: ['us venezuela normalization', 'venezuela full sanctions lifted',
        'venezuela us ambassador exchange', 'venezuela us treaty',
        'venezuela full diplomatic relations restored'],
}

# Diplomatic modifier (canonical schema):
# 0=baseline, 1=-1, 2=-3, 3=-6, 4=-10, 5=-15
DIPLOMATIC_MODIFIER_MAP = {0: 0, 1: -1, 2: -3, 3: -6, 4: -10, 5: -15}

# ════════════════════════════════════════════════════════════════════
# VECTOR DESCRIPTIONS (frontend UI hints)
# ════════════════════════════════════════════════════════════════════
VECTOR_DESCRIPTIONS = {
    'us_pressure': (
        'US pressure on Venezuela: sanctions tempo, executive rhetoric, military '
        'posture, regulatory actions. Currently in EASING/DÉTENTE phase but '
        'fragile.'
    ),
    'regime_legitimacy': (
        'Venezuelan regime legitimacy: Delcy 90-day cap question, NA legitimacy, '
        'opposition strength, internal-security cohesion. Inverse of opposition.'
    ),
    'adversary_access': (
        'Russia/China/Iran cooperation signals with Venezuela. Currently quieter '
        'due to US-VZ détente — sponsor axes likely receding.'
    ),
    'oil_extraction': (
        'PDVSA production levels, Chevron license status, dark fleet activity, '
        'sanctions waivers/revocations affecting Venezuelan oil sector.'
    ),
    'migration_outflow': (
        'Venezuela → Colombia/Brazil/Peru migration flows. Surge = stability '
        'collapse signal. Return flows = de-escalator (bidirectional model).'
    ),
    'essequibo_dispute': (
        'Active territorial dispute with Guyana at ICJ. Major regional risk '
        'vector — overlaps with ExxonMobil Stabroek oil blocks.'
    ),
}


# ════════════════════════════════════════════════════════════════════
# RSS SOURCES (Spanish + English, with weight overrides)
# ════════════════════════════════════════════════════════════════════
RSS_SOURCES = [
    # ── State media (regime line) ──
    ('https://www.telesurtv.net/feed', 'TeleSur (State)', 0.9, 'es'),

    # ── International wire (neutral) ──
    ('https://feeds.reuters.com/reuters/INworldNews', 'Reuters World', 0.95, 'en'),
    ('https://elpais.com/rss/internacional/portada.xml', 'El País Internacional', 0.95, 'es'),

    # ── Indie / opposition Venezuelan media ──
    ('https://caracaschronicles.com/feed/', 'Caracas Chronicles', 1.0, 'en'),
    ('https://efectococuyo.com/feed/', 'Efecto Cocuyo (Indie)', 1.0, 'es'),
    ('https://talcualdigital.com/feed/', 'Tal Cual (Indie)', 1.0, 'es'),
    ('https://elpitazo.net/feed/', 'El Pitazo (Indie)', 1.0, 'es'),

    # ── Human rights / civic ──
    ('https://provea.org/feed/', 'Provea (Human Rights)', 1.0, 'es'),
    ('https://www.observatoriodeconflictos.org.ve/feed', 'OVCS (Protest Tracker)', 0.95, 'es'),

    # ── Google News searches (resilience layer) ──
    ('https://news.google.com/rss/search?q=Delcy+Rodriguez+Venezuela&hl=es&gl=VE&ceid=VE:es',
     'Google News — Delcy', 0.85, 'es'),
    ('https://news.google.com/rss/search?q=Venezuela+Trump+detente&hl=en&gl=US&ceid=US:en',
     'Google News — US-VZ Détente', 0.85, 'en'),
    ('https://news.google.com/rss/search?q=Maduro+trial+New+York&hl=en&gl=US&ceid=US:en',
     'Google News — Maduro Trial', 0.85, 'en'),
    ('https://news.google.com/rss/search?q=Essequibo+Guyana&hl=en&gl=US&ceid=US:en',
     'Google News — Essequibo', 0.85, 'en'),
    ('https://news.google.com/rss/search?q=PDVSA+Chevron+oil&hl=en&gl=US&ceid=US:en',
     'Google News — PDVSA/Chevron', 0.85, 'en'),
]

# ════════════════════════════════════════════════════════════════════
# SOURCE WEIGHTS (canonical pattern from Cuba)
# ════════════════════════════════════════════════════════════════════
SOURCE_WEIGHTS = {
    'rss':      0.85,
    'gdelt':    0.95,
    'newsapi':  0.90,
    'brave':    0.80,
    'telegram': 0.80,
    'reddit':   0.70,
    'bluesky':  0.85,
}

# ════════════════════════════════════════════════════════════════════
# GDELT QUERIES (multi-language)
# ════════════════════════════════════════════════════════════════════
GDELT_QUERIES = {
    'venezuela_general_en':  ('"Venezuela" AND ("Maduro" OR "Delcy" OR "Caracas")', 'eng'),
    'venezuela_general_es':  ('"Venezuela" AND ("Maduro" OR "Delcy" OR "Caracas")', 'spa'),
    'venezuela_detente':     ('"Venezuela" AND ("Trump" OR "détente" OR "sanctions")', 'eng'),
    'venezuela_oil':         ('"Venezuela" AND ("PDVSA" OR "Chevron" OR "oil")', 'eng'),
    'venezuela_essequibo':   ('("Essequibo" OR "Guyana") AND "Venezuela"', 'eng'),
    'venezuela_opposition':  ('"Venezuela" AND ("Machado" OR "Gonzalez" OR "opposition")', 'eng'),
    'venezuela_maduro_trial':('"Maduro" AND ("court" OR "trial" OR "Brooklyn")', 'eng'),
}

# ════════════════════════════════════════════════════════════════════
# REDIS HELPERS (Upstash REST API)
# ════════════════════════════════════════════════════════════════════

def _redis_get(key):
    """GET from Upstash Redis REST."""
    if not UPSTASH_URL or not UPSTASH_TOKEN:
        return None
    try:
        resp = requests.get(
            f"{UPSTASH_URL}/get/{key}",
            headers={'Authorization': f'Bearer {UPSTASH_TOKEN}'},
            timeout=5
        )
        if resp.status_code != 200:
            return None
        result = resp.json().get('result')
        if not result:
            return None
        try:
            return json.loads(result)
        except (TypeError, ValueError):
            return result
    except Exception as e:
        print(f"[VZ Rhetoric] Redis GET failed for {key}: {type(e).__name__}: {e}")
        return None


def _redis_set(key, value, ttl=None):
    """SET to Upstash Redis REST with optional TTL."""
    if not UPSTASH_URL or not UPSTASH_TOKEN:
        return False
    try:
        payload = json.dumps(value) if not isinstance(value, str) else value
        url = f"{UPSTASH_URL}/set/{key}"
        if ttl:
            url += f"?EX={ttl}"
        resp = requests.post(
            url,
            headers={'Authorization': f'Bearer {UPSTASH_TOKEN}'},
            data=payload,
            timeout=5
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"[VZ Rhetoric] Redis SET failed for {key}: {type(e).__name__}: {e}")
        return False


def _redis_lpush_trim(key, value, max_len=336):
    """LPUSH + LTRIM for circular history buffers (Cuba pattern)."""
    if not UPSTASH_URL or not UPSTASH_TOKEN:
        return False
    try:
        payload = json.dumps(value) if not isinstance(value, str) else value
        requests.post(
            f"{UPSTASH_URL}/lpush/{key}",
            headers={'Authorization': f'Bearer {UPSTASH_TOKEN}'},
            data=payload,
            timeout=5
        )
        requests.post(
            f"{UPSTASH_URL}/ltrim/{key}/0/{max_len - 1}",
            headers={'Authorization': f'Bearer {UPSTASH_TOKEN}'},
            timeout=5
        )
        return True
    except Exception as e:
        print(f"[VZ Rhetoric] Redis LPUSH/LTRIM failed for {key}: {type(e).__name__}: {e}")
        return False


# ════════════════════════════════════════════════════════════════════
# DATE PARSING (RSS edge cases)
# ════════════════════════════════════════════════════════════════════

def _parse_pub_date(pub_str):
    """Best-effort RSS date parse. Returns datetime or now()."""
    if not pub_str:
        return datetime.now(timezone.utc)
    formats = [
        '%a, %d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d %H:%M:%S',
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(pub_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            continue
    return datetime.now(timezone.utc)


# ════════════════════════════════════════════════════════════════════
# ARTICLE FETCHERS
# ════════════════════════════════════════════════════════════════════

def _fetch_rss(url, source_name, weight=0.85, lang='es', max_items=20):
    """Fetch one RSS feed. Returns list of articles."""
    articles = []
    try:
        resp = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 Asifah-Analytics-VZ-Tracker'},
            timeout=10
        )
        if resp.status_code != 200:
            return articles

        import re
        items = re.findall(r'<item>(.*?)</item>', resp.text, re.DOTALL | re.IGNORECASE)
        for item in items[:max_items]:
            def extract(tag):
                m = re.search(f'<{tag}>(.*?)</{tag}>', item, re.DOTALL | re.IGNORECASE)
                if not m:
                    return ''
                raw = m.group(1).strip()
                raw = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', raw, flags=re.DOTALL)
                return raw.strip()

            title = extract('title')
            link = extract('link')
            desc = extract('description')
            pubdate = extract('pubDate')
            if not title:
                continue
            articles.append({
                'title':                 title,
                'description':           desc,
                'content':               title,
                'url':                   link,
                'publishedAt':           pubdate,
                'language':              lang,
                'feed_type':             'rss',
                'source':                {'name': source_name},
                'source_weight_override': weight,
            })
    except Exception as e:
        print(f"[VZ Rhetoric] RSS fetch failed ({source_name}): {type(e).__name__}: {str(e)[:80]}")
    return articles


def _fetch_gdelt(query, language='eng', days=3, max_records=25):
    """GDELT Doc API with 8s timeout + 429 short-circuit."""
    try:
        url = (
            f"https://api.gdeltproject.org/api/v2/doc/doc?query={quote_plus(query)}"
            f"&mode=ArtList&format=json&maxrecords={max_records}"
            f"&sourcelang={language}&timespan={days}d"
        )
        resp = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 Asifah-Analytics-VZ-Tracker'},
            timeout=8
        )
        if resp.status_code == 429:
            print(f"[VZ Rhetoric] GDELT 429 — short-circuit")
            return []
        if resp.status_code != 200:
            return []
        try:
            data = resp.json()
        except ValueError:
            return []
        out = []
        for art in data.get('articles', []):
            out.append({
                'title':                 art.get('title', ''),
                'description':           art.get('seendate', ''),
                'content':               art.get('title', ''),
                'url':                   art.get('url', ''),
                'publishedAt':           art.get('seendate', ''),
                'language':              language,
                'feed_type':             'gdelt',
                'source':                {'name': art.get('domain', 'GDELT')},
            })
        return out
    except Exception as e:
        print(f"[VZ Rhetoric] GDELT fetch failed: {type(e).__name__}: {str(e)[:80]}")
        return []


def _fetch_newsapi(query='Venezuela', days=3, max_records=30, language='en'):
    """NewsAPI fetcher with quota guard."""
    if not NEWSAPI_KEY:
        return []
    try:
        from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')
        url = (
            f"https://newsapi.org/v2/everything?q={quote_plus(query)}"
            f"&from={from_date}&sortBy=publishedAt&pageSize={max_records}"
            f"&language={language}&apiKey={NEWSAPI_KEY}"
        )
        resp = requests.get(url, timeout=8)
        if resp.status_code != 200:
            return []
        try:
            data = resp.json()
        except ValueError:
            return []
        out = []
        for art in data.get('articles', []):
            out.append({
                'title':                 art.get('title', ''),
                'description':           art.get('description', ''),
                'content':               (art.get('title', '') or '') + ' ' + (art.get('description', '') or ''),
                'url':                   art.get('url', ''),
                'publishedAt':           art.get('publishedAt', ''),
                'language':              language,
                'feed_type':             'newsapi',
                'source':                art.get('source', {'name': 'NewsAPI'}),
            })
        return out
    except Exception as e:
        print(f"[VZ Rhetoric] NewsAPI fetch failed: {type(e).__name__}: {str(e)[:80]}")
        return []


def _fetch_brave(query='Venezuela', max_records=15):
    """Brave Search API fallback (tertiary)."""
    if not BRAVE_API_KEY:
        return []
    try:
        resp = requests.get(
            f"https://api.search.brave.com/res/v1/news/search?q={quote_plus(query)}&count={max_records}",
            headers={
                'X-Subscription-Token': BRAVE_API_KEY,
                'Accept': 'application/json',
            },
            timeout=8
        )
        if resp.status_code != 200:
            return []
        try:
            data = resp.json()
        except ValueError:
            return []
        out = []
        for art in data.get('results', []):
            out.append({
                'title':                 art.get('title', ''),
                'description':           art.get('description', ''),
                'content':               (art.get('title', '') or '') + ' ' + (art.get('description', '') or ''),
                'url':                   art.get('url', ''),
                'publishedAt':           art.get('age', ''),
                'language':              'en',
                'feed_type':             'brave',
                'source':                {'name': art.get('source', 'Brave')},
            })
        return out
    except Exception as e:
        print(f"[VZ Rhetoric] Brave fetch failed: {type(e).__name__}: {str(e)[:80]}")
        return []


def _fetch_all_articles():
    """Aggregate articles from all sources. Uses circuit breaker on GDELT."""
    all_articles = []
    source_counts = {'rss': 0, 'gdelt': 0, 'newsapi': 0, 'brave': 0,
                     'telegram': 0, 'reddit': 0, 'bluesky': 0}

    # ── RSS feeds ──
    for url, name, weight, lang in RSS_SOURCES:
        items = _fetch_rss(url, name, weight=weight, lang=lang)
        all_articles.extend(items)
        source_counts['rss'] += len(items)
        time.sleep(0.2)

    # ── GDELT (with circuit breaker) ──
    gdelt_failed = False
    for query_name, (query, lang) in GDELT_QUERIES.items():
        if gdelt_failed:
            break
        items = _fetch_gdelt(query, language=lang)
        if not items:
            gdelt_failed = True  # short-circuit on first failure
        all_articles.extend(items)
        source_counts['gdelt'] += len(items)
        time.sleep(0.5)  # rate limit

    # ── NewsAPI (only if GDELT+RSS < 20) ──
    article_count_so_far = len(all_articles)
    if article_count_so_far < 20:
        for q in ['Venezuela Delcy', 'Maduro court', 'PDVSA Chevron', 'Essequibo Guyana']:
            items = _fetch_newsapi(query=q)
            all_articles.extend(items)
            source_counts['newsapi'] += len(items)

    # ── Brave (tertiary fallback if STILL < 10) ──
    if len(all_articles) < 10:
        items = _fetch_brave(query='Venezuela Delcy Rodriguez')
        all_articles.extend(items)
        source_counts['brave'] += len(items)

    # Dedupe by URL
    seen_urls = set()
    deduped = []
    for art in all_articles:
        u = art.get('url', '')
        if u and u not in seen_urls:
            seen_urls.add(u)
            deduped.append(art)
        elif not u:
            deduped.append(art)  # keep articles with no URL (RSS sometimes)

    print(f"[VZ Rhetoric] Fetched {len(deduped)} unique articles "
          f"(rss={source_counts['rss']}, gdelt={source_counts['gdelt']}, "
          f"newsapi={source_counts['newsapi']}, brave={source_counts['brave']})")
    return deduped, source_counts


# ════════════════════════════════════════════════════════════════════
# ARTICLE CLASSIFIER + SCORER (Cuba pattern)
# ════════════════════════════════════════════════════════════════════

def _score_article_for_actor(article, actor_key, actor_def):
    """
    Score one article against one actor's keywords + tripwires.
    Returns (score 0-5, matched_phrase or None).
    """
    text = ((article.get('title', '') or '') + ' ' +
            (article.get('description', '') or '') + ' ' +
            (article.get('content', '') or '')).lower()
    if not text.strip():
        return 0, None

    # Tripwires (severity 4)
    for tw in actor_def.get('tripwires', []):
        if tw.lower() in text:
            return 4, tw

    # Keywords (severity 1 base, weighted by feed_type + source weight)
    matched_kw = None
    for kw in actor_def.get('keywords', []):
        if kw.lower() in text:
            matched_kw = kw
            break

    if not matched_kw:
        return 0, None

    feed_type = article.get('feed_type', 'rss')
    base_weight = article.get('source_weight_override',
                              SOURCE_WEIGHTS.get(feed_type, 0.85))

    # Score = 1 (rhetoric detected) scaled by base_weight bucket
    if base_weight >= 0.95:
        return 2, matched_kw   # high-credibility = warning level
    elif base_weight >= 0.85:
        return 1, matched_kw   # standard = rhetoric level
    else:
        return 1, matched_kw


def _classify_articles(articles):
    """
    Classify articles against all actors. Returns actor_results dict.
    Each entry has: actor_score (max severity), statement_count,
    escalation_level, escalation_label, top_articles, etc.
    """
    actor_results = {}
    for actor_key, actor_def in ACTORS.items():
        actor_results[actor_key] = {
            'name':                 actor_def['name'],
            'flag':                 actor_def['flag'],
            'icon':                 actor_def['icon'],
            'color':                actor_def['color'],
            'role':                 actor_def['role'],
            'description':          actor_def['description'],
            'butterfly_boost':      actor_def.get('butterfly_boost'),
            'actor_score':          0,
            'statement_count':      0,
            'escalation_level':     0,
            'escalation_label':     'Stable',
            'escalation_color':     '#6b7280',
            'escalation_phrase':    None,
            'silence_alert':        True,
            'top_articles':         [],
            'articles':             [],
        }

    for art in articles:
        for actor_key, actor_def in ACTORS.items():
            score, phrase = _score_article_for_actor(art, actor_key, actor_def)
            if score == 0:
                continue
            result = actor_results[actor_key]
            result['statement_count'] += 1
            if score > result['actor_score']:
                result['actor_score'] = score
                result['escalation_phrase'] = phrase
            # Top articles: keep up to 5, sorted by score desc
            art_record = dict(art)
            art_record['escalation_level'] = score
            art_record['trigger_phrase'] = phrase
            result['articles'].append(art_record)
            if len(result['top_articles']) < 5:
                result['top_articles'].append(art_record)

    # Finalize per actor
    for actor_key, result in actor_results.items():
        lvl = result['actor_score']
        result['escalation_level'] = lvl
        meta = ESCALATION_LEVELS.get(lvl, ESCALATION_LEVELS[0])
        result['escalation_label'] = meta['label']
        result['escalation_color'] = meta['color']
        if result['statement_count'] > 0:
            result['silence_alert'] = False

    return actor_results


# ════════════════════════════════════════════════════════════════════
# VECTOR COMPUTERS (6 vectors)
# ════════════════════════════════════════════════════════════════════

def _detect_civilian_pressure(articles):
    """Civilian pressure: blackouts, scarcity, hyperinflation, healthcare."""
    max_level = 0
    signals = []
    for lvl in [5, 4, 3, 2, 1]:
        for phrase in CIVILIAN_PRESSURE_TRIGGERS[lvl]:
            for art in articles:
                text = ((art.get('title', '') or '') + ' ' +
                        (art.get('description', '') or '')).lower()
                if phrase.lower() in text:
                    if lvl > max_level:
                        max_level = lvl
                    signals.append({
                        'article':   art.get('title', ''),
                        'level':     lvl,
                        'phrase':    phrase,
                        'published': art.get('publishedAt', ''),
                    })
                    if len(signals) >= 10:
                        break
            if len(signals) >= 10:
                break
        if max_level >= lvl and signals:
            break
    return max_level, signals


def _detect_migration(articles):
    """Bidirectional migration: out + return. Returns net modifier."""
    out_max = 0
    out_signals = []
    return_max = 0
    return_signals = []

    for lvl in [5, 4, 3, 2, 1]:
        for phrase in MIGRATION_OUT_TRIGGERS[lvl]:
            for art in articles:
                text = ((art.get('title', '') or '') + ' ' +
                        (art.get('description', '') or '')).lower()
                if phrase.lower() in text:
                    if lvl > out_max:
                        out_max = lvl
                    out_signals.append({'article': art.get('title', ''),
                                        'level': lvl, 'phrase': phrase})

    for lvl in [5, 4, 3, 2, 1]:
        for phrase in MIGRATION_RETURN_TRIGGERS[lvl]:
            for art in articles:
                text = ((art.get('title', '') or '') + ' ' +
                        (art.get('description', '') or '')).lower()
                if phrase.lower() in text:
                    if lvl > return_max:
                        return_max = lvl
                    return_signals.append({'article': art.get('title', ''),
                                           'level': lvl, 'phrase': phrase})

    out_mod_map = {0: 0, 1: 1, 2: 3, 3: 5, 4: 7, 5: 8}
    ret_mod_map = {0: 0, 1: -1, 2: -3, 3: -5, 4: -7, 5: -8}
    net_mod = out_mod_map[out_max] + ret_mod_map[return_max]
    return out_max, out_signals, return_max, return_signals, net_mod


def _detect_oil_extraction(articles):
    """PDVSA / Chevron / dark fleet detection."""
    max_level = 0
    signals = []
    for lvl in [5, 4, 3, 2, 1]:
        for phrase in OIL_EXTRACTION_TRIGGERS[lvl]:
            for art in articles:
                text = ((art.get('title', '') or '') + ' ' +
                        (art.get('description', '') or '')).lower()
                if phrase.lower() in text:
                    if lvl > max_level:
                        max_level = lvl
                    signals.append({'article': art.get('title', ''),
                                    'level': lvl, 'phrase': phrase})
                    if len(signals) >= 8:
                        break
            if len(signals) >= 8:
                break
        if max_level >= lvl and signals:
            break
    return max_level, signals


def _detect_essequibo(articles):
    """Territorial dispute escalation."""
    max_level = 0
    signals = []
    for lvl in [5, 4, 3, 2, 1]:
        for phrase in ESSEQUIBO_TRIGGERS[lvl]:
            for art in articles:
                text = ((art.get('title', '') or '') + ' ' +
                        (art.get('description', '') or '')).lower()
                if phrase.lower() in text:
                    if lvl > max_level:
                        max_level = lvl
                    signals.append({'article': art.get('title', ''),
                                    'level': lvl, 'phrase': phrase})
                    if len(signals) >= 6:
                        break
            if len(signals) >= 6:
                break
        if max_level >= lvl and signals:
            break
    return max_level, signals


def _detect_diplomatic_track(articles):
    """
    US-VZ détente / diplomatic track detection.
    Canonical pattern from Iran/Israel/Lebanon trackers.
    Returns (max_level, signals, modifier).
    """
    max_level = 0
    signals = []
    for lvl in [5, 4, 3, 2, 1]:
        for phrase in DIPLOMATIC_TRIGGERS[lvl]:
            for art in articles:
                text = ((art.get('title', '') or '') + ' ' +
                        (art.get('description', '') or '')).lower()
                if phrase.lower() in text:
                    if lvl > max_level:
                        max_level = lvl
                    signals.append({'article': art.get('title', ''),
                                    'level': lvl, 'phrase': phrase})
                    if len(signals) >= 6:
                        break
            if len(signals) >= 6:
                break
        if max_level >= lvl and signals:
            break
    modifier = DIPLOMATIC_MODIFIER_MAP.get(max_level, 0)
    return max_level, signals, modifier


def _compute_vectors(actor_results, civ_press_lvl, oil_lvl, essequibo_lvl,
                     migration_net_mod):
    """
    Compute 6 composite vectors from actor scores + signal levels.
    Returns dict with us_pressure, regime_legitimacy, adversary_access,
    oil_extraction, migration_outflow, essequibo_dispute.
    """
    def max_score(*actor_keys):
        return max((actor_results.get(k, {}).get('actor_score', 0)
                    for k in actor_keys), default=0)

    us_pressure = max_score('us_government', 'us_sanctions_regulatory',
                            'us_military_posture', 'us_vz_envoys')

    # Regime legitimacy: opposition strength INVERSE + government fracture
    opp = actor_results.get('vz_opposition', {}).get('actor_score', 0)
    govt_int = max_score('vz_delcy_rodriguez', 'vz_jorge_rodriguez',
                         'vz_yvan_gil', 'vz_internal_security')
    # If opposition is high AND govt cohesion is low → high fracture
    regime_legitimacy = max(opp, max(0, 4 - govt_int) if opp >= 3 else opp)

    adversary_access = max_score('russia_vz_axis', 'china_vz_axis', 'iran_vz_axis',
                                 'hizballah_vz_signals')

    oil_extraction = oil_lvl
    migration_outflow_lvl = min(5, max(0, migration_net_mod // 2 + 1))
    essequibo_dispute = essequibo_lvl

    return {
        'us_pressure':         us_pressure,
        'regime_legitimacy':   regime_legitimacy,
        'adversary_access':    adversary_access,
        'oil_extraction':      oil_extraction,
        'migration_outflow':   migration_outflow_lvl,
        'essequibo_dispute':   essequibo_dispute,
    }


# ════════════════════════════════════════════════════════════════════
# CROSS-THEATER FINGERPRINT READS
# Reads US, Cuba, Iran, Russia, China fingerprints from Redis.
# ════════════════════════════════════════════════════════════════════

CROSS_THEATER_KEYS = [
    'us', 'cuba', 'iran', 'russia', 'china',
]

def _read_crosstheater_fingerprints():
    """
    Read cross-theater fingerprints. Tries multiple key conventions
    (canonical platform pattern). Returns dict by source theater.
    """
    out = {}
    for theater in CROSS_THEATER_KEYS:
        keys_to_try = [
            f'fingerprint:{theater}:current',
            f'fingerprint:{theater}',
            f'rhetoric:{theater}:latest',
        ]
        for key in keys_to_try:
            fp = _redis_get(key)
            if fp:
                # If it's the full latest payload, extract fingerprint-like fields
                if isinstance(fp, dict):
                    out[theater] = fp
                    break
    return out


# ════════════════════════════════════════════════════════════════════
# FINGERPRINT WRITER
# Writes VZ fingerprint with canonical schema (diplomatic_active /
# ceasefire_level / diplomatic_modifier) so other trackers can read.
# ════════════════════════════════════════════════════════════════════

def _write_vz_fingerprint(actor_results, vectors, civ_press_lvl,
                          migration_net_mod, diplomatic_lvl,
                          diplomatic_mod, essequibo_lvl):
    """
    Write VZ cross-theater fingerprint to Redis. Canonical schema.
    """
    actors_compact = {k: {kk: v[kk] for kk in v if kk not in ('articles', 'top_articles')}
                      for k, v in actor_results.items()}
    fingerprint = {
        'theater':                 'venezuela',
        'theatre_label':           THEATRE_LABELS.get(vectors.get('us_pressure', 0), 'Stable'),
        'theatre_band':            THEATRE_BANDS.get(vectors.get('us_pressure', 0), 'STABLE'),
        'actor_scores':            {k: v.get('actor_score', 0) for k, v in actor_results.items()},
        'vectors':                 vectors,
        'civilian_pressure_level': civ_press_lvl,
        'migration_net_modifier':  migration_net_mod,
        'essequibo_level':         essequibo_lvl,

        # ── Canonical diplomatic schema (mirrors Iran/Israel/Lebanon) ──
        'diplomatic_active':       diplomatic_lvl >= 2,
        'ceasefire_level':         diplomatic_lvl,
        'diplomatic_modifier':     diplomatic_mod,

        'updated_at':              datetime.now(timezone.utc).isoformat(),
    }
    _redis_set(FINGERPRINT_KEY, fingerprint, ttl=86400)
    return fingerprint


# ════════════════════════════════════════════════════════════════════
# L5 RESERVATION CONTRACT — GATE LOGIC
# Real triggers for kinetic / humanitarian / economic.
# Diplomatic = scaffold (audit weekend).
# Kinetic = ceasefire-aware via US-VZ détente (mirrors US tracker).
# ════════════════════════════════════════════════════════════════════

def _compute_vz_l5_gate(actor_results, vectors, civ_press_lvl, oil_lvl,
                        migration_out_max, diplomatic_lvl, essequibo_lvl,
                        cross_theater_fps):
    """
    Per L5 Reservation Contract: VZ L5 "Active Crisis" requires
    explicit axis trigger.

    KINETIC: REAL — fires if us_military_posture L4+ OR essequibo L4+ AND
             US-VZ détente NOT active (ceasefire-aware).
    HUMANITARIAN: REAL — fires if civilian pressure L5 OR migration out L5.
    ECONOMIC: REAL — fires if oil_extraction L5.
    DIPLOMATIC: SCAFFOLD — weekend audit.

    Returns dict with axis flags + reasons + transparency.
    """
    gate = {
        'kinetic':                         False,
        'humanitarian':                    False,
        'economic':                        False,
        'diplomatic':                      False,
        'any':                             False,
        'reason':                          '',
        'l5_ceasefire_suppressed_sources': [],
    }
    reasons = []

    # ── KINETIC L5 (REAL, ceasefire-aware via US-VZ détente) ──
    us_mil = actor_results.get('us_military_posture', {}).get('actor_score', 0)
    essequibo_kinetic = essequibo_lvl >= 4

    if us_mil >= 4 or essequibo_kinetic:
        # Check for active US-VZ détente (ceasefire-analog)
        us_fp = cross_theater_fps.get('us', {}) if isinstance(cross_theater_fps, dict) else {}
        # Also check VZ's own diplomatic level
        vz_detente_active = diplomatic_lvl >= CEASEFIRE_THRESHOLD
        # AND the US side must reciprocate via lifted sanctions / embassy etc.
        us_partner_detente = (us_fp.get('diplomatic_active') and
                              us_fp.get('ceasefire_level', 0) >= CEASEFIRE_THRESHOLD)

        if vz_detente_active and us_partner_detente:
            # Kinetic L5 suppressed by US-VZ détente
            gate['l5_ceasefire_suppressed_sources'].append({
                'source':           'us',
                'reason':           f'us_military_posture L{us_mil} + essequibo L{essequibo_lvl}',
                'ceasefire_level':  diplomatic_lvl,
                'note':             f'Kinetic L5 conditions present but suppressed by active US-VZ détente (level {diplomatic_lvl})',
            })
        else:
            gate['kinetic'] = True
            sources = []
            if us_mil >= 4:
                sources.append(f'us_military L{us_mil}')
            if essequibo_kinetic:
                sources.append(f'essequibo L{essequibo_lvl}')
            reasons.append(f'Kinetic: {", ".join(sources)} without active détente')

    # ── HUMANITARIAN L5 (REAL) ──
    if civ_press_lvl >= 5:
        gate['humanitarian'] = True
        reasons.append(f'Humanitarian: civilian pressure L5 (famine/grid collapse/currency total collapse)')
    elif migration_out_max >= 5:
        gate['humanitarian'] = True
        reasons.append(f'Humanitarian: migration outflow L5 (mass exodus crisis)')

    # ── ECONOMIC L5 (REAL) ──
    if oil_lvl >= 5:
        gate['economic'] = True
        reasons.append(f'Economic: PDVSA/oil sector collapse L5 (total halt or sovereign default)')

    # ── DIPLOMATIC L5 (SCAFFOLD — weekend audit) ──
    # Would fire on: full normalization OR full rupture. Not yet detected.

    gate['any'] = any(gate[k] for k in ('kinetic', 'humanitarian', 'economic', 'diplomatic'))
    if reasons:
        gate['reason'] = '; '.join(reasons)
    elif gate['l5_ceasefire_suppressed_sources']:
        gate['reason'] = f"L5 conditions suppressed by active US-VZ détente"
    else:
        gate['reason'] = 'No L5 axis trigger fired'

    return gate


# ════════════════════════════════════════════════════════════════════
# SIGNAL TEXT BUILDER (theatre_high for WHA BLUF)
# ════════════════════════════════════════════════════════════════════

def _build_vz_signal_text(theatre_level, theatre_score, vectors, civ_press_lvl,
                          oil_lvl, migration_net_mod, diplomatic_lvl,
                          essequibo_lvl, l5_gate, l5_capped=False):
    """Build short_text + long_text for VZ's theatre_high signal."""
    label = THEATRE_LABELS.get(theatre_level, 'Stable')

    # Top vector contributors
    top_vectors = sorted(vectors.items(), key=lambda kv: kv[1], reverse=True)[:3]
    vector_brief = ', '.join(f'{k.replace("_", " ")} L{v}' for k, v in top_vectors if v > 0)

    suppressed = l5_gate.get('l5_ceasefire_suppressed_sources', []) if isinstance(l5_gate, dict) else []

    # SHORT TEXT (<=120 chars)
    if suppressed:
        short = f'🇻🇪 VZ L{theatre_level} {label} — détente holding; underlying L5 pressure'
    elif theatre_level >= 4:
        short = f'🇻🇪 VZ L{theatre_level} {label} — {vector_brief}'
    elif theatre_level >= 2:
        short = f'🇻🇪 VZ L{theatre_level} {label} — {vector_brief}'
    else:
        short = f'🇻🇪 VZ L{theatre_level} {label}'

    if len(short) > 120:
        short = short[:117] + '...'

    # LONG TEXT (full picture)
    long_parts = [
        f'🇻🇪 Venezuela at L{theatre_level} {label} (theatre score {theatre_score}/100).'
    ]
    if vector_brief:
        long_parts.append(f'Active vectors: {vector_brief}.')
    if diplomatic_lvl >= 2:
        long_parts.append(f'US-VZ détente: level {diplomatic_lvl} (de-escalator).')
    if civ_press_lvl >= 3:
        long_parts.append(f'Civilian pressure L{civ_press_lvl} (scarcity/blackouts/hyperinflation signals).')
    if oil_lvl >= 3:
        long_parts.append(f'PDVSA/oil sector pressure L{oil_lvl}.')
    if essequibo_lvl >= 2:
        long_parts.append(f'Essequibo dispute L{essequibo_lvl} (ICJ active).')
    if migration_net_mod >= 5:
        long_parts.append(f'Migration outflow net +{migration_net_mod} (exodus rising).')
    elif migration_net_mod <= -3:
        long_parts.append(f'Migration return flow net {migration_net_mod} (returnees rising).')
    if suppressed:
        for s in suppressed:
            long_parts.append(
                f'⚠️ L5 conditions present ({s.get("reason")}) but suppressed by active US-VZ détente (level {s.get("ceasefire_level", 0)}).'
            )
    if l5_capped:
        long_parts.append('L5 axis gate did not fire — capped at L4 ceiling per platform L5 Reservation Contract.')
    long_parts.append('VZ is a hybrid command-node/absorber tracker; reads US/CU/IR/RU/CN fingerprints.')

    return {'short': short, 'long': ' '.join(long_parts)}


# ════════════════════════════════════════════════════════════════════
# COMPOSITE SCORE
# ════════════════════════════════════════════════════════════════════

def _compute_composite_score(actor_results, vectors, civ_press_lvl,
                             oil_lvl, essequibo_lvl, diplomatic_mod,
                             migration_net_mod, commodity_pressure=None):
    """
    Weighted composite for theatre_score (0-100).
    Includes diplomatic_mod as DOWNWARD pressure (canonical pattern).

    May 22 2026: now also reads commodity_pressure (commodity tracker SURGE/elevated)
    so that external commodity dynamics (oil-recovery, food shortages, gold sanctions
    flows) feed into the composite. This catches scenarios where Venezuela's commodity
    posture is reshaping rapidly even when domestic rhetoric volume stays low.
    """
    # Actor-driven baseline
    actor_avg = sum(v.get('actor_score', 0) for v in actor_results.values()) / max(1, len(actor_results))
    actor_component = actor_avg * 10  # 0-50

    # Vector-driven
    vector_max = max(vectors.values()) if vectors else 0
    vector_component = vector_max * 8  # 0-40

    # Signal-level adjusters
    civ_component = civ_press_lvl * 3   # 0-15
    oil_component = oil_lvl * 2          # 0-10
    essequibo_component = essequibo_lvl * 2  # 0-10

    # ── Commodity pressure component (May 22 2026 — VZ baseline calibration) ──
    # commodity_pressure dict has 'alert_level': 'normal'|'low'|'elevated'|'high'|'surge'
    # Translates external commodity reality (oil-major activity, food prices, gold flows)
    # into VZ composite. Conservative weighting: SURGE = +8, elevated = +4, else 0.
    commodity_component = 0
    if commodity_pressure and isinstance(commodity_pressure, dict):
        alert = (commodity_pressure.get('alert_level') or '').lower()
        if alert == 'surge':
            commodity_component = 8
        elif alert == 'high':
            commodity_component = 6
        elif alert == 'elevated':
            commodity_component = 4
        # 'normal' and 'low' contribute 0

    raw = (actor_component + vector_component + civ_component +
           oil_component + essequibo_component + commodity_component)
    raw += migration_net_mod  # +8 to -8 range
    raw += diplomatic_mod      # 0 to -15 (de-escalator)

    return max(0, min(100, int(raw)))


def _composite_to_theatre_level(composite):
    """Map 0-100 composite to L0-L5 theatre_level."""
    if composite >= 80: return 5
    if composite >= 65: return 4
    if composite >= 50: return 3
    if composite >= 35: return 2
    if composite >= 20: return 1
    return 0


# ════════════════════════════════════════════════════════════════════
# TOP SIGNALS BUILDER
# Emits theatre_high signal for WHA BLUF consumption.
# ════════════════════════════════════════════════════════════════════

def _build_top_signals(theatre_level, theatre_score, signal_text, vectors,
                       civ_press_lvl, oil_lvl, essequibo_lvl, l5_gate):
    """Build top_signals[] list for BLUF consumption."""
    signals = []

    # theatre_high signal (always emitted)
    if theatre_level >= 2:
        signals.append({
            'category':    'theatre_high',
            'theatre':     'venezuela',
            'level':       theatre_level,
            'score':       theatre_score,
            'short_text':  signal_text['short'],
            'long_text':   signal_text['long'],
            'icon':        ESCALATION_LEVELS.get(theatre_level, ESCALATION_LEVELS[0])['icon'],
            'color':       ESCALATION_LEVELS.get(theatre_level, ESCALATION_LEVELS[0])['color'],
            'priority':    11,
            'l5_gate':     l5_gate,
        })

    # Essequibo as its own signal if elevated
    if essequibo_lvl >= 3:
        signals.append({
            'category':    'essequibo_dispute',
            'theatre':     'venezuela',
            'level':       essequibo_lvl,
            'short_text':  f'🗺️ Essequibo dispute L{essequibo_lvl} — ICJ active, territorial tensions',
            'long_text':   f'Venezuela-Guyana Essequibo territorial dispute at L{essequibo_lvl}. ICJ case active. ExxonMobil Stabroek oil blocks in disputed area. Delcy attended The Hague May 9.',
            'icon':        '🗺️',
            'color':       '#16a34a',
            'priority':    9,
        })

    # Civilian pressure signal if high
    if civ_press_lvl >= 3:
        signals.append({
            'category':    'civilian_pressure',
            'theatre':     'venezuela',
            'level':       civ_press_lvl,
            'short_text':  f'⚡ VZ civilian pressure L{civ_press_lvl} — scarcity/blackouts',
            'long_text':   f'Venezuelan civilian pressure at L{civ_press_lvl}. Blackouts, food/medicine scarcity, hyperinflation signals detected.',
            'icon':        '⚡',
            'color':       '#f97316',
            'priority':    8,
        })

    # Oil extraction signal if high
    if oil_lvl >= 3:
        signals.append({
            'category':    'oil_extraction',
            'theatre':     'venezuela',
            'level':       oil_lvl,
            'short_text':  f'🛢️ PDVSA pressure L{oil_lvl}',
            'long_text':   f'Venezuelan oil sector pressure at L{oil_lvl}. PDVSA production, Chevron license, dark fleet signals.',
            'icon':        '🛢️',
            'color':       '#71717a',
            'priority':    7,
        })

    return signals


# ════════════════════════════════════════════════════════════════════
# SOURCE COUNTS HELPER
# ════════════════════════════════════════════════════════════════════

def _compute_source_counts(articles):
    """Tally articles per source type."""
    counts = {'rss': 0, 'gdelt': 0, 'newsapi': 0, 'brave': 0,
              'telegram': 0, 'reddit': 0, 'bluesky': 0}
    for art in articles:
        ft = art.get('feed_type', 'rss')
        if ft in counts:
            counts[ft] += 1
    return counts


# ════════════════════════════════════════════════════════════════════
# MAIN SCAN ORCHESTRATOR
# ════════════════════════════════════════════════════════════════════

_scan_lock = threading.Lock()
_scan_running = False


def run_venezuela_rhetoric_scan(force=False):
    """Run a full Venezuela rhetoric scan. Returns the result dict."""
    global _scan_running
    with _scan_lock:
        if _scan_running and not force:
            print('[VZ Rhetoric] Scan already running, skipping')
            return None
        _scan_running = True

    start_time = time.time()
    print(f'[VZ Rhetoric] === Starting scan at {datetime.now(timezone.utc).isoformat()} ===')

    try:
        # Phase 1: fetch articles
        print('[VZ Rhetoric] Phase 1: fetching articles...')
        articles, source_counts = _fetch_all_articles()

        # Phase 2: classify by actor
        print('[VZ Rhetoric] Phase 2: classifying by actor...')
        actor_results = _classify_articles(articles)

        # Phase 3: detect signals
        print('[VZ Rhetoric] Phase 3: detecting signals...')
        civ_press_lvl, civ_signals = _detect_civilian_pressure(articles)
        mig_out_max, mig_out_signals, mig_ret_max, mig_ret_signals, mig_net_mod = _detect_migration(articles)
        oil_lvl, oil_signals = _detect_oil_extraction(articles)
        essequibo_lvl, essequibo_signals = _detect_essequibo(articles)
        diplomatic_lvl, diplomatic_signals, diplomatic_mod = _detect_diplomatic_track(articles)

        # Phase 4: cross-theater reads
        print('[VZ Rhetoric] Phase 4: reading cross-theater fingerprints...')
        cross_theater_fps = _read_crosstheater_fingerprints()
        print(f'[VZ Rhetoric] Read fingerprints from {len(cross_theater_fps)} theaters: {list(cross_theater_fps.keys())}')

        # Phase 4.5: commodity pull (VZ-specific: oil + gold + wheat pressure from ME backend)
        commodity_pressure = {}
        commodity_fingerprints = {}
        if COMMODITY_PROXY_AVAILABLE:
            try:
                print('[VZ Rhetoric] Phase 4.5: pulling commodity pressure...')
                commodity_pressure = get_commodity_pressure('venezuela') or {}
                commodity_fingerprints = get_commodity_fingerprints_for_country('venezuela') or {}
                print(f"[VZ Rhetoric] Commodity pressure: {commodity_pressure.get('commodity_pressure', 0)}, "
                      f"alert: {commodity_pressure.get('alert_level', 'unknown')}, "
                      f"fingerprints: {list(commodity_fingerprints.get('fingerprints', {}).keys())}")
            except Exception as e:
                print(f'[VZ Rhetoric] Commodity pull failed: {type(e).__name__}: {e}')
                commodity_pressure = {}
                commodity_fingerprints = {}
        else:
            print('[VZ Rhetoric] Phase 4.5: commodity proxy unavailable, skipping')

        # Phase 5: vectors
        vectors = _compute_vectors(actor_results, civ_press_lvl, oil_lvl,
                                   essequibo_lvl, mig_net_mod)

        # Phase 6: composite + theatre_level
        # (May 22 2026: commodity_pressure now feeds composite for VZ baseline calibration)
        composite = _compute_composite_score(actor_results, vectors, civ_press_lvl,
                                             oil_lvl, essequibo_lvl, diplomatic_mod,
                                             mig_net_mod, commodity_pressure=commodity_pressure)
        raw_theatre_level = _composite_to_theatre_level(composite)
        print(f'[VZ Rhetoric] Composite: {composite}, raw_theatre_level: L{raw_theatre_level}')

        # Phase 7: L5 Reservation Contract gate
        l5_gate = _compute_vz_l5_gate(actor_results, vectors, civ_press_lvl, oil_lvl,
                                      mig_out_max, diplomatic_lvl, essequibo_lvl,
                                      cross_theater_fps)
        if raw_theatre_level >= 5 and not l5_gate['any']:
            theatre_level = 4
            l5_capped = True
            print(f"[VZ Rhetoric] L5 gate enforced: raw=L5 capped at L4 (reason: {l5_gate['reason']})")
        else:
            theatre_level = raw_theatre_level
            l5_capped = False

        theatre_label = THEATRE_LABELS.get(theatre_level, 'Stable')

        # Phase 8: signal text
        signal_text = _build_vz_signal_text(theatre_level, composite, vectors,
                                            civ_press_lvl, oil_lvl, mig_net_mod,
                                            diplomatic_lvl, essequibo_lvl,
                                            l5_gate, l5_capped)

        # Phase 9: top_signals
        top_signals = _build_top_signals(theatre_level, composite, signal_text,
                                         vectors, civ_press_lvl, oil_lvl,
                                         essequibo_lvl, l5_gate)

        # Phase 9.5: signal interpreter (red lines + executive summary + so-what)
        # Mid-scan call so we can include outputs in the result dict.
        # We pass a PRELIM scan_data snapshot containing what's been computed.
        interpreter_output = {}
        if INTERPRETER_AVAILABLE:
            try:
                prelim_scan_data = {
                    'theatre_level':            theatre_level,
                    'theatre_label':            theatre_label,
                    'theatre_score':            composite,
                    'vectors':                  vectors,
                    'civilian_pressure_level':  civ_press_lvl,
                    'civilian_pressure_signals': civ_signals,
                    'oil_extraction_level':     oil_lvl,
                    'oil_extraction_signals':   oil_signals,
                    'essequibo_level':          essequibo_lvl,
                    'essequibo_signals':        essequibo_signals,
                    'migration_out_signals':    mig_out_signals,
                    'migration_net_modifier':   mig_net_mod,
                    'diplomatic_level':         diplomatic_lvl,
                    'l5_gate':                  l5_gate,
                    'actors':                   {k: {kk: v[kk] for kk in v if kk != 'articles'}
                                                 for k, v in actor_results.items()},
                    'commodity_pressure':       commodity_pressure,
                    'commodity_fingerprints':   commodity_fingerprints,
                }
                interpreter_output = interpret_venezuela_signals(prelim_scan_data)
                print(f"[VZ Rhetoric] Interpreter: {interpreter_output.get('red_lines_count', 0)} red lines, "
                      f"scenario: {interpreter_output.get('so_what', {}).get('scenario', 'unknown')}")

                # Merge commodity-driven top_signals from interpreter into our top_signals
                commodity_top_signals = interpreter_output.get('commodity_top_signals', [])
                if commodity_top_signals:
                    top_signals.extend(commodity_top_signals)
                    # Resort by priority
                    top_signals.sort(key=lambda s: -s.get('priority', 0))
            except Exception as e:
                print(f'[VZ Rhetoric] Interpreter failed: {type(e).__name__}: {e}')
                interpreter_output = {}

        # Phase 10: fingerprint write
        fingerprint = _write_vz_fingerprint(actor_results, vectors, civ_press_lvl,
                                            mig_net_mod, diplomatic_lvl,
                                            diplomatic_mod, essequibo_lvl)

        # Phase 11: build full result
        elapsed = round(time.time() - start_time, 1)
        result = {
            # ── L5 Reservation Contract fields (v1.0.0 May 21 2026, contract-native) ──
            'theatre':                  'venezuela',
            'theatre_level':            theatre_level,
            'theatre_score':            composite,
            'theatre_label':            theatre_label,
            'theatre_band':             THEATRE_BANDS.get(theatre_level, 'STABLE'),
            'theatre_color':            ESCALATION_LEVELS.get(theatre_level, ESCALATION_LEVELS[0])['color'],
            'theatre_escalation_label': theatre_label,
            'signal_text_short':        signal_text['short'],
            'signal_text_long':         signal_text['long'],
            'l5_gate':                  l5_gate,
            'raw_theatre_level':        raw_theatre_level,
            'l5_capped':                l5_capped,
            'source_class':             SOURCE_CLASS,

            # ── Actor results ──
            'actors':                   {k: {kk: v[kk] for kk in v if kk != 'articles'}
                                         for k, v in actor_results.items()},
            'actor_display_order':      ACTOR_DISPLAY_ORDER,

            # ── Composite vectors ──
            'vectors':                  vectors,
            'vector_descriptions':      VECTOR_DESCRIPTIONS,

            # ── Civilian pressure ──
            'civilian_pressure_level':  civ_press_lvl,
            'civilian_pressure_label':  ESCALATION_LEVELS.get(civ_press_lvl, ESCALATION_LEVELS[0])['label'],
            'civilian_pressure_signals': civ_signals[:10],

            # ── Migration ──
            'migration_out_level':      mig_out_max,
            'migration_out_label':      ESCALATION_LEVELS.get(mig_out_max, ESCALATION_LEVELS[0])['label'],
            'migration_out_signals':    mig_out_signals[:5],
            'migration_return_level':   mig_ret_max,
            'migration_return_label':   ESCALATION_LEVELS.get(mig_ret_max, ESCALATION_LEVELS[0])['label'],
            'migration_return_signals': mig_ret_signals[:5],
            'migration_net_modifier':   mig_net_mod,
            'migration_net_label':      'Surge' if mig_net_mod >= 5 else 'Quiet' if abs(mig_net_mod) < 3 else 'Mixed' if mig_net_mod > 0 else 'Return',

            # ── Oil ──
            'oil_extraction_level':     oil_lvl,
            'oil_extraction_label':     ESCALATION_LEVELS.get(oil_lvl, ESCALATION_LEVELS[0])['label'],
            'oil_extraction_signals':   oil_signals[:6],

            # ── Essequibo ──
            'essequibo_level':          essequibo_lvl,
            'essequibo_label':          ESCALATION_LEVELS.get(essequibo_lvl, ESCALATION_LEVELS[0])['label'],
            'essequibo_signals':        essequibo_signals[:6],

            # ── Diplomatic (US-VZ détente) ──
            'diplomatic_level':         diplomatic_lvl,
            'diplomatic_label':         ESCALATION_LEVELS.get(diplomatic_lvl, ESCALATION_LEVELS[0])['label'],
            'diplomatic_signals':       diplomatic_signals[:6],
            'diplomatic_modifier':      diplomatic_mod,
            'diplomatic_track_active':  diplomatic_lvl >= 2,

            # ── Top signals ──
            'top_signals':              top_signals,

            # ── Cross-theater ──
            'cross_theater_fps_keys':   list(cross_theater_fps.keys()),

            # ── Commodity pressure (from commodity_proxy_wha) ──
            'commodity_pressure':       commodity_pressure,
            'commodity_fingerprints':   commodity_fingerprints,

            # ── Signal interpreter output ──
            'red_lines':                interpreter_output.get('red_lines', []) if interpreter_output else [],
            'red_lines_count':          interpreter_output.get('red_lines_count', 0) if interpreter_output else 0,
            'executive_summary':        interpreter_output.get('executive_summary', {}) if interpreter_output else {},
            'so_what':                  interpreter_output.get('so_what', {}) if interpreter_output else {},

            # ── Fingerprint ──
            'fingerprint':              fingerprint,

            # ── Meta ──
            'success':                  True,
            'articles_scanned':         len(articles),
            'articles_classified':      sum(v.get('statement_count', 0) for v in actor_results.values()),
            'scan_time_seconds':        elapsed,
            'source_counts':            _compute_source_counts(articles),
            'scanned_at':               datetime.now(timezone.utc).isoformat(),
            'timestamp':                datetime.now(timezone.utc).isoformat(),
            'version':                  '1.0.0 - May 21 2026 (contract-native build)',
        }

        # Phase 12: cache writes
        _redis_set(RHETORIC_CACHE_KEY, result, ttl=CACHE_TTL)
        compact = {k: result.get(k) for k in (
            'theatre_level', 'theatre_score', 'theatre_label',
            'signal_text_short', 'signal_text_long', 'l5_gate',
            'top_signals', 'civilian_pressure_level',
            'oil_extraction_level', 'essequibo_level',
            'diplomatic_level', 'scanned_at',
        )}
        _redis_set(SUMMARY_CACHE_KEY, compact, ttl=CACHE_TTL)

        # ── Phase 13: canonical history snapshot (May 22 2026 reconciled schema) ──
        # Universal fields read by wha_regional_bluf.prose_v2:
        #   theatre_level, theatre_score, scanned_at, red_lines_count
        # Plus VZ-specific vector levels.
        snapshot = {
            'theatre_level':     theatre_level,
            'theatre_score':     composite,
            'scanned_at':        result.get('scanned_at') or datetime.now(timezone.utc).isoformat(),
            'red_lines_count':   len(interpreter_output.get('red_lines', [])) if interpreter_output else 0,
            'civilian_pressure': civ_press_lvl,
            'oil_extraction':    oil_lvl,
            'essequibo':         essequibo_lvl,
            'diplomatic':        diplomatic_lvl,
        }
        _redis_lpush_trim(HISTORY_KEY, snapshot, max_len=336)

        print(f'[VZ Rhetoric] === Scan complete in {elapsed}s — L{theatre_level} {theatre_label} (score {composite}) ===')
        return result

    except Exception as e:
        import traceback
        print(f'[VZ Rhetoric] ❌ Scan failed: {type(e).__name__}: {e}')
        traceback.print_exc()
        return {'success': False, 'error': str(e)[:200]}
    finally:
        _scan_running = False


# ════════════════════════════════════════════════════════════════════
# CACHE / BACKGROUND REFRESH HELPERS
# ════════════════════════════════════════════════════════════════════

def get_venezuela_rhetoric_cache():
    """Return cached result or None."""
    return _redis_get(RHETORIC_CACHE_KEY)


def _background_refresh():
    """
    Background thread: refresh VZ scan every SCAN_INTERVAL_HOURS hours.
    Boot delay lets Render warm up before first scan kicks off.
    Pattern mirrors Cuba/Chile/Peru/US — canonical platform behavior.
    """
    time.sleep(90)  # Boot delay — let Render warm up
    while True:
        try:
            print(f'[VZ Rhetoric] Background refresh starting...')
            run_venezuela_rhetoric_scan(force=True)
        except Exception as e:
            print(f'[VZ Rhetoric] Background refresh error: {str(e)[:120]}')
        # Sleep until next scheduled refresh
        time.sleep(SCAN_INTERVAL_HOURS * 3600)


def start_background_refresh():
    """Start the persistent background refresh thread (12hr cadence)."""
    t = threading.Thread(target=_background_refresh, daemon=True)
    t.start()
    print(f'[VZ Rhetoric] Background refresh thread started — every {SCAN_INTERVAL_HOURS}hr')
    return t


# ════════════════════════════════════════════════════════════════════
# ENDPOINT REGISTRATION
# ════════════════════════════════════════════════════════════════════

def register_venezuela_rhetoric_endpoints(app):
    """Register /api/rhetoric/venezuela endpoints on the Flask app."""

    @app.route('/api/rhetoric/venezuela', methods=['GET'])
    def venezuela_rhetoric():
        force = request.args.get('force', '').lower() in ('true', '1', 'yes')

        if not force:
            cached = _redis_get(RHETORIC_CACHE_KEY)
            if cached:
                cached['from_cache'] = True
                return jsonify(cached)

        # Non-blocking scan with 25s timeout; fall back to cache if scan exceeds
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(run_venezuela_rhetoric_scan, True)
        executor.shutdown(wait=False)

        try:
            result = future.result(timeout=25)
            if result:
                result['from_cache'] = False
                return jsonify(result)
            # Scan in progress; fall through to cache
            cached = _redis_get(RHETORIC_CACHE_KEY)
            if cached:
                cached['from_cache'] = True
                cached['scan_triggered'] = True
                return jsonify(cached)
            return jsonify({'success': False, 'error': 'Scan in progress, no cache yet'}), 503
        except Exception:
            cached = _redis_get(RHETORIC_CACHE_KEY)
            if cached:
                cached['from_cache'] = True
                cached['scan_triggered'] = True
                return jsonify(cached)
            return jsonify({'success': False, 'error': 'Scan timeout, no cache available'}), 503

    @app.route('/api/rhetoric/venezuela/summary', methods=['GET'])
    def venezuela_rhetoric_summary():
        cached = _redis_get(SUMMARY_CACHE_KEY)
        if not cached:
            return jsonify({'success': False, 'error': 'No data yet — trigger a scan first'}), 404
        return jsonify({'success': True, **cached, 'from_cache': True})

    @app.route('/api/rhetoric/venezuela/history', methods=['GET'])
    def venezuela_rhetoric_history():
        # Fetch list from Redis
        try:
            resp = requests.get(
                f"{UPSTASH_URL}/lrange/{HISTORY_KEY}/0/-1",
                headers={'Authorization': f'Bearer {UPSTASH_TOKEN}'},
                timeout=5,
            )
            if resp.status_code != 200:
                return jsonify({'success': False, 'error': 'Redis fetch failed'}), 500
            raw = resp.json().get('result', [])
            history = []
            for entry in raw:
                try:
                    history.append(json.loads(entry))
                except (TypeError, ValueError):
                    continue
            return jsonify({'success': True, 'history': history, 'count': len(history)})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)[:120]}), 500

    @app.route('/api/rhetoric/venezuela/refresh', methods=['POST', 'GET'])
    def venezuela_rhetoric_refresh():
        """Trigger a background scan; returns immediately."""
        start_background_refresh()
        return jsonify({'success': True, 'message': 'Background scan triggered'})

    print('[VZ Rhetoric] Endpoints registered: /api/rhetoric/venezuela, /summary, /history, /refresh')


# ════════════════════════════════════════════════════════════════════
# MODULE LOAD BANNER
# ════════════════════════════════════════════════════════════════════
print(f'[VZ Rhetoric] Module loaded — {len(ACTORS)} actors, 6 vectors, '
      f'L5 contract-native (v1.0.0 May 21 2026)')
