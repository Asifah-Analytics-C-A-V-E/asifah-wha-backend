"""
Venezuela Signal Interpreter — v1.0.0 (May 21 2026)

MVP build: red lines + executive summary + so-what factor.
Historical matches deferred to v1.1 (research-intensive).

Imported by rhetoric_tracker_venezuela.py at scan-time (Phase 9+).
Output feeds: top_signals tuning, frontend prose, BLUF context.

Mirrors Peru/Chile pattern (build_top_signals + build_so_what_factor +
interpret_X_signals wrapper).

═══════════════════════════════════════════════════════════════════
KEY PATTERNS (May 2026 reality)
═══════════════════════════════════════════════════════════════════
1. US-VZ DÉTENTE: Trump cooperation rhetoric + Delcy delisting +
   embassy reopening + Chevron license + 621+ political prisoner
   releases. ACTS AS L5 SUPPRESSOR for kinetic axis.
2. DELCY 90-DAY CAP EXPIRY: May 4 deadline came and went without
   public NA vote. Legal continuity contested. Real fracture signal.
3. CABELLO DUAL ROLE: sitting Interior Minister + sole at-large
   indicted co-defendant. He's the wild card.
4. ESSEQUIBO: ICJ active, Delcy went to Hague May 9. Territorial
   vector overlaps with ExxonMobil oil blocks.
5. CHAVISMO RESIDUAL: Maduro court appearances, Nicolasito speeches,
   Argentina extradition pending, defense legal fees fight.

Author: Asifah Analytics
"""

import re


# ════════════════════════════════════════════════════════════════════
# LEVEL HELPERS
# ════════════════════════════════════════════════════════════════════

_LEVEL_RANK = {
    'baseline':       0,
    'rhetoric':       1,
    'warning':        2,
    'confrontation': 3,
    'coercion':       4,
    'active crisis':  5,
}

def _level_rank(label_or_int):
    if isinstance(label_or_int, int):
        return label_or_int
    if isinstance(label_or_int, str):
        return _LEVEL_RANK.get(label_or_int.lower(), 0)
    return 0


def _max_level(levels):
    return max((_level_rank(l) for l in levels), default=0)


# ════════════════════════════════════════════════════════════════════
# RED LINES MODULE
# Explicit tripwires that, when crossed, fire emergency flags.
# These are the platform's "we are watching for THIS" surface.
# ════════════════════════════════════════════════════════════════════

