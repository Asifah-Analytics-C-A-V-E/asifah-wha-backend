"""
peru_signal_interpreter.py
=========================================================
Peru Rhetoric Signal Interpreter v1.1.0 — Asifah Analytics
Built: May 9, 2026 · v1.1.0 Nov 4, 2026

Generates analytical prose for the Peru rhetoric tracker:
  • build_top_signals()       — canonical top signals (int level, pressure_type, meaning)
  • build_executive_summary() — plain 2-4 sentence headline narrative
  • build_so_what_factor()    — bulleted strategic implications
  • score_alignment_drift()   — great-power alignment-drift read (BRI writ large)

v1.1.0 (Nov 4 2026) -- WHA Phase 2 refresh
  * CANONICAL LEVELS. Signals now carry an INTEGER `level` (0-4) plus
    `level_name` ('elevated' etc.) for the page. The word 'surge' used to
    travel downstream as a string and the GPI read it as L5 "Economic
    Rupture" -- a news-volume count became the platform's top economic alarm.
  * EVIDENCE. A tripwire speaks at its full severity only when 2+ separate
    outlets report it (tracker v1.1.0 grades them). One outlet = "approaching";
    rumour / hedged = not a top signal. Volume alone is capped at 'elevated'.
  * MEANING. Every signal carries `what_it_means` (plain / local / regional /
    global / economy / not_implied) and a one-sentence `meaning`. The GPI
    writer used to receive "Las Bambas -- SURGE-level rhetoric" and could only
    say "hits a severe rhetoric level". Now it is told what Las Bambas is,
    who buys its copper, what a stoppage does to prices, and what is NOT
    implied.
  * ALIGNMENT DRIFT. Band levels lowered one step (Drifting = L3, not L4):
    the Chancay floor is a standing structural fact, and a permanent L4 from
    a fact that does not change was inflating Peru on every cycle.

Facts carried here are dated; re-verify on the 45-day review cycle.

COPYRIGHT (c) 2025-2026 Asifah Analytics. All rights reserved.
"""

import re
from datetime import datetime, timezone

# ============================================
# LEVELS
# ============================================
LEVEL_ORDER = ['low', 'normal', 'elevated', 'high', 'surge']
LEVEL_INT = {'low': 0, 'normal': 1, 'elevated': 2, 'high': 3, 'surge': 4}
ESCALATORY_LEVELS = {'elevated', 'high', 'surge'}
PRIORITY_BY_LEVEL = {0: 2, 1: 4, 2: 7, 3: 10, 4: 12}


def _level_rank(level):
    if isinstance(level, int):
        return level
    try:
        return LEVEL_ORDER.index(level)
    except ValueError:
        return 0


def _max_level(levels):
    if not levels:
        return 'low'
    return max(levels, key=_level_rank)


def _int(level):
    return level if isinstance(level, int) else LEVEL_INT.get(level, 0)


VECTOR_NAMES = {
    'domestic_stability': 'domestic politics and security',
    'resource_sector':    'mining and fisheries',
    'us_alignment':       'US-Peru relations',
    'china_alignment':    'China-Peru relations',
}

ACTOR_PROSE_NAMES = {
    'presidency':       'the presidency',
    'cancilleria':      'the foreign ministry',
    'ffaa':             'the armed forces',
    'mining_sector':    'the mining sector',
    'las_bambas':       'the Las Bambas copper mine',
    'fisheries_sector': 'the anchoveta fishery',
    'vraem_sendero':    'the VRAEM coca valley and Shining Path remnants',
    'us_peru':          'US-Peru relations',
    'china_peru':       'China-Peru relations and the Chancay port',
}

DEESCALATION_PATTERNS = [
    'mesa de diálogo', 'mesa de dialogo', 'dialogue table',
    'consulta previa', 'prior consultation',
    'agreement reached', 'acuerdo alcanzado',
    'tregua', 'truce', 'cese de hostilidades',
    'reanuda operaciones', 'resumes operations',
    'lifts blockade', 'levanta el bloqueo', 'levantan el bloqueo',
]


