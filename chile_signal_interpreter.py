"""
chile_signal_interpreter.py
=========================================================
Chile Rhetoric Signal Interpreter v1.1.0 — Asifah Analytics
Built: May 9, 2026 · v1.1.0 Nov 4, 2026

Generates analytical prose for the Chile rhetoric tracker:
  • build_top_signals()       — canonical top signals (int level, pressure_type, meaning)
  • build_top_indicator()     — the one plain sentence to leave with
  • build_executive_summary() — plain 2-4 sentence narrative
  • build_so_what_factor()    — bulleted strategic implications
  • score_alignment_drift()   — great-power alignment-drift read (BRI writ large)

v1.1.0 (Nov 4 2026) -- WHA Phase 2 refresh (same pass as Peru 1.1.0 / Cuba 1.4.0)
  * CANONICAL LEVELS. Signals carry an INTEGER `level` (0-4) plus
    `level_name` for the page. The word 'surge' used to travel downstream as a
    string, and the GPI reads 'surge' as L5 -- the Peru "Economic Rupture" bug.
  * EVIDENCE. A tripwire speaks at full severity only when 2+ separate
    outlets report it (tracker v1.2.0 grades them). One outlet = "approaching"
    (L2). Rumour / hedged = never a top signal. Volume alone tops out at L2.
  * MEANING. Every signal carries `what_it_means` (plain / local / regional /
    global / economy / not_implied) and a one-sentence `meaning`: what Escondida
    is, who buys Chile's copper and lithium, what a strike does to prices, and
    what is NOT implied.
  * CURRENT FACTS. Boric-era prose retired: José Antonio Kast has been
    president since March 11 2026. "Boric resignation" and "approval cliff"
    tripwires removed (the approval pattern 'aprobación 20' matched every
    headline containing "aprobación 2026").
  * ALIGNMENT DRIFT. Band levels lowered one step, matching Peru.

Facts carried here are dated; re-verify on the 45-day review cycle (~Dec 19).

COPYRIGHT (c) 2025-2026 Asifah Analytics. All rights reserved.
"""

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
    'us_alignment':       'US-Chile relations',
    'china_alignment':    'China-Chile relations',
}

ACTOR_PROSE_NAMES = {
    'presidency':              'the Kast government',
    'cancilleria':             'the foreign ministry',
    'mining_sector':           'copper and lithium mining',
    'fisheries_sector':        'fishing and salmon farming',
    'mapuche_conflict':        'the Mapuche conflict in the south',
    'constitutional_politics': 'Congress and the reform fights',
    'us_chile':                'US-Chile relations',
    'china_chile':             'China-Chile relations',
}

DEESCALATION_PATTERNS = [
    'mesa de diálogo', 'mesa de dialogo', 'dialogue table',
    'consulta indígena', 'indigenous consultation',
    'acuerdo', 'agreement reached', 'tentative deal', 'preacuerdo',
    'tregua', 'truce', 'cese de hostilidades',
    'reanuda operaciones', 'resumes operations',
    'levanta bloqueo', 'lifts blockade', 'fin de la huelga', 'strike ends',
]