RED_LINES = {

    # ── DETENTE COLLAPSE (kinetic L5 firing condition) ──
    'rl_detente_collapse': {
        'name':         'US-VZ Détente Collapse',
        'severity':     5,
        'category':     'kinetic',
        'short_text':   '🚨 US-VZ DÉTENTE COLLAPSE — kinetic posture re-escalation',
        'long_text':    (
            'US-VZ détente has collapsed. Signals: second-wave strikes threatened, '
            'embassy withdrawal signals, sanctions re-imposed, Delcy delisting reversed, '
            'or Trump publicly reverses on Venezuela. Kinetic L5 axis fires.'
        ),
        'triggers':     [
            'us reverses venezuela', 'second wave venezuela',
            'detente collapse', 'venezuela ultimatum',
            'sanctions reimposed venezuela', 'embassy withdrawn venezuela',
            'delcy delisting reversed', 'trump threatens venezuela',
            'us strike venezuela imminent', 'pentagon escalates venezuela',
        ],
        'actor_check':  ['us_government', 'us_military_posture', 'us_sanctions_regulatory'],
    },

    # ── DELCY OUSTED / RESIGNS / ARRESTED ──
    'rl_delcy_ousted': {
        'name':         'Delcy Rodríguez Out',
        'severity':     5,
        'category':     'regime_legitimacy',
        'short_text':   '🚨 DELCY OUT — interim presidency ends',
        'long_text':    (
            'Delcy Rodríguez has stepped down, been removed, or arrested. '
            'Major regime fracture. Succession question wide open: NA action, '
            'snap election, military intervention, or Cabello play all possible.'
        ),
        'triggers':     [
            'delcy steps down', 'delcy resigns', 'delcy removed',
            'delcy arrested', 'delcy ousted', 'rodriguez ousted',
            'delcy detention', 'delcy challenges trump',
        ],
        'actor_check':  ['vz_delcy_rodriguez'],
    },

    # ── NA DECLARES PRESIDENCY VACANT / SNAP ELECTION ──
    'rl_snap_election': {
        'name':         'Snap Election / NA Declares Vacancy',
        'severity':     4,
        'category':     'regime_legitimacy',
        'short_text':   '⚠️ NA declares presidency vacant — snap election triggered',
        'long_text':    (
            'Maduro-aligned National Assembly has declared the presidency '
            'permanently vacant (post 90-day cap, expired May 4 2026) or '
            'triggered a snap election. Major constitutional event — opposition '
            '(Machado/González) likely to push for fair contest.'
        ),
        'triggers':     [
            'na declares vacancy', 'snap election called venezuela',
            'permanently vacant venezuela', 'na refuses extension',
            'venezuela snap election', 'assembly dissolves venezuela',
        ],
        'actor_check':  ['vz_jorge_rodriguez'],
    },

    # ── MILITARY UPRISING / COUP ──
    'rl_military_uprising': {
        'name':         'FANB Defection / Coup',
        'severity':     5,
        'category':     'kinetic',
        'short_text':   '🚨 FANB DEFECTS / military coup signals',
        'long_text':    (
            'Venezuelan armed forces have defected, mutinied, or staged a coup. '
            'Padrino López position critical. Kinetic L5 fires automatically.'
        ),
        'triggers':     [
            'fanb defects', 'military coup venezuela',
            'padrino defies delcy', 'venezuela military uprising',
            'soldiers fire on civilians', 'padrino arrested',
        ],
        'actor_check':  ['vz_internal_security'],
    },

    # ── MASS OPPOSITION RALLY / GENERAL STRIKE ──
    'rl_mass_opposition': {
        'name':         'Mass Opposition Mobilization',
        'severity':     4,
        'category':     'regime_legitimacy',
        'short_text':   '⚠️ Mass opposition rally / general strike',
        'long_text':    (
            'Machado, González, or MUD has mobilized mass opposition protests '
            'or called a general strike. Tests Delcy government legitimacy '
            'and may force US to take position on opposition recognition.'
        ),
        'triggers':     [
            'mass opposition rally', 'general strike venezuela',
            'opposition declares victory', 'parallel government venezuela',
            'machado mass rally', 'gonzalez declares victory',
        ],
        'actor_check':  ['vz_opposition'],
    },

    # ── CABELLO MOVES (he's the wild card) ──
    'rl_cabello_event': {
        'name':         'Cabello Event',
        'severity':     5,
        'category':     'regime_legitimacy',
        'short_text':   '🚨 CABELLO EVENT — Interior Minister / fugitive co-defendant',
        'long_text':    (
            'Diosdado Cabello — sitting Interior Minister AND only remaining '
            'at-large co-defendant in Maduro indictment — has been arrested, '
            'extradited, has defected, fled, or staged action. Wild card with '
            'cross-cutting implications for US-VZ détente AND regime stability.'
        ),
        'triggers':     [
            'cabello arrested', 'cabello extradited', 'cabello flees',
            'cabello defies delcy', 'cabello coup', 'cabello detention',
            'us targets cabello', 'cabello sanctioned',
        ],
        'actor_check':  ['vz_diosdado_cabello'],
    },

    # ── MADURO COURT EVENTS ──
    'rl_maduro_custody': {
        'name':         'Maduro Custody Event',
        'severity':     4,
        'category':     'chavismo_residual',
        'short_text':   '⚠️ Maduro custody event — death, plea deal, or extradition',
        'long_text':    (
            'Major event in Maduro\'s ongoing US detention: death in custody, '
            'plea deal, hunger strike, extradition (e.g. Argentina), or major '
            'trial ruling. Will trigger Chavismo loyalist response and likely '
            'mass mobilization in VZ. Watch for Nicolasito (son) reactions.'
        ),
        'triggers':     [
            'maduro dies in custody', 'maduro hunger strike',
            'maduro convicted', 'maduro acquitted',
            'maduro plea deal', 'maduro extradited argentina',
            'cilia flores released',
        ],
        'actor_check':  ['vz_chavismo_residual'],
    },

    # ── ESSEQUIBO ESCALATION ──
    'rl_essequibo_escalation': {
        'name':         'Essequibo Kinetic Escalation',
        'severity':     5,
        'category':     'kinetic',
        'short_text':   '🚨 ESSEQUIBO kinetic event — territorial dispute → conflict',
        'long_text':    (
            'Venezuela-Guyana Essequibo dispute has moved from ICJ litigation '
            'to kinetic event: VZ troops cross border, Guyana mobilizes, '
            'ExxonMobil evacuates Stabroek block, US/UK military responds, '
            'or oil block seized. CARICOM in emergency mode.'
        ),
        'triggers':     [
            'venezuela invades guyana', 'venezuela seizes essequibo',
            'venezuela troops essequibo', 'guyana mobilizes',
            'us troops guyana', 'uk troops guyana',
            'exxon evacuates guyana', 'oil block seized',
        ],
        'actor_check':  ['essequibo_guyana_dispute'],
    },

    # ── HEZBOLLAH-VZ DEDICATED WATCH ──
    'rl_hezbollah_event': {
        'name':         'Hezbollah-VZ Operative Event',
        'severity':     4,
        'category':     'special_watch',
        'short_text':   '⚠️ Hezbollah-VZ event — named operative or designation',
        'long_text':    (
            'Hezbollah-Venezuela watch tripped: arrest, designation, or named '
            'operative event in VZ (likely Margarita Island or Lebanese diaspora '
            'financial flow). Watch for OFAC CT designations naming VZ entities.'
        ),
        'triggers':     [
            'hezbollah cell arrested venezuela',
            'hezbollah attack venezuela', 'hezbollah uranium venezuela',
            'us designates hezbollah venezuela', 'margarita raid',
            'hezbollah operative captured venezuela',
        ],
        'actor_check':  ['hizballah_vz_signals'],
    },

    # ── HUMANITARIAN CRISIS L5 ──
    'rl_humanitarian_crisis': {
        'name':         'Humanitarian L5 Crisis',
        'severity':     5,
        'category':     'humanitarian',
        'short_text':   '🚨 Humanitarian L5 — famine / mass exodus / grid collapse',
        'long_text':    (
            'Venezuela has reached humanitarian L5 conditions: declared famine, '
            'total grid collapse, mass exodus surge (>500K/month), or healthcare '
            'system implosion. Triggers L5 axis fire and likely international '
            'response (CARICOM, OAS, UN OCHA).'
        ),
        'triggers':     [
            'venezuela famine declared', 'venezuela hambruna declarada',
            'venezuela total grid collapse', 'venezuela mass exodus',
            'venezuela healthcare implodes', 'venezuela border emergency',
        ],
        'actor_check':  [],  # detected via civilian_pressure_signals + migration_signals
    },

    # ── ECONOMIC L5 CRISIS ──
    'rl_economic_collapse': {
        'name':         'Economic L5 Collapse',
        'severity':     5,
        'category':     'economic',
        'short_text':   '🚨 Economic L5 — bolívar collapse / PDVSA halt / sovereign default',
        'long_text':    (
            'Venezuelan economy has reached L5 conditions: total bolívar collapse, '
            'PDVSA cease operations, or sovereign default declared. Triggers '
            'L5 axis fire. Will cascade to humanitarian crisis if not addressed.'
        ),
        'triggers':     [
            'pdvsa total halt', 'pdvsa cease operations',
            'venezuela sovereign default oil',
            'venezuela bolivar zero', 'venezuela currency total collapse',
        ],
        'actor_check':  [],  # detected via oil_extraction_signals
    },
}