# ============================================
# WHAT IT MEANS  (dated Nov 4 2026 -- re-verify on the 45-day cycle)
# ============================================
# Sources for the figures: Peru MINEM via Mysteel (Las Bambas 410,829 t
# copper in 2025, ~2% of world mined supply); SMM (Peru ~2.77 Mt copper in
# concentrate in 2025); Mysteel spot TC index negative through 2026.
MEANINGS = {
    'copper': {
        'plain':    ('Peru mines roughly a tenth of the world\'s copper (about 2.8 million tonnes '
                     'in 2025) and is one of the top three producers.'),
        'local':    ('Mining towns, workers and regional budgets depend on it; road blockades in the '
                     'southern corridor are how communities press their demands.'),
        'regional': ('Copper is Peru\'s biggest export and pays a large share of the state\'s '
                     'revenue; Chile is the only bigger supplier nearby.'),
        'global':   ('Copper goes into power grids, wiring, electric vehicles, data centres and '
                     'buildings. In 2026 the ore market is already tight -- smelters have been '
                     'paying miners to take their ore -- so lost Peruvian supply bites faster than usual.'),
        'economy':  ('If supply really falls, the cost reaches cables, appliances, cars and grid '
                     'projects over months, not at the shop next week.'),
        'not_implied': 'More news about Peruvian mining does not mean any mine has stopped.',
    },
    'las_bambas': {
        'plain':    ('Las Bambas is one Chinese-owned (MMG) mine in Peru\'s southern Andes that '
                     'produces about 2% of the world\'s mined copper (about 411,000 tonnes in 2025).'),
        'local':    ('Communities along the road that trucks the ore out (Chumbivilcas, '
                     'Cotabambas) block it to press demands; each blockade is a negotiation as '
                     'much as a protest.'),
        'regional': ('A long stoppage dents Peru\'s exports and tax take, and tests the new '
                     'Fujimori government\'s promise to speed up mining.'),
        'global':   ('Almost all of its ore goes to Chinese smelters. A blockade of a few days '
                     'rarely moves world copper prices; a stoppage lasting weeks squeezes smelters '
                     'first and can lift prices when supply is already tight, as it is in 2026.'),
        'economy':  ('Any price effect reaches wiring, electronics, cars and power grids '
                     'gradually, over months.'),
        'not_implied': ('Busier news coverage of Las Bambas is not a shutdown. Only reported '
                        'suspended operations, confirmed by more than one outlet, is a supply event.'),
    },
    'silver': {
        'plain':    'Peru is one of the world\'s two or three largest silver producers.',
        'global':   ('Silver goes into solar panels, electronics and jewellery; Peruvian '
                     'disruption matters most when solar demand is high.'),
        'economy':  'Effects show up in solar-panel and electronics costs, slowly.',
        'not_implied': 'Mining news volume is not a supply loss.',
    },
    'fishmeal': {
        'plain':    ('Peru runs the world\'s largest single-species fishery (anchoveta) and is the '
                     'biggest exporter of fishmeal.'),
        'local':    ('Quota decisions set the income of the fishing fleet and coastal processing '
                     'towns; cuts bring protests.'),
        'global':   ('Fishmeal feeds farmed salmon, shrimp and pigs. A cancelled or slashed season '
                     '(as in 2023) raises feed costs for fish farms in Norway, Chile and Asia.'),
        'economy':  'Farmed salmon and shrimp prices rise with a lag of months.',
        'not_implied': 'A quota debate is not a cancelled season.',
    },
    'chancay': {
        'plain':    ('Chancay is a Chinese-controlled (COSCO, 60%) deep-water port north of Lima, '
                     'open since November 2024, that cuts shipping time between South America and Asia.'),
        'local':    'It brings jobs and traffic to a small town and makes Peru a regional shipping hub.',
        'regional': ('Brazilian, Chilean and Ecuadorian exporters can route through it; it is the '
                     'flagship of China\'s Belt and Road in South America.'),
        'global':   ('Washington worries it could serve the Chinese navy; disruption would reroute '
                     'Pacific trade and sharpen the US-China contest in the region.'),
        'not_implied': 'Coverage of the port is not a disruption or a military deal.',
    },
    'state_of_emergency': {
        'plain':    ('A state of emergency lets the government suspend some freedoms and send in '
                     'the army. Peru uses them often -- Lima has been under rolling crime '
                     'emergencies -- so only a new or wider declaration is news.'),
        'not_implied': 'A renewal of an existing emergency is routine, not a new crisis.',
    },
    'politics': {
        'plain':    ('Keiko Fujimori has been president since July 28 2026, Peru\'s ninth president '
                     'in about ten years; Congress has removed presidents repeatedly.'),
        'not_implied': 'Political news volume is not a vacancy motion or a crisis.',
    },
}

ACTOR_MEANING_KEY = {
    'las_bambas': 'las_bambas', 'mining_sector': 'copper', 'fisheries_sector': 'fishmeal',
    'china_peru': 'chancay', 'presidency': 'politics',
}
TRIPWIRE_MEANING_KEY = {
    'las_bambas_full_closure': 'las_bambas', 'chancay_disruption': 'chancay',
    'anchoveta_season_cancelled': 'fishmeal', 'fishing_quota_slashed': 'fishmeal',
    'fishing_fleet_protest': 'fishmeal', 'state_of_emergency': 'state_of_emergency',
    'presidential_vacancy': 'politics',
}
COMMODITY_MEANING_KEY = {'copper': 'copper', 'silver': 'silver', 'fishmeal': 'fishmeal',
                         'fish_meal': 'fishmeal', 'anchoveta': 'fishmeal'}


def _meaning(key):
    m = MEANINGS.get(key) or {}
    return dict(m)


def _meaning_sentence(key):
    m = MEANINGS.get(key) or {}
    bits = [m.get('plain'), m.get('global') or m.get('regional')]
    return ' '.join(b for b in bits if b)


def _sig(category, level, short, long_text, pressure_type, meaning_key=None,
         actor=None, sources=None, kind=None, extra=None):
    """One canonical signal. level is an int 0-4."""
    level = max(0, min(4, int(level)))
    s = {
        'category':      category,
        'type':          kind or category,
        'theatre':       'peru',
        'level':         level,
        'level_name':    LEVEL_ORDER[level],
        'priority':      PRIORITY_BY_LEVEL.get(level, 2),
        'pressure_type': pressure_type,
        'short_text':    short[:230],
        'long_text':     long_text,
        'actor':         actor,
        'sources':       sources or [],
    }
    if meaning_key:
        s['what_it_means'] = _meaning(meaning_key)
        s['meaning'] = _meaning_sentence(meaning_key)
    if extra:
        s.update(extra)
    return s


def _has_deescalation(actor_summary):
    text = ' '.join((a.get('title') or '').lower() for a in actor_summary.get('top_articles', []))
    return any(p in text for p in DEESCALATION_PATTERNS)


def _sources(arts, n=3):
    return [{'title': a.get('title', ''), 'url': a.get('url', ''),
             'source': a.get('outlet') or a.get('source', '')} for a in (arts or [])[:n]]