# ============================================
# WHAT IT MEANS  (dated Nov 4 2026 -- re-verify on the 45-day cycle)
# ============================================
# Figures: Chile ~5.5 Mt copper in 2025 (Cochilco range 5.4-5.6 Mt), roughly a
# quarter of world mined copper; Codelco 1.332 Mt in 2025 (La Tercera via
# Reuters/Kitco, Jan 2026), down from ~1.7 Mt a decade ago, ~$24bn debt (CRU,
# Feb 2026); Codelco-SQM joint venture (NovaAndino Litio) -- Codelco majority
# from 2031 to 2060, Kast government not reversing it (CRU, Feb 2026).
MEANINGS = {
    'copper': {
        'plain':    ('Chile is the world\'s largest copper producer -- about 5.5 million tonnes in '
                     '2025, roughly a quarter of all copper mined.'),
        'local':    ('Mining pays for a large share of the state budget and the northern regions '
                     '(Antofagasta, Atacama, Tarapacá) live on it.'),
        'regional': ('Chile and Peru together supply about a third of the world\'s copper, so trouble '
                     'in both at once matters more than either alone.'),
        'global':   ('China buys about half of Chile\'s copper. Copper goes into power grids, wiring, '
                     'electric vehicles, data centres and buildings; in 2026 the ore market is already '
                     'tight, so lost Chilean supply moves prices faster than usual.'),
        'economy':  ('If supply really falls, the cost reaches cables, appliances, cars and grid '
                     'projects over months, not at the shop next week.'),
        'not_implied': 'More news about Chilean mining does not mean any mine has stopped.',
    },
    'escondida': {
        'plain':    ('Escondida, run by BHP in the Atacama desert, is the world\'s biggest copper '
                     'mine -- about 5% of all copper mined.'),
        'local':    ('Its union strikes are bargaining rounds; the 2017 strike lasted 44 days and is '
                     'the benchmark.'),
        'global':   ('A strike of a few days is usually absorbed; a long one tightens copper '
                     'supply worldwide, and Chinese smelters feel it first.'),
        'economy':  'Any price effect reaches wiring, electronics, cars and grids over months.',
        'not_implied': 'Strike talk or a strike vote is not a strike; only a walkout confirmed by 2+ outlets is.',
    },
    'codelco': {
        'plain':    ('Codelco is Chile\'s state copper company -- about 1.3 million tonnes in 2025, '
                     'well below its 1.7 million peak, and about $24bn in debt.'),
        'local':    ('Its profits go to the treasury; its unions are among the strongest in Chile. '
                     'The 2025 El Teniente collapse that killed six miners still shapes safety politics.'),
        'global':   ('A Codelco strike or shutdown removes a few percent of world supply and '
                     'tightens an already tight market.'),
        'not_implied': 'Codelco news is often about debt and management, not lost output.',
    },
    'lithium': {
        'plain':    ('Chile is the world\'s second-largest lithium producer, from the Salar de '
                     'Atacama (SQM and Albemarle).'),
        'local':    ('A state-led deal (NovaAndino Litio) gives Codelco majority control of SQM\'s '
                     'Atacama lithium from 2031 to 2060; the Kast government has not reversed it.'),
        'regional': ('Chile, Argentina and Bolivia -- the "lithium triangle" -- hold most of the '
                     'world\'s known lithium brine.'),
        'global':   ('Lithium goes into electric-car and grid batteries. China refines most of the '
                     'world\'s lithium, and the Chinese firm Tianqi owns about a fifth of SQM -- so who '
                     'controls Chilean lithium is a US-China question as much as a Chilean one.'),
        'economy':  'Effects show up in battery and electric-car costs, slowly.',
        'not_implied': 'Lithium-policy debate is not a change of contracts or output.',
    },
    'fishmeal': {
        'plain':    ('Chile is the world\'s second-largest salmon farmer and fishes the same '
                     'Humboldt Current anchoveta as Peru.'),
        'global':   'Salmon disease or algal blooms raise salmon prices in the US, Brazil and Asia.',
        'not_implied': 'A quota debate is not a collapse.',
    },
    'state_of_exception': {
        'plain':    ('The south (Araucanía and parts of Biobío) has been under a state of exception '
                     'since October 2021; Congress renews it every 30 days. Renewals are routine -- '
                     'only a NEW or WIDER declaration is news.'),
        'not_implied': 'A renewal of the existing state of exception is not an escalation.',
    },
    'mapuche': {
        'plain':    ('The Mapuche conflict is a long-running land and autonomy dispute in southern '
                     'Chile. Armed groups such as the CAM burn forestry trucks and equipment; the '
                     'state answers with troops under the state of exception.'),
        'local':    'Violence hits forestry firms, farmers, truck drivers and Mapuche communities alike.',
        'not_implied': ('Mapuche news from Argentina (Bariloche, Neuquén) is a different country\'s '
                        'conflict and is filtered out here.'),
    },
    'politics': {
        'plain':    ('José Antonio Kast, on the right, has been president since March 11 2026. He '
                     'lacks a majority in Congress; his approval fell to around 35-40% by August 2026.'),
        'not_implied': 'Political news volume is not a cabinet crisis or an impeachment.',
    },
    'china_chile': {
        'plain':    ('China is Chile\'s largest trading partner and buys about half of its copper. '
                     'Chinese money is in lithium (Tianqi\'s SQM stake), power grids and ports.'),
        'global':   ('Washington presses Santiago to limit Chinese access to critical minerals and '
                     'dual-use sites such as observatories.'),
        'not_implied': 'Trade news is not a political realignment.',
    },
    'us_chile': {
        'plain':    ('The Kast government has moved closer to Washington (security cooperation, '
                     'critical minerals) while China remains its biggest customer.'),
        'not_implied': 'Warm words from Washington are not a change in who buys Chile\'s copper.',
    },
}