# ════════════════════════════════════════════════════════════════════
# CHECK RED LINES
# ════════════════════════════════════════════════════════════════════

def check_red_lines(scan_data):
    """
    Scan articles + actor results against all red lines.
    Returns list of triggered red lines (most severe first).
    """
    articles = []
    actor_results = scan_data.get('actors', {}) or {}
    civ_signals = scan_data.get('civilian_pressure_signals', []) or []
    mig_out_signals = scan_data.get('migration_out_signals', []) or []
    oil_signals = scan_data.get('oil_extraction_signals', []) or []
    essequibo_signals = scan_data.get('essequibo_signals', []) or []

    # Collect article texts from top_articles per actor
    for actor_key, actor in actor_results.items():
        for art in (actor.get('top_articles', []) or []):
            articles.append({
                'title':       art.get('title', '') or '',
                'description': art.get('description', '') or '',
                'url':         art.get('url', ''),
                'actor_key':   actor_key,
            })
    # Plus signal-context articles
    for sig in civ_signals + mig_out_signals + oil_signals + essequibo_signals:
        articles.append({
            'title':       sig.get('article', '') or '',
            'description': sig.get('phrase', '') or '',
            'url':         '',
            'actor_key':   None,
        })

    triggered = []
    for rl_id, rl in RED_LINES.items():
        for art in articles:
            text = (art['title'] + ' ' + art['description']).lower()
            for trigger in rl['triggers']:
                if trigger.lower() in text:
                    # Optional actor_check: trigger must come from a designated actor
                    if rl['actor_check']:
                        if art['actor_key'] in rl['actor_check']:
                            triggered.append({
                                'rl_id':      rl_id,
                                'name':       rl['name'],
                                'severity':   rl['severity'],
                                'category':   rl['category'],
                                'short_text': rl['short_text'],
                                'long_text':  rl['long_text'],
                                'matched_phrase': trigger,
                                'article_title':  art['title'],
                            })
                            break  # one match per RL is enough
                    else:
                        # Severity-driven RLs (humanitarian/economic) — no actor_check
                        triggered.append({
                            'rl_id':      rl_id,
                            'name':       rl['name'],
                            'severity':   rl['severity'],
                            'category':   rl['category'],
                            'short_text': rl['short_text'],
                            'long_text':  rl['long_text'],
                            'matched_phrase': trigger,
                            'article_title':  art['title'],
                        })
                        break
            if any(t['rl_id'] == rl_id for t in triggered):
                break  # dedupe

    # Sort by severity desc
    triggered.sort(key=lambda t: -t['severity'])
    return triggered


# ════════════════════════════════════════════════════════════════════
# BUILD EXECUTIVE SUMMARY
# Short prose paragraph for frontend "Executive Summary" card
# ════════════════════════════════════════════════════════════════════