# ============================================
# TRIPWIRE PROSE (plain)
# ============================================
TRIPWIRE_PLAIN = {
    'state_of_emergency':        ('a new state of emergency', 'domestic_stability', 'governance'),
    'las_bambas_full_closure':   ('Las Bambas copper mine operations suspended', 'resource_sector', 'economic'),
    'chancay_disruption':        ('disruption at the Chinese-run Chancay port', 'china_alignment', 'economic'),
    'presidential_vacancy':      ('a move to remove the president', 'domestic_stability', 'governance'),
    'ffaa_intervention':         ('the military stepping into politics', 'domestic_stability', 'governance'),
    'mass_casualty_protest':     ('protesters killed', 'domestic_stability', 'humanitarian'),
    'sendero_attack':            ('an attack by Shining Path remnants or drug gangs', 'domestic_stability', 'kinetic'),
    'extremist_network_signal':  ('a Hizballah / Iran-linked network tied to Peru', 'domestic_stability', 'kinetic'),
    'anchoveta_season_cancelled': ('the anchoveta fishing season cancelled', 'resource_sector', 'economic'),
    'fishing_quota_slashed':     ('the anchoveta quota cut', 'resource_sector', 'economic'),
    'fishing_fleet_protest':     ('a fishing-fleet protest', 'resource_sector', 'economic'),
}


def _tripwire_signal(tw, actor_summaries):
    """Corroborated -> full severity. Single source -> 'approaching' at L2.
    Rumour -> None (shown on the page as rumour, never as a top signal)."""
    tw_id = tw.get('id')
    grade = tw.get('grade', 'corroborated')   # pre-1.1 payloads carried no grade
    what, _vec, ptype = TRIPWIRE_PLAIN.get(tw_id, (tw_id.replace('_', ' '), None, 'kinetic'))
    sev = _int(tw.get('severity', 'high'))
    outlets = tw.get('outlets') or []
    if grade == 'corroborated':
        level = sev
        short = f'Peru: {what} -- reported by {len(outlets) or 2} separate outlets'
    elif grade == 'single_source':
        level = 2
        short = f'Peru: one outlet reports {what} -- not yet corroborated'
    else:
        return None
    mk = TRIPWIRE_MEANING_KEY.get(tw_id)
    long_text = ' '.join(x for x in (
        f'{what[0].upper() + what[1:]}: {"confirmed by " + ", ".join(outlets[:4]) if grade == "corroborated" else "a single report so far"}.',
        _meaning_sentence(mk) if mk else '',
        (MEANINGS.get(mk) or {}).get('not_implied', '') if mk and grade != 'corroborated' else '',
    ) if x)
    actor = tw.get('actor')
    return _sig('tripwire_' + tw_id, level, short, long_text, ptype, mk, actor=actor,
                sources=[{'title': i.get('title'), 'url': i.get('url'), 'source': i.get('outlet')}
                         for i in (tw.get('items') or [])[:3]],
                kind='tripwire', extra={'evidence': grade, 'outlets': outlets})


# ============================================
# TOP SIGNALS
# ============================================
def _commodity_story_signal(commodity_pressure):
    """Composite commodity pressure -- news-signal volume, NOT price. Capped at L3:
    commodity news volume is not an economic rupture (GPI v3.16 ruling)."""
    story = (commodity_pressure or {}).get('_pressure_story') or {}
    alert = (story.get('alert') or 'normal').lower()
    if alert == 'normal':
        return None
    lvl = {'elevated': 2, 'high': 3, 'critical': 3, 'surge': 3}.get(alert, 2)
    escalated = sorted(c for c, a in (story.get('commodities') or {}).items() if a and a != 'normal')
    names = ', '.join(escalated) or 'its export commodities'
    return _sig('commodity_coupling', lvl,
                f'Peru: news about {names} is running hot -- a supply-risk signal, not a measured price move',
                ('Asifah\'s commodity tracker sees heavier-than-usual reporting on ' + names +
                 ' for Peru. This measures news volume and severity, not prices. ' +
                 _meaning_sentence('copper')),
                'economic', 'copper', kind='commodity_coupling',
                extra={'source_link': '/peru-stability.html#commodities'})