ACTOR_MEANING_KEY = {
    'mining_sector': 'copper', 'fisheries_sector': 'fishmeal', 'mapuche_conflict': 'mapuche',
    'presidency': 'politics', 'constitutional_politics': 'politics',
    'china_chile': 'china_chile', 'us_chile': 'us_chile',
}
TRIPWIRE_MEANING_KEY = {
    'escondida_strike': 'escondida', 'codelco_strike': 'codelco',
    'chuquicamata_disruption': 'codelco', 'lithium_nationalization': 'lithium',
    'mining_fatality': 'codelco', 'state_of_exception': 'state_of_exception',
    'mass_arson': 'mapuche', 'mapuche_fatality': 'mapuche', 'cam_attack': 'mapuche',
    'impeachment_vote': 'politics', 'cabinet_minister_ousted': 'politics',
    'major_reform_collapse': 'politics', 'president_resignation': 'politics',
    'cabinet_collapse': 'politics', 'strategic_minerals_pact': 'lithium',
    'fishing_quota_cut': 'fishmeal', 'salmon_disruption': 'fishmeal',
    'fisheries_collapse': 'fishmeal', 'fishing_law_reform': 'fishmeal',
    'chinese_naval_visit': 'china_chile', 'dual_use_facility': 'china_chile',
    'major_infra_milestone': 'china_chile', 'fta_renegotiation': 'china_chile',
    'security_cooperation': 'china_chile',
}
COMMODITY_MEANING_KEY = {'copper': 'copper', 'lithium': 'lithium', 'fishmeal': 'fishmeal',
                         'salmon': 'fishmeal'}