def build_executive_summary(scan_data):
    """
    Build a 2-3 sentence executive summary paragraph from scan_data.
    Returns dict with 'headline' + 'paragraph'.
    """
    theatre_level = scan_data.get('theatre_level', 0)
    theatre_label = scan_data.get('theatre_label', 'Baseline')
    composite     = scan_data.get('theatre_score', 0)

    vectors = scan_data.get('vectors', {}) or {}
    civ_press_lvl = scan_data.get('civilian_pressure_level', 0)
    oil_lvl       = scan_data.get('oil_extraction_level', 0)
    essequibo_lvl = scan_data.get('essequibo_level', 0)
    diplomatic_lvl = scan_data.get('diplomatic_level', 0)
    mig_net_mod   = scan_data.get('migration_net_modifier', 0)
    l5_gate       = scan_data.get('l5_gate', {}) or {}
    suppressed    = l5_gate.get('l5_ceasefire_suppressed_sources', []) or []

    actor_results = scan_data.get('actors', {}) or {}

    # Headline
    if l5_gate.get('any'):
        headline = f'🇻🇪 Venezuela at L{theatre_level} {theatre_label} — L5 axis fired ({l5_gate.get("reason", "")})'
    elif suppressed:
        headline = f'🇻🇪 Venezuela at L{theatre_level} {theatre_label} — détente holding, L5 conditions suppressed'
    else:
        headline = f'🇻🇪 Venezuela at L{theatre_level} {theatre_label} (composite {composite}/100)'

    # Build paragraph
    parts = []

    # Lead with regime status
    delcy_lvl = actor_results.get('vz_delcy_rodriguez', {}).get('actor_score', 0)
    if delcy_lvl >= 3:
        parts.append('Delcy Rodríguez under active rhetorical pressure')
    elif delcy_lvl >= 1:
        parts.append('Delcy Rodríguez continues interim presidency')
    else:
        parts.append('Delcy Rodríguez governing quietly')

    # US-VZ posture
    if diplomatic_lvl >= 3:
        parts.append(f'US-VZ détente active at level {diplomatic_lvl} (de-escalator)')
    elif diplomatic_lvl >= 2:
        parts.append(f'US-VZ diplomatic signals emerging at level {diplomatic_lvl}')

    # Key pressure axes
    pressures = []
    if civ_press_lvl >= 3:
        pressures.append(f'civilian pressure L{civ_press_lvl}')
    if oil_lvl >= 3:
        pressures.append(f'oil sector pressure L{oil_lvl}')
    if essequibo_lvl >= 3:
        pressures.append(f'Essequibo dispute L{essequibo_lvl}')
    if mig_net_mod >= 5:
        pressures.append(f'migration outflow surge (+{mig_net_mod})')
    if pressures:
        parts.append('active pressures: ' + ', '.join(pressures))

    # Cabello wild card
    cabello_lvl = actor_results.get('vz_diosdado_cabello', {}).get('actor_score', 0)
    if cabello_lvl >= 3:
        parts.append('Cabello rhetoric elevated (wild card)')

    # Opposition
    opp_lvl = actor_results.get('vz_opposition', {}).get('actor_score', 0)
    if opp_lvl >= 3:
        parts.append(f'opposition (Machado/González) at L{opp_lvl}')

    # Chavismo residual / Maduro court
    chav_lvl = actor_results.get('vz_chavismo_residual', {}).get('actor_score', 0)
    if chav_lvl >= 3:
        parts.append('Maduro detention signals elevated')

    paragraph = '. '.join(p.capitalize() for p in parts) + '.' if parts else 'Venezuela quiet baseline.'

    return {
        'headline':  headline,
        'paragraph': paragraph,
    }


# ════════════════════════════════════════════════════════════════════
# SO WHAT FACTOR
# The analyst's "why this matters" — feeds front-page Three-Altitude
# pattern (Country → Regional → GPI).
# ════════════════════════════════════════════════════════════════════