def build_top_signals(actor_summaries, tripwires_global, commodity_pressure, crosstheater_amplifiers):
    """Canonical top_signals[] for Peru (v1.1.0 plain, evidence-graded, int levels)."""
    signals = []

    # 1. Tripwires -- one per id, best grade wins
    best = {}
    rank = {'corroborated': 0, 'single_source': 1, 'rumint': 2}
    for tw in tripwires_global or []:
        cur = best.get(tw.get('id'))
        if cur is None or rank.get(tw.get('grade', 'corroborated'), 3) < rank.get(cur.get('grade', 'corroborated'), 3):
            best[tw.get('id')] = tw
    for tw in best.values():
        s = _tripwire_signal(tw, actor_summaries)
        if s:
            signals.append(s)

    # 2. Convergence -- 2+ areas busier than usual at once
    vector_levels = {}
    for a in (actor_summaries or {}).values():
        v = a.get('vector')
        if v and _level_rank(a.get('level', 'low')) > _level_rank(vector_levels.get(v, 'low')):
            vector_levels[v] = a.get('level', 'low')
    elevated = [v for v, lv in vector_levels.items() if lv in ESCALATORY_LEVELS]
    if len(elevated) >= 2:
        names = [VECTOR_NAMES.get(v, v) for v in elevated]
        lvl = min(3, max(_int(vector_levels[v]) for v in elevated))
        signals.append(_sig('convergence', lvl,
                            'Peru: several areas are busier than usual at once -- ' + ' and '.join(names[:3]),
                            ('More than one part of the Peru picture is active in the same week: ' +
                             ', '.join(names) + '. Pressures that usually move separately are moving '
                             'together, which is when a local dispute is most likely to spread.'),
                            'composite', kind='convergence'))

    # 3. Actors busier than usual (volume is capped at 'elevated' upstream)
    covered = {t.get('actor') for t in best.values() if t.get('grade') in ('corroborated', 'single_source')}
    for actor_id, actor in (actor_summaries or {}).items():
        level = actor.get('level', 'low')
        if level not in ESCALATORY_LEVELS or actor_id in covered:
            continue
        name = ACTOR_PROSE_NAMES.get(actor_id, actor.get('name', actor_id))
        n = actor.get('article_count', 0)
        outlets = actor.get('outlet_count') or len(actor.get('sources') or [])
        deesc = _has_deescalation(actor)
        mk = ACTOR_MEANING_KEY.get(actor_id)
        short = (f'Peru: more reporting than usual on {name} ({n} items from {outlets} outlets)'
                 + (' -- much of it about talks or a deal' if deesc else ''))
        long_text = ' '.join(x for x in (
            f'Coverage of {name} is running above its usual weekly level. This counts reporting, '
            f'not events: it says something is happening there, not how serious it is.',
            'Several items describe dialogue or an agreement, which usually means a dispute is being settled.' if deesc else '',
            _meaning_sentence(mk) if mk else '',
            (MEANINGS.get(mk) or {}).get('not_implied', '') if mk else '',
        ) if x)
        ptype = {'resource_sector': 'economic', 'china_alignment': 'diplomatic',
                 'us_alignment': 'diplomatic'}.get(actor.get('vector'), 'governance')
        if actor_id == 'vraem_sendero':
            ptype = 'kinetic'
        signals.append(_sig('actor_volume', _int(level), short, long_text, ptype, mk,
                            actor=actor_id, sources=_sources(actor.get('top_articles')),
                            kind='actor_signal'))

    # 4. Commodity coupling (commodity alert AND sector reporting both up)
    for cid, risk in (commodity_pressure or {}).items():
        if cid.startswith('_') or not isinstance(risk, dict):
            continue
        if risk.get('alert_level') not in ESCALATORY_LEVELS:
            continue
        sector_lvl = max(_int((actor_summaries.get('mining_sector') or {}).get('level', 'low')),
                         _int((actor_summaries.get('las_bambas') or {}).get('level', 'low')))
        lvl = min(3, _int(risk.get('alert_level')), max(sector_lvl, 1) + 1)
        mk = COMMODITY_MEANING_KEY.get(cid, 'copper')
        top = risk.get('top_signal') or {}
        signals.append(_sig('commodity_coupling', lvl,
                            f'Peru: {cid} supply-risk reporting is up while Peruvian mining news is busy',
                            (f'The commodity tracker reads {risk.get("alert_level")} news pressure on {cid}, '
                             f'and Peru is a major producer. ' + _meaning_sentence(mk) + ' ' +
                             (MEANINGS.get(mk) or {}).get('not_implied', '')),
                            'economic', mk, actor='mining_sector', kind='commodity_coupling',
                            sources=[{'title': top.get('title', ''), 'url': top.get('url', ''),
                                      'source': top.get('source', '')}] if top.get('title') else []))

    # 5. Cross-theater amplifiers
    for amp, data in (crosstheater_amplifiers or {}).items():
        if not isinstance(data, dict) or not data.get('active'):
            continue
        text = {
            'china_lac_active':   'China\'s Latin America messaging is active this cycle',
            'china_bri_latam':    'China\'s Belt and Road push in Latin America is active this cycle',
            'iran_latam_active':  'Iran\'s Latin America activity is elevated this cycle',
            'iran_hezbollah_tba': 'Hizballah\'s Tri-Border Area network is active this cycle',
        }.get(amp, amp.replace('_', ' '))
        signals.append(_sig('crosstheater', 1, 'Peru context: ' + text,
                            text + '. It raises the stakes of Peru-side signals but is not a Peru event.',
                            'diplomatic', kind='crosstheater'))

    signals.sort(key=lambda s: (-s['level'], -len(s.get('sources') or [])))
    cs = _commodity_story_signal(commodity_pressure)
    if cs:
        signals.append(cs)
        signals.sort(key=lambda s: -s['level'])
    return signals[:12]


# ============================================
# EXECUTIVE SUMMARY + TOP INDICATOR
# ============================================
def build_top_indicator(actor_summaries, tripwires_global, alignment_drift=None, articles_scanned=None):
    """The one plain sentence to leave with."""
    corro = [t for t in (tripwires_global or []) if t.get('grade', 'corroborated') == 'corroborated']
    single = [t for t in (tripwires_global or []) if t.get('grade') == 'single_source']
    busy = sorted(((k, a) for k, a in (actor_summaries or {}).items()
                   if a.get('level') in ESCALATORY_LEVELS),
                  key=lambda kv: -kv[1].get('score', 0))
    if corro:
        t = max(corro, key=lambda x: _int(x.get('severity', 'high')))
        what = TRIPWIRE_PLAIN.get(t.get('id'), (t.get('id', '').replace('_', ' '),))[0]
        mk = TRIPWIRE_MEANING_KEY.get(t.get('id'))
        main = f'Confirmed by more than one outlet: {what}. ' + ((MEANINGS.get(mk) or {}).get('global') or '')
    elif busy:
        names = [ACTOR_PROSE_NAMES.get(k, k) for k, _ in busy[:2]]
        main = ('Nothing high-impact is confirmed in Peru. Reporting is busier than usual on '
                + ' and '.join(names) + ' -- more news, not a crisis.')
    else:
        main = 'Peru reads quiet: nothing high-impact is confirmed and no area is unusually busy.'
    if single and not corro:
        what = TRIPWIRE_PLAIN.get(single[0].get('id'), (single[0].get('id', '').replace('_', ' '),))[0]
        main += f' Watching: one outlet reports {what}, not yet corroborated.'
    if alignment_drift and alignment_drift.get('band') in ('Drifting', 'Realigning'):
        main += (' Standing backdrop: Peru is drifting toward China economically, anchored by the '
                 'Chancay port -- a long-running fact, not this week\'s news.')
    if articles_scanned is not None and articles_scanned < 30:
        main += ' Coverage is thin this cycle, so quiet may be unread rather than calm.'
    return main