def _meaning(key):
    return dict(MEANINGS.get(key) or {})


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
        'theatre':       'chile',
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
    'president_resignation':   ('the president resigning', 'domestic_stability', 'governance'),
    'cabinet_collapse':        ('several ministers resigning at once', 'domestic_stability', 'governance'),
    'boundary_crisis':         ('a border crisis with a neighbour', 'domestic_stability', 'diplomatic'),
    'icj_filing':              ('a new case at the International Court of Justice', 'domestic_stability', 'diplomatic'),
    'escondida_strike':        ('a strike at Escondida, the world\'s biggest copper mine', 'resource_sector', 'economic'),
    'codelco_strike':          ('a strike at Codelco, the state copper company', 'resource_sector', 'economic'),
    'chuquicamata_disruption': ('a stoppage at Codelco\'s Chuquicamata mine', 'resource_sector', 'economic'),
    'lithium_nationalization': ('a move to nationalise lithium', 'resource_sector', 'economic'),
    'mining_fatality':         ('a fatal mining accident', 'resource_sector', 'humanitarian'),
    'state_of_exception':      ('a new or wider state of exception in the south', 'domestic_stability', 'governance'),
    'mass_arson':              ('coordinated arson attacks in the Mapuche conflict zone', 'domestic_stability', 'kinetic'),
    'mapuche_fatality':        ('a death in the Mapuche conflict zone', 'domestic_stability', 'kinetic'),
    'cam_attack':              ('an attack claimed by or blamed on the CAM', 'domestic_stability', 'kinetic'),
    'impeachment_vote':        ('an impeachment (constitutional accusation) approved', 'domestic_stability', 'governance'),
    'cabinet_minister_ousted': ('a minister removed by Congress', 'domestic_stability', 'governance'),
    'major_reform_collapse':   ('a flagship reform defeated in Congress', 'domestic_stability', 'governance'),
    'strategic_minerals_pact': ('a US-Chile critical-minerals agreement', 'us_alignment', 'economic'),
    'ambassador_recall':       ('an ambassador recalled between the US and Chile', 'us_alignment', 'diplomatic'),
    'joint_exercise_friction': ('a US-Chile military exercise cancelled or disputed', 'us_alignment', 'diplomatic'),
    'project_contestation':    ('the US blocking a Chinese project in Chile', 'us_alignment', 'diplomatic'),
    'monroe_doctrine_invoked': ('Washington invoking the Monroe Doctrine over Chile', 'us_alignment', 'diplomatic'),
    'us_displacement_push':    ('a US push to limit China in Chile', 'us_alignment', 'diplomatic'),
    'chinese_naval_visit':     ('a Chinese navy visit to Chile', 'china_alignment', 'diplomatic'),
    'major_infra_milestone':   ('a milestone on a Chinese-funded project in Chile', 'china_alignment', 'economic'),
    'fta_renegotiation':       ('a China-Chile trade-deal renegotiation', 'china_alignment', 'economic'),
    'dual_use_facility':       ('a Chinese observatory or space-tracking site in Chile', 'china_alignment', 'diplomatic'),
    'diplomatic_anti_us':      ('Chile or China pushing back at Washington\'s pressure', 'china_alignment', 'diplomatic'),
    'security_cooperation':    ('Chinese police or surveillance cooperation with Chile', 'china_alignment', 'diplomatic'),
    'fishing_quota_cut':       ('a fishing-quota cut', 'resource_sector', 'economic'),
    'fishing_law_reform':      ('a fishing-law overhaul', 'resource_sector', 'economic'),
    'salmon_disruption':       ('salmon die-offs or an algal bloom', 'resource_sector', 'economic'),
    'fisheries_collapse':      ('a fishery collapse', 'resource_sector', 'economic'),
}


def _tripwire_signal(tw, actor_summaries):
    """Corroborated -> full severity. Single source -> 'approaching' at L2.
    Rumour -> None (shown on the page as rumour, never as a top signal)."""
    tw_id = tw.get('id')
    grade = tw.get('grade', 'corroborated')
    what, _vec, ptype = TRIPWIRE_PLAIN.get(tw_id, (tw_id.replace('_', ' '), None, 'governance'))
    sev = _int(tw.get('severity', 'high'))
    outlets = tw.get('outlets') or []
    if grade == 'corroborated':
        level = sev
        short = f'Chile: {what} -- reported by {len(outlets) or 2} separate outlets'
    elif grade == 'single_source':
        level = min(2, sev)
        short = f'Chile: one outlet reports {what} -- not yet corroborated'
    else:
        return None
    mk = TRIPWIRE_MEANING_KEY.get(tw_id)
    long_text = ' '.join(x for x in (
        f'{what[0].upper() + what[1:]}: '
        f'{"confirmed by " + ", ".join(outlets[:4]) if grade == "corroborated" else "a single report so far"}.',
        _meaning_sentence(mk) if mk else '',
        (MEANINGS.get(mk) or {}).get('not_implied', '') if mk and grade != 'corroborated' else '',
    ) if x)
    return _sig('tripwire_' + tw_id, level, short, long_text, ptype, mk, actor=tw.get('actor'),
                sources=[{'title': i.get('title'), 'url': i.get('url'), 'source': i.get('outlet')}
                         for i in (tw.get('items') or [])[:3]],
                kind='tripwire', extra={'evidence': grade, 'outlets': outlets})