def build_so_what_factor(scan_data, red_lines_triggered):
    """
    Build the so-what factor: strategic implication of current readings.
    Returns dict with 'scenario', 'factor', 'description', 'watch_for'.
    """
    theatre_level = scan_data.get('theatre_level', 0)
    diplomatic_lvl = scan_data.get('diplomatic_level', 0)
    civ_press_lvl = scan_data.get('civilian_pressure_level', 0)
    oil_lvl       = scan_data.get('oil_extraction_level', 0)
    essequibo_lvl = scan_data.get('essequibo_level', 0)
    l5_gate       = scan_data.get('l5_gate', {}) or {}
    suppressed    = l5_gate.get('l5_ceasefire_suppressed_sources', []) or []

    actor_results = scan_data.get('actors', {}) or {}
    cabello_lvl = actor_results.get('vz_diosdado_cabello', {}).get('actor_score', 0)
    delcy_lvl   = actor_results.get('vz_delcy_rodriguez', {}).get('actor_score', 0)
    us_mil_lvl  = actor_results.get('us_military_posture', {}).get('actor_score', 0)

    # May 22 2026: commodity pressure feeds scenario classification
    commodity_pressure = scan_data.get('commodity_pressure', {}) or {}
    commodity_alert    = (commodity_pressure.get('alert_level') or '').lower()

    # Scenario classification (priority cascade)
    if l5_gate.get('kinetic') and l5_gate.get('any'):
        scenario = 'kinetic_l5_active'
        factor   = 'KINETIC CRISIS'
        description = (
            'Venezuela has entered active kinetic crisis. US-VZ détente has either '
            'collapsed or never held, and military posture is L5. This is the '
            'pre-conflict scenario the platform was designed to surface. Watch '
            'Caribbean naval positioning, SOUTHCOM exercises, Caracas civilian '
            'reactions, and FANB cohesion signals.'
        )
        watch_for = [
            'USS Nimitz movements',
            'Second-wave strike threats',
            'Caracas civilian protests',
            'Russia/China condemnation language',
            'Padrino López public statements',
        ]
    elif l5_gate.get('humanitarian') and l5_gate.get('any'):
        scenario = 'humanitarian_l5_active'
        factor   = 'HUMANITARIAN CRISIS'
        description = (
            'Venezuela has crossed into L5 humanitarian crisis: famine, grid collapse, '
            'mass exodus, or healthcare implosion. Major regional cascade risk — '
            'Colombia, Brazil, Peru migration shocks. International response (UN OCHA, '
            'OAS, CARICOM) will follow.'
        )
        watch_for = [
            'CARICOM emergency convening',
            'UN OCHA appeal',
            'Colombian border crisis declaration',
            'Brazilian/Peruvian border tightening',
        ]
    elif l5_gate.get('economic') and l5_gate.get('any'):
        scenario = 'economic_l5_active'
        factor   = 'ECONOMIC COLLAPSE'
        description = (
            'Venezuela in L5 economic collapse: bolívar gone, PDVSA halted, or '
            'sovereign default. Will cascade to humanitarian within weeks. '
            'US-VZ détente will face stress test — does Washington intervene with '
            'aid or step back?'
        )
        watch_for = [
            'Bolívar exchange rate cascading',
            'PDVSA production zero confirmation',
            'IMF/World Bank engagement signals',
            'Chevron force majeure declaration',
        ]
    elif suppressed:
        scenario = 'detente_suppressing_pressure'
        factor   = 'DÉTENTE SUSTAINING'
        description = (
            'Underlying L5 conditions present (military / Essequibo / civilian) but '
            'US-VZ détente is actively suppressing kinetic axis fire. Platform is '
            'reading this correctly via ceasefire-aware gate. Détente fragility is '
            'the dominant variable — any reversal cascades fast.'
        )
        watch_for = [
            'Chevron license renewal status',
            'Treasury sanctions actions',
            'Trump direct statements on Delcy',
            'Cabello positioning (wild card)',
            'NA legitimacy vote on Delcy term',
        ]
    elif cabello_lvl >= 4:
        scenario = 'cabello_volatility'
        factor   = 'CABELLO WILD CARD'
        description = (
            'Diosdado Cabello rhetoric elevated. He sits in dual role — Interior '
            'Minister AND sole at-large indicted co-defendant. If US targets him, '
            'détente strains. If he defies Delcy, regime fractures. If he flees, '
            'questions about Cuban DGI involvement (he\'s long suspected of '
            'sponsoring Cartel de los Soles).'
        )
        watch_for = [
            'Cabello public appearances',
            'Daniella Cabello (daughter, Tourism Min) signals',
            'US OFAC actions against PSUV elite',
            'Cabello travel pattern signals',
        ]
    elif essequibo_lvl >= 3:
        scenario = 'essequibo_escalation_watch'
        factor   = 'ESSEQUIBO TERRITORIAL PRESSURE'
        description = (
            'Venezuela-Guyana Essequibo dispute escalating at ICJ. ExxonMobil '
            'Stabroek block tensions. Delcy went to Hague May 9 — first international '
            'trip. Possible new domestic narrative play if détente strains internal '
            'cohesion.'
        )
        watch_for = [
            'ICJ procedural rulings',
            'CARICOM positioning',
            'ExxonMobil operations posture',
            'Guyana defense announcements',
            'VZ referendum revival signals',
        ]
    elif civ_press_lvl >= 3 or oil_lvl >= 3:
        scenario = 'structural_pressure_elevated'
        factor   = 'STRUCTURAL PRESSURE BUILD'
        description = (
            'Background structural pressures (civilian / oil) elevated. These are the '
            'long-running pre-conditions that, combined with a Cabello event, '
            'détente shift, or Maduro-court development, could cascade quickly.'
        )
        watch_for = [
            'Blackout duration trends',
            'PDVSA monthly production',
            'Bolívar black-market rate',
            'Food/medicine scarcity reports',
        ]
    elif diplomatic_lvl >= 3:
        scenario = 'detente_steady'
        factor   = 'DÉTENTE STEADY STATE'
        description = (
            'US-VZ détente is the dominant frame. Sanctions easing, embassy '
            'reopened, prisoner releases ongoing. Delcy performing cooperation '
            'while James Story\'s observation holds — "doing just enough to make '
            'it look as if they\'re complying" while waiting for US midterms.'
        )
        watch_for = [
            'Chevron license actions',
            'Political prisoner release pace',
            'Delcy vs. NA 90-day cap dynamics',
            'Sponsor-axis (RU/CN/IR) quiescence signals',
        ]
    elif commodity_alert == 'surge':
        # ── May 22 2026: commodity-driven scenarios ─────────────────────
        # Surge in oil/gold/wheat = real-world commercial/strategic activity
        # that the rhetoric tracker may not yet have picked up in actor signals.
        # Most likely an oil-recovery acceleration (Exxon/Chevron expansion,
        # sanctions-lift trajectory, Rubio-India oil pivot).
        scenario = 'commodity_surge_pressure'
        factor   = 'COMMODITY SURGE — STRATEGIC REPOSITIONING'
        description = (
            'Commodity pressure at SURGE level even as rhetoric tracker reads '
            'baseline-quiet on domestic actors. This pattern is consistent with '
            'oil-recovery acceleration (Exxon, Chevron, Repsol license expansions), '
            'sanctions-lift trajectory, or sponsor-axis commercial repositioning '
            '(Rosneft tanker continuity, CNPC offtake adjustments, Rodriguez '
            'India oil pivot). Strategic activity is happening in the commercial '
            'arena before it surfaces in political rhetoric.'
        )
        watch_for = [
            'Chevron/Exxon/Repsol OFAC license actions',
            'PDVSA monthly export volumes + Jose Terminal traffic',
            'Rodriguez foreign-visit oil agenda (India, China)',
            'White House Venezuela mineral-deal announcements',
            'Rosneft/CNPC tanker continuity at Venezuelan ports',
        ]
    elif commodity_alert in ('high', 'elevated'):
        scenario = 'commodity_pressure_building'
        factor   = 'COMMODITY PRESSURE BUILDING'
        description = (
            'Commodity pressure elevated. Oil/gold/wheat dynamics ahead of '
            'political rhetoric — worth watching whether this leads, lags, or '
            'predicts domestic political moves on PDVSA, Chevron, or sanctions.'
        )
        watch_for = [
            'Oil sector regulatory signals',
            'Food/agricultural import flows',
            'Gold/Orinoco mining arc reporting',
            'Whether rhetoric tracker catches up next cycle',
        ]
    else:
        scenario = 'baseline_quiet'
        factor   = 'BASELINE'
        description = (
            'Venezuela quiet baseline. Tracker is operational and reading low '
            'signal volume across actors.'
        )
        watch_for = [
            'New actor signal emergence',
            'Cross-theater fingerprint changes',
        ]

    # Add red lines triggered (if any) to watch_for
    if red_lines_triggered:
        for rl in red_lines_triggered[:3]:
            watch_for.insert(0, f"🚨 {rl['name']} — TRIGGERED")

    return {
        'scenario':    scenario,
        'factor':      factor,
        'description': description,
        'watch_for':   watch_for,
    }