def build_executive_summary(actor_summaries, vector_scores, vector_levels, tripwires_global):
    parts = []
    corro = [t for t in (tripwires_global or []) if t.get('grade', 'corroborated') == 'corroborated']
    elevated = [v for v, lv in (vector_levels or {}).items() if lv in ESCALATORY_LEVELS]
    if corro:
        whats = sorted({TRIPWIRE_PLAIN.get(t.get('id'), (t.get('id'),))[0] for t in corro})
        parts.append('High-impact events are confirmed by more than one outlet: ' + '; '.join(whats[:3]) + '.')
    if elevated:
        parts.append('Reporting is busier than usual on ' +
                     ', '.join(VECTOR_NAMES.get(v, v) for v in elevated) + '.')
    if not corro and not elevated:
        parts.append('Peru reads quiet this cycle: no area is unusually busy and nothing high-impact is confirmed.')
    single = [t for t in (tripwires_global or []) if t.get('grade') == 'single_source']
    if single:
        parts.append('Single-outlet reports not yet corroborated: ' +
                     ', '.join(sorted({TRIPWIRE_PLAIN.get(t.get('id'), (t.get('id'),))[0] for t in single})[:3]) + '.')
    parts.append(MEANINGS['politics']['plain'])
    return ' '.join(parts)


# ============================================
# GREAT-POWER ALIGNMENT DRIFT
# ============================================
# v1.1.0: one step lower across the board. Drifting is a standing structural
# reading (Chancay is built and operating); it belongs at "watch" (L3), not
# "serious pressure" (L4), or Peru carries L4 forever from a fact that does
# not move.
DRIFT_BAND_META = {
    'US-anchored': {'level': 1, 'color': '#38bdf8', 'priority': 4},
    'Contested':   {'level': 2, 'color': '#f59e0b', 'priority': 7},
    'Drifting':    {'level': 3, 'color': '#f97316', 'priority': 8},
    'Realigning':  {'level': 4, 'color': '#dc2626', 'priority': 11},
}

DRIFT_PROFILES = {
    'peru': {
        'flag':            '\U0001F1F5\U0001F1EA',
        'inroad_power':    'China',
        'incumbent_power': 'the US',
        'inroad_actor':    'china_peru',
        'counter_actor':   'us_peru',
        'inroad_tripwires':  ('dual_use_facility', 'diplomatic_anti_us',
                              'security_cooperation', 'major_infra_milestone'),
        'counter_tripwires': ('project_contestation', 'monroe_doctrine_invoked',
                              'us_displacement_push', 'strategic_minerals_pact'),
        'dependency_channel': 'the COSCO-controlled Chancay megaport and copper/silver sales to China',
        'commodity_keys':     ('copper', 'silver'),
        'crosstheater_amp':   'china_lac_active',
        'structural_dependency_baseline': True,
        'precedents': ('the COSCO-operated Chancay megaport -- the flagship Chinese port in '
                       'South America, opened November 2024 and not reversed'),
        'leading_indicators': [
            'Chancay throughput / expansion and COSCO stake moves',
            'Copper and silver sales locked in to Chinese buyers (Las Bambas, Chinalco, Shougang)',
            'China-Peru trade-deal upgrades and Belt-and-Road announcements',
            'Lima saying it has a "sovereign right to choose partners"',
            'US counter-moves -- ambassador pressure, "better partner" offers, congressional scrutiny',
        ],
    },
}

_DRIFT_LEVEL_RANK = {'low': 0, 'normal': 1, 'elevated': 2, 'high': 3, 'surge': 4}