# ============================================
# TOP SIGNALS
# ============================================
def build_top_signals(actor_summaries, tripwires_global, commodity_pressure, crosstheater_amplifiers):
    """Canonical top_signals[] for Chile (v1.1.0 plain, evidence-graded, int levels)."""
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
                            'Chile: several areas are busier than usual at once -- ' + ' and '.join(names[:3]),
                            ('More than one part of the Chile picture is active in the same week: ' +
                             ', '.join(names) + '. Pressures that usually move separately are moving '
                             'together. In Chile that more often means a busy political week than a crisis.'),
                            'composite', kind='convergence'))

    # 3. Actors busier than usual (volume is capped at 'elevated' upstream)
    covered = {t.get('actor') for t in best.values() if t.get('grade') in ('corroborated', 'single_source')}
    for actor_id, actor in (actor_summaries or {}).items():
        level = actor.get('level', 'low')
        if level not in ESCALATORY_LEVELS or actor_id in covered:
            continue
        name = ACTOR_PROSE_NAMES.get(actor_id, actor.get('name', actor_id))
        n = actor.get('article_count', 0)
        outlets = actor.get('outlet_count') or 0
        deesc = _has_deescalation(actor)
        mk = ACTOR_MEANING_KEY.get(actor_id)
        short = (f'Chile: more reporting than usual on {name} ({n} items from {outlets} outlets)'
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
        if actor_id == 'mapuche_conflict':
            ptype = 'kinetic'
        signals.append(_sig('actor_volume', _int(level), short, long_text, ptype, mk,
                            actor=actor_id, sources=_sources(actor.get('top_articles')),
                            kind='actor_signal'))

    # 4. Commodity coupling (commodity alert AND sector reporting both up), capped at L3
    for cid, risk in (commodity_pressure or {}).items():
        if cid.startswith('_') or not isinstance(risk, dict):
            continue
        if risk.get('alert_level') not in ESCALATORY_LEVELS:
            continue
        sector_lvl = _int((actor_summaries.get('mining_sector') or {}).get('level', 'low'))
        lvl = min(3, _int(risk.get('alert_level')), max(sector_lvl, 1) + 1)
        mk = COMMODITY_MEANING_KEY.get(cid, 'copper')
        top = risk.get('top_signal') or {}
        signals.append(_sig('commodity_coupling', lvl,
                            f'Chile: {cid} supply-risk reporting is up while Chilean mining news is busy',
                            (f'The commodity tracker reads {risk.get("alert_level")} news pressure on {cid}, '
                             f'and Chile is a major producer. ' + _meaning_sentence(mk) + ' ' +
                             (MEANINGS.get(mk) or {}).get('not_implied', '')),
                            'economic', mk, actor='mining_sector', kind='commodity_coupling',
                            sources=[{'title': top.get('title', ''), 'url': top.get('url', ''),
                                      'source': top.get('source', '')}] if top.get('title') else []))

    # 5. Cross-theater amplifiers (context, L1)
    for amp, data in (crosstheater_amplifiers or {}).items():
        if not isinstance(data, dict) or not data.get('active'):
            continue
        text = {
            'china_lac_active':   'China\'s Latin America messaging is active this cycle',
            'china_bri_latam':    'China\'s Belt and Road push in Latin America is active this cycle',
            'iran_latam_active':  'Iran\'s Latin America activity is elevated this cycle',
            'iran_hezbollah_tba': 'Hizballah\'s Tri-Border Area network is active this cycle',
        }.get(amp, amp.replace('_', ' '))
        signals.append(_sig('crosstheater', 1, 'Chile context: ' + text,
                            text + '. It raises the stakes of Chile-side signals but is not a Chile event.',
                            'diplomatic', kind='crosstheater'))

    signals.sort(key=lambda s: (-s['level'], -len(s.get('sources') or [])))
    return signals[:12]


# ============================================
# TOP INDICATOR + EXECUTIVE SUMMARY
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
        m = MEANINGS.get(mk) or {}
        main = f'Confirmed by more than one outlet: {what}. ' + (m.get('global') or m.get('plain') or '')
    elif busy:
        names = [ACTOR_PROSE_NAMES.get(k, k) for k, _ in busy[:2]]
        main = ('Nothing high-impact is confirmed in Chile. Reporting is busier than usual on '
                + ' and '.join(names) + ' -- more news, not a crisis.')
    else:
        main = 'Chile reads quiet: nothing high-impact is confirmed and no area is unusually busy.'
    if single and not corro:
        what = TRIPWIRE_PLAIN.get(single[0].get('id'), (single[0].get('id', '').replace('_', ' '),))[0]
        main += f' Watching: one outlet reports {what}, not yet corroborated.'
    if alignment_drift and alignment_drift.get('band') in ('Drifting', 'Realigning'):
        main += (' Backdrop: China\'s moves in Chile are outpacing Washington\'s this cycle, '
                 'even under a US-leaning government.')
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
        parts.append('Chile reads quiet this cycle: no area is unusually busy and nothing high-impact is confirmed.')
    single = [t for t in (tripwires_global or []) if t.get('grade') == 'single_source']
    if single:
        parts.append('Single-outlet reports not yet corroborated: ' +
                     ', '.join(sorted({TRIPWIRE_PLAIN.get(t.get('id'), (t.get('id'),))[0] for t in single})[:3]) + '.')
    parts.append(MEANINGS['politics']['plain'])
    return ' '.join(parts)


# ════════════════════════════════════════════════════════════════════
# GREAT-POWER ALIGNMENT-DRIFT — portable "BRI writ large" convergence
# ════════════════════════════════════════════════════════════════════
# Nets challenger (China) inroad pressure against incumbent (US) counter-
# pressure. CONVERGENCE / influence indicator -- NOT a prediction of realignment.
# v1.1.0: one step lower across the board, matching Peru. Chile carries NO
# structural floor (unlike Peru's Chancay): China is the biggest customer, but
# under Kast the political lean is toward Washington.
DRIFT_BAND_META = {
    'US-anchored': {'level': 1, 'color': '#38bdf8', 'priority': 4},
    'Contested':   {'level': 2, 'color': '#f59e0b', 'priority': 7},
    'Drifting':    {'level': 3, 'color': '#f97316', 'priority': 8},
    'Realigning':  {'level': 4, 'color': '#dc2626', 'priority': 11},
}

DRIFT_PROFILES = {
    'chile': {
        'flag':            '\U0001F1E8\U0001F1F1',
        'inroad_power':    'China',
        'incumbent_power': 'the US',
        'inroad_actor':    'china_chile',
        'counter_actor':   'us_chile',
        'inroad_tripwires':  ('dual_use_facility', 'diplomatic_anti_us',
                              'security_cooperation', 'chinese_naval_visit',
                              'major_infra_milestone'),
        'counter_tripwires': ('project_contestation', 'monroe_doctrine_invoked',
                              'us_displacement_push', 'strategic_minerals_pact'),
        'dependency_channel': 'copper and lithium sales to China',
        'commodity_keys':     ('copper', 'lithium'),
        'crosstheater_amp':   'china_lac_active',
        'precedents': ('the dismantled San Juan radio telescope and the suspended '
                       'Atacama observatory -- inroads that advanced until US '
                       'diplomatic pressure reversed them'),
        'leading_indicators': [
            'Dual-use sites -- observatory or ground-station approvals and reversals',
            'Lithium control -- the Codelco-SQM venture, Tianqi\'s SQM stake, new contracts',
            'Infrastructure -- the Humboldt submarine cable, San Antonio port, Huawei and 5G',
            'Santiago saying it has a "sovereign right to choose partners"',
            'US counter-moves -- critical-minerals deals, ambassador pressure, "better partner" offers',
        ],
    },
}

_DRIFT_LEVEL_RANK = {'low': 0, 'normal': 1, 'elevated': 2, 'high': 3, 'surge': 4}


def score_alignment_drift(actor_summaries, tripwires_global, commodity_pressure,
                          crosstheater_amplifiers, country='chile', profile=None):
    """Great-power alignment-drift convergence read. CONVERGENCE, not prediction."""
    prof = profile or DRIFT_PROFILES.get((country or '').lower())
    if not prof:
        return None
    asum = actor_summaries or {}
    inroad_lvl = _DRIFT_LEVEL_RANK.get((asum.get(prof['inroad_actor']) or {}).get('level', 'low'), 0)
    counter_lvl = _DRIFT_LEVEL_RANK.get((asum.get(prof['counter_actor']) or {}).get('level', 'low'), 0)
    # Only corroborated tripwires move the drift read.
    tw_ids = {tw.get('id') for tw in (tripwires_global or [])
              if tw.get('grade', 'corroborated') == 'corroborated'}
    inroad_tw = [t for t in prof['inroad_tripwires'] if t in tw_ids]
    counter_tw = [t for t in prof['counter_tripwires'] if t in tw_ids]
    dep_active = False
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
    ip, cp_, cc = prof['inroad_power'], prof['incumbent_power'], (country or '').title()
    if band == 'US-anchored':
        so_what = (ip + ' is ' + cc + '\'s biggest customer, but this cycle its presence reads as ordinary '
                   'business; ' + cp_ + '\'s position is not being contested.')
    elif band == 'Contested':
        so_what = (ip + ' and ' + cp_ + ' are both actively competing for ' + cc + ' this cycle -- a '
                   'tug-of-war like ' + prof['precedents'] + '. The alignment is being fought over, not conceded.')
    elif band == 'Drifting':
        so_what = (ip + '\'s moves in ' + cc + ' are outpacing ' + cp_ + '\'s this cycle, through '
                   + prof['dependency_channel'] + '. What it means: money pulls Santiago toward Beijing '
                   'even while its government leans toward Washington.')
    else:
        so_what = ('Sustained ' + ip + ' moves, deep dependency (' + prof['dependency_channel'] +
                   ') and little ' + cp_ + ' push-back are consistent with ' + cc +
                   ' settling into ' + ip + '\'s orbit.')
    meta = DRIFT_BAND_META[band]
    return {
        'id': 'bri_inroad_' + (country or '').lower(), 'country': (country or '').lower(),
        'flag': prof.get('flag', ''), 'band': band, 'standing_floor': False,
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
    return {
        'priority':      drift['priority'],
        'category':      'alignment_drift',
        'type':          'alignment_drift',
        'theatre':       drift['country'],
        'level':         drift['level'],
        'level_name':    LEVEL_ORDER[min(4, drift['level'])],
        'pressure_type': 'diplomatic',
        'standing':      False,
        'icon':          drift['icon'],
        'color':         drift['color'],
        'short_text':    'Chile: China and the US competing for influence -- ' + drift['band'].lower(),
        'long_text':     (drift['so_what_factor'] + ' ' + drift['disclaimer'])[:480],
        'what_it_means': _meaning('china_chile'),
        'meaning':       _meaning_sentence('china_chile'),
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

    if 'escondida_strike' in corro:
        bullets.append({'bullet': ('A strike at Escondida is confirmed by more than one outlet. ' +
                                   MEANINGS['escondida']['plain'] + ' ' + MEANINGS['escondida']['global'] +
                                   ' Watch: how long it lasts, and whether BHP declares force majeure.'),
                        'weight': 6.0})
    elif 'escondida_strike' in single:
        bullets.append({'bullet': ('One outlet reports a strike at Escondida; not yet corroborated. ' +
                                   MEANINGS['escondida']['not_implied']), 'weight': 4.6})
    if corro & {'codelco_strike', 'chuquicamata_disruption'}:
        bullets.append({'bullet': ('Codelco output is disrupted, confirmed by 2+ outlets. ' +
                                   MEANINGS['codelco']['plain'] + ' ' + MEANINGS['codelco']['global']),
                        'weight': 5.5})
    if 'lithium_nationalization' in corro:
        bullets.append({'bullet': ('A lithium-control move is confirmed. ' + MEANINGS['lithium']['local'] +
                                   ' ' + MEANINGS['lithium']['global']), 'weight': 5.3})
    if 'state_of_exception' in corro:
        bullets.append({'bullet': ('A new or wider state of exception in the south is confirmed. ' +
                                   MEANINGS['state_of_exception']['plain']), 'weight': 5.0})
    if corro & {'mass_arson', 'cam_attack', 'mapuche_fatality'}:
        bullets.append({'bullet': ('Violence in the Mapuche conflict zone is confirmed by 2+ outlets. ' +
                                   MEANINGS['mapuche']['plain'] + ' Watch: troop deployments and '
                                   'whether the government reaches for anti-terror law.'),
                        'weight': 4.8})
    if corro & {'impeachment_vote', 'cabinet_minister_ousted', 'cabinet_collapse', 'president_resignation'}:
        bullets.append({'bullet': ('A blow to the government in Congress or the cabinet is confirmed. ' +
                                   MEANINGS['politics']['plain']), 'weight': 5.2})
    if 'strategic_minerals_pact' in corro:
        bullets.append({'bullet': ('A US-Chile critical-minerals deal is confirmed. It ties Chilean copper '
                                   'and lithium closer to US supply chains; watch Beijing\'s response, since '
                                   'China is still the biggest buyer.'), 'weight': 4.7})

    if alignment_drift and alignment_drift.get('band') in ('Contested', 'Drifting', 'Realigning'):
        bullets.append({'bullet': 'China and the US: ' + alignment_drift.get('so_what_factor', ''),
                        'weight': 5.0})

    if (vector_levels or {}).get('resource_sector') in ESCALATORY_LEVELS and not (corro & {
            'escondida_strike', 'codelco_strike', 'chuquicamata_disruption'}):
        bullets.append({'bullet': ('Mining reporting is busier than usual. ' + MEANINGS['copper']['global'] +
                                   ' ' + MEANINGS['copper']['not_implied']), 'weight': 3.6})
    if (vector_levels or {}).get('domestic_stability') in ESCALATORY_LEVELS:
        bullets.append({'bullet': ('Politics and security reporting is busier than usual. ' +
                                   MEANINGS['politics']['plain']), 'weight': 3.2})

    story = (commodity_pressure or {}).get('_pressure_story') or {}
    if (story.get('alert') or 'normal') != 'normal':
        bullets.append({'bullet': ('Commodity news about Chile is running hot (' + str(story['alert']) +
                                   '). That measures how much is being written, not prices.'),
                        'weight': 3.0})

    if not bullets:
        bullets.append({'bullet': ('Chile reads quiet this cycle. What would change that: a confirmed '
                                   'strike at Escondida or Codelco, a new or wider state of exception in '
                                   'the south, an impeachment vote, or a change to lithium control.'),
                        'weight': 1.0})
    bullets.sort(key=lambda b: -b['weight'])
    return bullets[:7]


# ============================================
# Convenience entry point
# ============================================
def interpret_chile_signals(scan_data):
    actor_summaries         = scan_data.get('actor_summaries', {}) or {}
    vector_scores           = scan_data.get('vector_scores', {}) or {}
    vector_levels           = scan_data.get('vector_levels', {}) or {}
    tripwires_global        = scan_data.get('tripwires_global', []) or []
    commodity_pressure      = scan_data.get('commodity_pressure', {}) or {}
    crosstheater_amplifiers = scan_data.get('crosstheater_amplifiers', {}) or {}
    drift = score_alignment_drift(actor_summaries, tripwires_global, commodity_pressure,
                                  crosstheater_amplifiers, country='chile')
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


print("[Chile Signal Interpreter] Module loaded — v1.1.0 (evidence-graded, int levels, meanings)")