# ════════════════════════════════════════════════════════════════════
# COMMODITY COUPLING SIGNALS
# Detect convergence between commodity pressure (oil/gold/wheat) and
# actor-driven rhetoric pressure. Two-factor risk = both elevated.
# ════════════════════════════════════════════════════════════════════

# Commodity-to-actor coupling rules. When commodity pressure is high
# AND specific actors are also elevated, fire a convergence signal.
COMMODITY_COUPLINGS = {
    'oil': {
        'related_actors':   ['us_sanctions_regulatory', 'us_government', 'iran_vz_axis',
                             'russia_vz_axis', 'china_vz_axis'],
        'icon':             '🛢️',
        'color':            '#71717a',
        'name':             'Oil',
        'narrative_short':  'Oil pressure + sanctions/sponsor actors elevated → PDVSA convergence risk',
        'narrative_long': (
            'Venezuelan oil sector under multi-front pressure: commodity-market oil '
            'stress combined with elevated US sanctions/regulatory rhetoric and/or '
            'sponsor-axis (RU/CN/IR) activity. Watch for: Chevron license actions, '
            'PDVSA production reports, dark-fleet tanker activity, refinery rehab '
            'announcements from Iran, Rosneft positioning.'
        ),
    },
    'gold': {
        'related_actors':   ['us_sanctions_regulatory', 'vz_diosdado_cabello',
                             'vz_internal_security', 'hizballah_vz_signals'],
        'icon':             '🥇',
        'color':            '#facc15',
        'name':             'Gold',
        'narrative_short':  'Gold pressure + Cabello/security/Hezbollah → Arco Minero sanctions-evasion risk',
        'narrative_long': (
            'Venezuelan gold sector pressure converging with regime-security or '
            'illicit-finance actors. Arco Minero del Orinoco is the primary '
            'sanctions-evasion vehicle; gold-for-gasoline trades with Iran are a '
            'recurring pattern. Hezbollah-VZ watch sits exactly at this intersection. '
            'Watch for: OFAC gold sanctions, named gold-trader designations, gold '
            'export route signals (UAE/Turkey/Iran).'
        ),
    },
    'wheat': {
        'related_actors':   ['russia_vz_axis', 'vz_delcy_rodriguez'],
        'icon':             '🌾',
        'color':            '#84cc16',
        'name':             'Wheat',
        'narrative_short':  'Wheat pressure + Russia-VZ axis → food-security cascade risk',
        'narrative_long': (
            'Venezuelan wheat imports (largely Russian) under pressure. Bread '
            'and arepa flour scarcity has historically triggered protest waves. '
            'A Russian wheat shock combined with VZ détente fragility could '
            'cascade quickly to civilian-pressure L4+. Watch for: Black Sea grain '
            'corridor signals, VZ wheat reserve announcements, bread-line reports.'
        ),
    },
}