def score_alignment_drift(actor_summaries, tripwires_global, commodity_pressure,
                          crosstheater_amplifiers, country='peru', profile=None):
    """Great-power alignment-drift convergence read. CONVERGENCE, not prediction."""
    prof = profile or DRIFT_PROFILES.get((country or '').lower())
    if not prof:
        return None
    asum = actor_summaries or {}
    inroad_lvl = _DRIFT_LEVEL_RANK.get((asum.get(prof['inroad_actor']) or {}).get('level', 'low'), 0)
    counter_lvl = _DRIFT_LEVEL_RANK.get((asum.get(prof['counter_actor']) or {}).get('level', 'low'), 0)
    tw_ids = {tw.get('id') for tw in (tripwires_global or [])
              if tw.get('grade', 'corroborated') == 'corroborated'}
    inroad_tw = [t for t in prof['inroad_tripwires'] if t in tw_ids]
    counter_tw = [t for t in prof['counter_tripwires'] if t in tw_ids]
    dep_active = bool(prof.get('structural_dependency_baseline', False))
    if not dep_active:
        for ck in prof.get('commodity_keys', ()):
            cp = (commodity_pressure or {}).get(ck) or {}
            if isinstance(cp, dict) and (cp.get('active') or cp.get('level') in ('elevated', 'high', 'surge')):
                dep_active = True
                break
    amp_active = bool((crosstheater_amplifiers or {}).get(prof.get('crosstheater_amp', '')))
    inroad = inroad_lvl + len(inroad_tw) + (1 if dep_active else 0) + (1 if amp_active else 0)
    counter = counter_lvl + len(counter_tw)
    if inroad <= 1:
        band = 'US-anchored'
    elif inroad >= 2 and counter >= 2:
        band = 'Contested'
    elif inroad >= 5 and counter <= 1 and dep_active:
        band = 'Realigning'
    elif (inroad - counter) >= 2:
        band = 'Drifting'
    elif counter >= 2:
        band = 'Contested'
    else:
        band = 'US-anchored'
    floor = False
    if prof.get('structural_dependency_baseline') and band == 'US-anchored':
        band, floor = 'Drifting', True
    ip, cp_, cc = prof['inroad_power'], prof['incumbent_power'], (country or '').title()
    if band == 'US-anchored':
        so_what = (ip + "'s presence in " + cc + " reads as ordinary business this cycle; "
                   + cp_ + "'s position is not being contested.")
    elif band == 'Contested':
        so_what = (ip + ' and ' + cp_ + ' are both actively competing for ' + cc + ' this cycle -- '
                   'a tug-of-war, not a settled choice.')
    elif band == 'Drifting':
        so_what = (cc + ' is tied ever more closely to ' + ip + ' through ' + prof['dependency_channel'] +
                   (', a standing fact rather than this week\'s news.' if floor else
                    ', and ' + ip + '\'s moves are outpacing ' + cp_ + '\'s this cycle.') +
                   ' What it means: trade and investment pull Lima toward Beijing even when politics leans to Washington.')
    else:
        so_what = ('Sustained ' + ip + ' moves, deep dependency (' + prof['dependency_channel'] +
                   ') and little ' + cp_ + ' push-back are consistent with ' + cc +
                   ' settling into ' + ip + '\'s orbit.')
    meta = DRIFT_BAND_META[band]
    return {
        'id': 'bri_inroad_' + (country or '').lower(), 'country': (country or '').lower(),
        'flag': prof.get('flag', ''), 'band': band, 'standing_floor': floor,
        'inroad_power': ip, 'incumbent_power': cp_,
        'inroad_score': inroad, 'counter_score': counter, 'net': inroad - counter,
        'active_inroad_tripwires': inroad_tw, 'active_counter_tripwires': counter_tw,
        'dependency_active': dep_active, 'regional_amp_active': amp_active,
        'so_what_factor': so_what, 'leading_indicators': list(prof['leading_indicators']),
        'precedent': prof['precedents'],
        'disclaimer': ('A convergence / influence indicator, not a prediction of realignment. '
                       + cc + ' keeps full agency over its partners.'),
        'level': meta['level'], 'priority': meta['priority'], 'color': meta['color'],
        'icon': '\U0001F9ED',
    }


def build_alignment_drift_top_signal(drift):
    if not drift or drift.get('band') in (None, 'US-anchored'):
        return None
    floor = drift.get('standing_floor')
    return {
        'priority':      drift['priority'],
        'category':      'alignment_drift',
        'theatre':       drift['country'],
        'level':         drift['level'],
        'level_name':    LEVEL_ORDER[min(4, drift['level'])],
        'pressure_type': 'diplomatic',
        'standing':      bool(floor),
        'icon':          drift['icon'],
        'color':         drift['color'],
        'short_text':    ('Peru: economically tied ever more closely to China (Chancay port, copper sales)'
                          + (' -- a standing fact, not new' if floor else ' -- China\'s moves outpacing the US this cycle')),
        'long_text':     (drift['so_what_factor'] + ' ' + drift['disclaimer'])[:480],
        'what_it_means': _meaning('chancay'),
        'meaning':       _meaning_sentence('chancay'),
    }