def _commodity_coupling_signal(commodity_id, commodity_data, actor_results):
    """
    Build a coupling signal when a commodity is under pressure AND
    related actors are elevated. Returns signal dict or None.
    """
    coupling = COMMODITY_COUPLINGS.get(commodity_id)
    if not coupling:
        return None

    # Extract commodity pressure level (0-5 or alert_level string)
    commodity_lvl = 0
    alert_level = commodity_data.get('alert_level', 'normal') if isinstance(commodity_data, dict) else 'normal'
    alert_to_level = {
        'normal': 0, 'baseline': 0,
        'low': 1, 'elevated': 2, 'warning': 2,
        'high': 3, 'severe': 4, 'critical': 5,
    }
    commodity_lvl = alert_to_level.get(str(alert_level).lower(), 0)

    # Also try numeric pressure if available
    pressure_score = commodity_data.get('commodity_pressure', 0) if isinstance(commodity_data, dict) else 0
    if pressure_score >= 80:
        commodity_lvl = max(commodity_lvl, 5)
    elif pressure_score >= 65:
        commodity_lvl = max(commodity_lvl, 4)
    elif pressure_score >= 50:
        commodity_lvl = max(commodity_lvl, 3)
    elif pressure_score >= 35:
        commodity_lvl = max(commodity_lvl, 2)
    elif pressure_score >= 20:
        commodity_lvl = max(commodity_lvl, 1)

    if commodity_lvl < 2:
        return None  # not elevated enough to couple

    # Check related actor scores
    related_max = 0
    related_top = []
    for actor_key in coupling['related_actors']:
        actor = actor_results.get(actor_key, {})
        score = actor.get('actor_score', 0)
        if score >= 2:
            related_top.append({'actor': actor_key, 'score': score})
            if score > related_max:
                related_max = score

    if related_max < 2:
        return None  # no coupling — commodity-only stress, not convergence

    # Fire coupling signal
    convergence_level = min(5, max(commodity_lvl, related_max))
    actor_brief = ', '.join(t['actor'].replace('_', ' ') for t in related_top[:3])

    return {
        'category':    'commodity_coupling',
        'commodity':   commodity_id,
        'theatre':     'venezuela',
        'level':       convergence_level,
        'short_text':  f"{coupling['icon']} VZ {coupling['name']} L{convergence_level} convergence — {actor_brief}",
        'long_text':   coupling['narrative_long'] + f' Related actors at L{related_max}+: {actor_brief}.',
        'icon':        coupling['icon'],
        'color':       coupling['color'],
        'priority':    9 + convergence_level,  # higher convergence = higher priority
        'related_actors': related_top,
    }


def build_commodity_coupling_signals(scan_data):
    """
    Build commodity coupling signals for all three VZ commodities.
    Returns list of triggered coupling signal dicts.
    """
    commodity_pressure = scan_data.get('commodity_pressure', {}) or {}
    commodity_fingerprints = scan_data.get('commodity_fingerprints', {}) or {}
    actor_results = scan_data.get('actors', {}) or {}

    signals = []

    # Try per-commodity fingerprints first (richer data)
    fps = commodity_fingerprints.get('fingerprints', {}) or {}

    for commodity_id in ('oil', 'gold', 'wheat'):
        # Prefer per-commodity fingerprint if available
        commodity_data = fps.get(commodity_id)
        if not commodity_data:
            # Fall back to country-level pressure (less granular)
            commodity_data = commodity_pressure

        signal = _commodity_coupling_signal(commodity_id, commodity_data, actor_results)
        if signal:
            signals.append(signal)

    return signals


def build_coalition_signals(scan_data):
    """
    Local Coalition convergence signal -- fires ONLY when >=2 external sponsor
    hubs (Iran/Russia/China) are simultaneously elevated on Venezuela. A lone
    patron is NOT a local signal (it surfaces at the GPI as that hub's global
    spread, per the three-altitude rule); a coalition IS -- multiple external
    pressures converging can bend Venezuela's internal and regional dynamics.
    Absence-honest: below the 2-hub gate, returns [] (no manufactured signal).
    """
    coalition    = scan_data.get('coalition', {}) or {}
    hub_presence = scan_data.get('hub_presence', {}) or {}
    level  = coalition.get('level', 0)
    detail = coalition.get('detail', {}) or {}
    hub_count = detail.get('hub_count', 0)

    # Gate: >=2 hubs elevated (coalition level >= 3 on the non-linear ladder)
    if hub_count < 2 or level < 3:
        return []

    elevated = detail.get('elevated_hubs', {}) or {}
    hubs_str = ', '.join(f"{h.title()} L{lv}"
                         for h, lv in sorted(elevated.items(), key=lambda x: -x[1]))
    reading  = detail.get('reading', 'sponsor coalition converging')
    roles = []
    for h in elevated:
        role = (hub_presence.get(h, {}) or {}).get('role')
        if role:
            roles.append(f"{h.title()} ({role})")

    return [{
        'category':   'coalition_convergence',
        'theatre':    'venezuela',
        'level':      level,
        'short_text': f"🕸️ VZ sponsor coalition L{level} — {hub_count} hubs converging ({hubs_str})",
        'long_text':  (
            f"Coalition convergence: {reading}. Elevated sponsor hubs on Venezuela: "
            f"{'; '.join(roles) if roles else hubs_str}. Multiple external patrons "
            f"activating at once erodes US leverage over Caracas and can bend Venezuela's "
            f"internal and regional dynamics. This is a CONVERGENCE indicator, NOT a "
            f"probability of action; each hub is independently sourced and the reader "
            f"completes the inference."
        ),
        'icon':       '🕸️',
        'color':      '#be185d',
        'priority':   9 + level,
    }]


# ════════════════════════════════════════════════════════════════════
# MAIN INTERPRETER WRAPPER
# ════════════════════════════════════════════════════════════════════

def interpret_venezuela_signals(scan_data):
    """
    Main interpreter wrapper called by rhetoric_tracker_venezuela or
    by external consumers (BLUF, GPI). Returns dict with:
        - red_lines: list of triggered red line dicts
        - executive_summary: dict with headline + paragraph
        - so_what: dict with scenario / factor / description / watch_for
        - red_lines_count: int (convenience)
    """
    red_lines_triggered    = check_red_lines(scan_data)
    executive_summary      = build_executive_summary(scan_data)
    commodity_top_signals  = build_commodity_coupling_signals(scan_data)
    coalition_top_signals  = build_coalition_signals(scan_data)
    so_what                = build_so_what_factor(scan_data, red_lines_triggered)

    # Augment so-what watch_for with commodity-coupling alerts
    # (sig['short_text'] already includes the icon, so don't double it)
    if commodity_top_signals and 'watch_for' in so_what:
        for sig in commodity_top_signals[:2]:
            so_what['watch_for'].insert(0, sig['short_text'])

    # Coalition convergence surfaces in the So-What (watch_for + narrative) at >=2 hubs
    if coalition_top_signals:
        cs = coalition_top_signals[0]
        if 'watch_for' in so_what:
            so_what['watch_for'].insert(0, cs['short_text'])
        _cdetail = (scan_data.get('coalition', {}) or {}).get('detail', {}) or {}
        so_what['description'] = (
            so_what.get('description', '').rstrip()
            + f" Sponsor-coalition read: {_cdetail.get('reading', 'multiple sponsors converging')}"
              f" -- multiple external patrons activating at once erode US leverage over Caracas."
        )

    # Earthquake legitimacy-strain surfaces in the So-What when the disaster is
    # straining the transitional government's response (>=L2 political). Ties the
    # legitimacy risk to the relief-as-access opening (the Coalition vector).
    _eq_lvl = scan_data.get('earthquake_political_level', 0)
    if _eq_lvl >= 2 and 'watch_for' in so_what:
        so_what['watch_for'].insert(0,
            f"🏚️ Post-quake legitimacy strain L{_eq_lvl} — transitional govt response capacity")
        so_what['description'] = (
            so_what.get('description', '').rstrip()
            + f" Post-earthquake strain (L{_eq_lvl}): the disaster is testing the transitional"
              f" government's response capacity -- a legitimacy risk for a nascent government, and"
              f" an opening sponsors can exploit via relief-as-access."
        )

    return {
        'red_lines':              red_lines_triggered,
        'red_lines_count':        len(red_lines_triggered),
        'executive_summary':      executive_summary,
        'commodity_top_signals':  commodity_top_signals,
        'coalition_top_signals':  coalition_top_signals,
        'coalition':              scan_data.get('coalition', {}),
        'so_what':                so_what,
    }


# ════════════════════════════════════════════════════════════════════
# MODULE LOAD
# ════════════════════════════════════════════════════════════════════
print(f'[VZ Interpreter] Module loaded — {len(RED_LINES)} red lines defined, MVP v1.0.0')