# ============================================
# SO WHAT
# ============================================
def build_so_what_factor(actor_summaries, vector_scores, vector_levels, tripwires_global,
                         commodity_pressure, alignment_drift=None):
    """Plain So What bullets: {bullet, weight}."""
    bullets = []
    corro = {t.get('id') for t in (tripwires_global or []) if t.get('grade', 'corroborated') == 'corroborated'}
    single = {t.get('id') for t in (tripwires_global or []) if t.get('grade') == 'single_source'}

    if 'las_bambas_full_closure' in corro:
        m = MEANINGS['las_bambas']
        bullets.append({'bullet': ('Las Bambas has stopped, confirmed by more than one outlet. ' + m['global'] +
                                   ' Watch: how long it lasts, and whether Chinese smelters cut output.'),
                        'weight': 6.0})
    elif 'las_bambas_full_closure' in single:
        bullets.append({'bullet': ('One outlet reports Las Bambas operations suspended; not yet corroborated. '
                                   + MEANINGS['las_bambas']['not_implied']), 'weight': 4.6})
    if 'chancay_disruption' in corro:
        bullets.append({'bullet': ('Disruption at Chancay, confirmed by 2+ outlets. ' + MEANINGS['chancay']['global']),
                        'weight': 5.4})
    if 'state_of_emergency' in corro:
        bullets.append({'bullet': ('A new state of emergency is confirmed. ' + MEANINGS['state_of_emergency']['plain']),
                        'weight': 5.0})
    if 'presidential_vacancy' in corro:
        bullets.append({'bullet': ('A move to remove the president is confirmed by 2+ outlets. Peru has '
                                   'changed presidents repeatedly this decade; a removal would hand power to '
                                   'Congress\'s succession line and unsettle the mining fast-track agenda.'),
                        'weight': 5.6})
    if corro & {'anchoveta_season_cancelled', 'fishing_quota_slashed'}:
        bullets.append({'bullet': 'Anchoveta catch cut, confirmed. ' + MEANINGS['fishmeal']['global'], 'weight': 5.2})
    if 'extremist_network_signal' in corro:
        bullets.append({'bullet': ('A Hizballah / Iran-linked network tied to Peru is reported by 2+ outlets -- '
                                   'out of pattern for Peru; read it with the Tri-Border Area.'), 'weight': 5.3})

    if alignment_drift and alignment_drift.get('band') in ('Contested', 'Drifting', 'Realigning'):
        bullets.append({'bullet': 'China and the US: ' + alignment_drift.get('so_what_factor', ''),
                        'weight': 4.0 if alignment_drift.get('standing_floor') else 5.5})

    if (vector_levels or {}).get('resource_sector') in ESCALATORY_LEVELS and 'las_bambas_full_closure' not in corro:
        bullets.append({'bullet': ('Mining reporting is busier than usual. ' + MEANINGS['copper']['global'] +
                                   ' ' + MEANINGS['copper']['not_implied']), 'weight': 3.6})
    if (vector_levels or {}).get('domestic_stability') in ESCALATORY_LEVELS:
        bullets.append({'bullet': ('Politics and security reporting is busier than usual. ' +
                                   MEANINGS['politics']['plain']), 'weight': 3.2})

    story = (commodity_pressure or {}).get('_pressure_story') or {}
    if (story.get('alert') or 'normal') != 'normal':
        bullets.append({'bullet': ('Commodity news about Peru is running hot (' + story['alert'] +
                                   '). That measures how much is being written, not prices.'),
                        'weight': 3.0})

    if not bullets:
        bullets.append({'bullet': ('Peru reads quiet this cycle. The things that would change that: a '
                                   'confirmed Las Bambas stoppage, a new state of emergency, a move against '
                                   'the president, or trouble at the Chancay port.'), 'weight': 1.0})
    bullets.sort(key=lambda b: -b['weight'])
    return bullets[:7]


# ============================================================
# ELECTION RUNOFF WATCH (Jun 2026 cycle) -- RETIRED Jul 2026, kept dormant
# ============================================================
# Convergence module for the Fujimori-Sanchez runoff. Reports WHICH counting
# and candidate signals are present in the current scan -- it NEVER predicts
# a winner. Market polarity per candidate is an analytical READ of policy
# posture (mining/fiscal), not an endorsement or forecast.

ELECTION_CANDIDATES = {
    'fujimori': {
        'display':     'Keiko Fujimori',
        'party':       'Fuerza Popular (conservative)',
        'keywords':    ['keiko fujimori', 'fujimori', 'fuerza popular'],
        'lead_phrases': ['fujimori leads', 'fujimori ahead', 'fujimori edges',
                         'fujimori takes lead', 'fujimori widens', 'lead for fujimori'],
        'market_read': 'stabilizing',
        'market_prose': ('read by markets as mining-continuity / fiscal-orthodoxy '
                         'posture -- the stabilizing scenario for copper and '
                         'silver supply expectations'),
        'count_base':  'international / diaspora ballots (typically counted late)',
    },
    'sanchez': {
        'display':     'Roberto Sanchez',
        'party':       'Juntos por el Peru (left-nationalist, Castillo ally)',
        'keywords':    ['roberto sanchez', 'sanchez palomino', 'juntos por el peru'],
        'lead_phrases': ['sanchez leads', 'sanchez ahead', 'sanchez edges',
                         'sanchez takes lead', 'sanchez widens', 'lead for sanchez',
                         'sanchez edged ahead'],
        'market_read': 'volatile',
        'market_prose': ('read by markets as mining-policy-uncertainty posture '
                         '(contract review / royalty revision risk) -- the '
                         'volatility scenario; silver and copper risk premium '
                         'is partly this political risk premium'),
        'count_base':  'rural domestic ballots (late-count strength)',
    },
}

ELECTION_PHASE_KEYWORDS = {
    'decided':  ['president-elect', 'presidente electo', 'wins peru presidency',
                 'declared the winner', 'proclamacion', 'proclama', 'concedes',
                 'concede defeat'],
    'disputed': ['fraud', 'fraude', 'annul', 'nulidad', 'impugna', 'recount',
                 'irregularities', 'irregularidades', 'audit the vote'],
    'counting': ['runoff', 'segunda vuelta', 'balotaje', 'votes counted',
                 'ballots tallied', 'conteo', 'actas', 'onpe', 'virtually tied',
                 'razor-thin', 'too close to call', 'diaspora', 'voto extranjero',
                 'international polling'],
}


def _election_corpus(actor_summaries):
    """Concatenated lowercase corpus from every actor's top articles --
    title + description + slugified URL (slugs encode full headlines)."""
    parts = []
    for actor in (actor_summaries or {}).values():
        for art in (actor.get('top_articles') or []):
            parts.append((art.get('title') or '').lower())
            parts.append((art.get('description') or '').lower())
            url = (art.get('url') or art.get('link') or '').lower()
            if url:
                parts.append(url.replace('-', ' ').replace('_', ' ').replace('/', ' '))
    return ' '.join(parts)


def build_election_watch(actor_summaries):
    """Returns the election_watch block, or None when the cycle is quiet
    (auto-quiesces once runoff coverage leaves the corpus)."""
    corpus = _election_corpus(actor_summaries)
    if not corpus.strip():
        return None

    cands = {}
    for cid, c in ELECTION_CANDIDATES.items():
        mentions = sum(corpus.count(k) for k in c['keywords'])
        leads = sum(corpus.count(p) for p in c['lead_phrases'])
        cands[cid] = {
            'display':      c['display'],
            'party':        c['party'],
            'market_read':  c['market_read'],
            'count_base':   c['count_base'],
            'mention_count': mentions,
            'lead_signal_count': leads,
        }

    phase_hits = {ph: sum(corpus.count(k) for k in kws)
                  for ph, kws in ELECTION_PHASE_KEYWORDS.items()}

    total_mentions = sum(c['mention_count'] for c in cands.values())
    if total_mentions == 0 and phase_hits['counting'] == 0:
        return None

    # Phase precedence: decided > disputed > counting
    if phase_hits['decided'] >= 2:
        phase = 'decided'
    elif phase_hits['disputed'] >= 2:
        phase = 'count_disputed'
    else:
        phase = 'count_in_progress'

    # Which candidate's lead-language dominates THIS scan (signals, not a call)
    f, s = cands['fujimori']['lead_signal_count'], cands['sanchez']['lead_signal_count']
    if f == s:
        momentum = 'balanced'
    else:
        momentum = 'fujimori' if f > s else 'sanchez'

    return {
        'active':      True,
        'phase':       phase,
        'phase_hits':  phase_hits,
        'momentum_signals': momentum,
        'candidates':  cands,
        'disclaimer':  ('CONVERGENCE indicator: reports which counting and '
                        'candidate signals are present in the current scan. '
                        'NOT a prediction of the electoral outcome.'),
    }


def _election_bullets(election, commodity_pressure):
    """So-What bullets for an active election watch."""
    if not election:
        return []
    bullets = []
    cf = election['candidates']['fujimori']
    cs = election['candidates']['sanchez']

    # Market-polarity bullet -- the core analytical read
    bullets.append({
        'bullet': ("ELECTION WATCH -- runoff count signals active. The two "
                   "outcomes carry opposite market reads: "
                   + cf['display'] + " (" + cf['party'] + ") is " + ELECTION_CANDIDATES['fujimori']['market_prose']
                   + "; " + cs['display'] + " (" + cs['party'] + ") is " + ELECTION_CANDIDATES['sanchez']['market_prose']
                   + ". Counting structure cuts both ways: " + cs['display']
                   + "'s strength sits in " + cs['count_base'] + ", while "
                   + cf['display'] + "'s sits in " + cf['count_base'] + "."),
        'weight': 5.5,
    })

    # Momentum-signal bullet (dynamic, per-scan)
    mom = election['momentum_signals']
    if mom != 'balanced':
        lead = election['candidates'][mom]
        other = 'sanchez' if mom == 'fujimori' else 'fujimori'
        bullets.append({
            'bullet': ("Current-scan lead language clusters around " + lead['display']
                       + " (" + str(lead['lead_signal_count']) + " lead-phrase signals vs "
                       + str(election['candidates'][other]['lead_signal_count'])
                       + ") -- a snapshot of coverage, not a result. Implied market posture if "
                       "that trajectory holds: " + lead['market_read'] + "."),
            'weight': 5.2,
        })

    # Phase bullets
    if election['phase'] == 'count_disputed':
        bullets.append({
            'bullet': ("Dispute-language signals active (fraud / recount / annulment "
                       "vocabulary in coverage). 2021 precedent: a near-tie plus fraud "
                       "claims extended uncertainty for weeks -- itself a market-volatility "
                       "vector independent of who wins."),
            'weight': 5.4,
        })
    if election['phase'] == 'decided':
        bullets.append({
            'bullet': ("Decision-language signals active (president-elect / proclamation "
                       "vocabulary). Watch the transition window: cabinet signals and "
                       "mining-policy first statements will set the commodity tone."),
            'weight': 5.3,
        })

    # Commodity cross-read
    _story = (commodity_pressure or {}).get('_pressure_story') or {}
    alert = (_story.get('alert')
             or (commodity_pressure or {}).get('composite_level')
             or (commodity_pressure or {}).get('alert'))
    if alert and str(alert).lower() in ('elevated', 'high', 'surge', 'critical'):
        bullets.append({
            'bullet': ("Convergence note: commodity news-signal pressure is already at "
                       + str(alert).upper() + " while the runoff count is unresolved -- "
                       "political uncertainty and supply-side signal pressure are stacking "
                       "on the same window."),
            'weight': 5.1,
        })
    return bullets



# ============================================
# Convenience entry point
# ============================================
def interpret_peru_signals(scan_data):
    actor_summaries         = scan_data.get('actor_summaries', {}) or {}
    vector_scores           = scan_data.get('vector_scores', {}) or {}
    vector_levels           = scan_data.get('vector_levels', {}) or {}
    tripwires_global        = scan_data.get('tripwires_global', []) or []
    commodity_pressure      = scan_data.get('commodity_pressure', {}) or {}
    crosstheater_amplifiers = scan_data.get('crosstheater_amplifiers', {}) or {}
    drift = score_alignment_drift(actor_summaries, tripwires_global, commodity_pressure,
                                  crosstheater_amplifiers, country='peru')
    return {
        'top_signals':       build_top_signals(actor_summaries, tripwires_global,
                                               commodity_pressure, crosstheater_amplifiers),
        'executive_summary': build_executive_summary(actor_summaries, vector_scores,
                                                     vector_levels, tripwires_global),
        'so_what':           build_so_what_factor(actor_summaries, vector_scores, vector_levels,
                                                  tripwires_global, commodity_pressure,
                                                  alignment_drift=drift),
        'alignment_drift':   drift,
        'top_indicator':     build_top_indicator(actor_summaries, tripwires_global, drift),
    }


print("[Peru Signal Interpreter] Module loaded — v1.1.0 (evidence-graded, int levels, meanings)")
