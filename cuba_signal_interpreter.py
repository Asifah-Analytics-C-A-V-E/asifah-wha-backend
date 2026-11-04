"""
cuba_signal_interpreter.py
Asifah Analytics -- WHA Backend Module
v1.3.0 -- Nov 4, 2026   (Venezuela-pattern checklist; v1.2.0 earlier today; v1.1.0 May 17 2026)

Signal interpretation engine for the Cuba Rhetoric Tracker: red lines,
So What, historical matches, top signals, top indicator, RUMINT.

v1.2.0 (Nov 4 2026)
  * build_top_signals() and build_top_indicator() ADDED. The tracker has
    imported build_top_signals since v2.4 and it did not exist here, so the
    import failed and this whole module was silently unavailable: no red
    lines, no So What, no top signals on any scan.
  * RED LINES ARE EVIDENCE-GRADED, read across EVERY article (not an actor's
    top five): BREACHED = 2+ separate outlets, unhedged; APPROACHING = one
    outlet; WATCHING = rumour or hedged wording. The 1962-pattern check used
    to fire on any single article containing "cuba", "300 drones" and
    "russia" -- the May 2026 drone story could breach it forever.
  * PLAIN LANGUAGE: no L-codes in reader text; each red line says what
    crossing it would MEAN. Signals carry `what_it_means`.
  * Context (Nov 4 2026, re-verify): US fuel blockade since Jan 2026;
    grid deficit about two-thirds of peak demand; 20+ hour outages; talks
    confirmed Mar 2026; 2,000+ prisoners released from Apr; Raul Castro
    indicted; US says regime change is the goal.

The 1962 historical analog stays: it is structural pattern recognition,
offered only when two adversaries' weapons transfers are each confirmed.

Author: RCGG / Asifah Analytics
"""

import unicodedata
from datetime import datetime, timezone

try:
    from evidence_gate import TripwireLedger, is_hedged, outlet_of
except ImportError:  # degrade: count outlets crudely, no hedge filter
    def is_hedged(t): return False
    def outlet_of(a):
        s = a.get('source'); return str((s.get('name') if isinstance(s, dict) else s) or 'unknown').lower()
    class TripwireLedger:
        def __init__(self): self._h = {}
        def add(self, tw, a, text=None): self._h.setdefault(tw, set()).add(outlet_of(a))
        def ids(self): return list(self._h)
        def result(self, tw):
            o = sorted(self._h.get(tw, ()))
            return {'grade': 'corroborated' if len(o) >= 2 else ('single_source' if o else 'none'),
                    'outlets': o, 'rumint_outlets': [], 'items': []}


def _fold(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s or '')
                   if not unicodedata.combining(c)).lower()


def _atext(a):
    return _fold(' '.join(str(a.get(k) or '') for k in ('title', 'description', 'snippet')))


# ============================================================
# WHAT IT MEANS  (dated Nov 4 2026 -- re-verify on the 45-day cycle)
# ============================================================
MEANINGS = {
    'blackouts': {
        'plain':    ('Cuba\'s grid has been covering only about a third of peak demand, with outages '
                     'of 20 hours or more a day in many areas (UNE reports, Oct-Nov 2026).'),
        'local':    ('No power means no water pumping, spoiled food, hospitals on generators and '
                     'schools closing -- the daily experience of most Cubans.'),
        'regional': ('Hardship is the main driver of emigration; Florida, Mexico and the Caribbean '
                     'feel it first.'),
        'global':   ('The US fuel blockade (since January 2026) and the loss of Venezuelan oil are '
                     'the cause; Russia and China have sent some oil, rice and aid.'),
        'not_implied': 'More blackout reporting is not the same as protest or regime collapse.',
    },
    'us_pressure': {
        'plain':    ('Washington has blocked oil shipments to Cuba since January 2026, says regime '
                     'change is its goal, and has indicted Raul Castro; talks have also been held.'),
        'regional': ('Mexico stopped oil shipments under US tariff threat; other Caribbean and Latin '
                     'governments are being pushed to pick a side.'),
        'global':   ('It is a test of whether economic siege alone can force a political transition '
                     '-- watched closely in Moscow, Beijing and Tehran.'),
        'not_implied': 'Tough US statements are not military action.',
    },
    'protest': {
        'plain':    ('Street protest in Cuba is rare and costly; the July 2021 protests were the '
                     'largest in decades and were met with mass arrests.'),
        'local':    'Protests usually start over power or food and spread fastest in eastern cities.',
        'not_implied': 'Coverage by exile media is not, by itself, evidence of protest on the ground.',
    },
    'migration': {
        'plain':    ('Cuba has lost a large share of its population since 2021; past mass departures '
                     '(Mariel 1980, the rafters of 1994) followed exactly this mix of hardship and US pressure.'),
        'regional': 'A new wave would land on Florida and the US Coast Guard first, then Mexico.',
        'not_implied': 'Migration talk is not a surge of boats.',
    },
    'patrons': {
        'plain':    ('Russia, China and Iran are Cuba\'s remaining outside backers: Russian oil '
                     'tankers, Chinese rice and grid aid, and long-standing intelligence ties.'),
        'global':   ('Their access to an island 90 miles from Florida is what turns Cuba\'s crisis '
                     'into a great-power question.'),
        'not_implied': 'Statements of friendship are not weapons deliveries or bases.',
    },
}


def _meaning_sentence(key):
    m = MEANINGS.get(key) or {}
    return ' '.join(x for x in (m.get('plain'), m.get('global') or m.get('regional')) if x)


# ============================================================
# RED LINES  (phrases are folded at match time)
# ============================================================
RED_LINES = [
    {'id': 'us_direct_military_action', 'label': 'US military action against Cuba',
     'detail': 'Blockade enforced by force, a strike, or troops inside Cuban waters or airspace.',
     'plain': ('The first US military action against Cuba since 1962; Russia and China would have '
               'to decide how to respond.'),
     'severity': 3, 'color': '#dc2626', 'icon': '⚓', 'category': 'us_escalation',
     'phrases': ['us naval blockade cuba', 'us strike cuba', 'us strikes cuba', 'us forces enter cuba',
                 'us military action cuba', 'us airstrike cuba', 'us invasion cuba', 'us invades cuba',
                 'us forces land in cuba', 'ataque estadounidense contra cuba']},
    {'id': 'us_unilateral_coercion', 'label': 'US punishes third countries over Cuba',
     'detail': 'Secondary sanctions or tariffs on countries that trade with Cuba, beyond the oil measures already in force.',
     'plain': ('It forces Latin American governments to choose between Washington and Havana, and can '
               'push some toward China.'),
     'severity': 2, 'color': '#ef4444', 'icon': '🦅', 'category': 'us_escalation',
     'phrases': ['secondary sanctions cuba', 'us sanctions mexico over cuba', 'title iii lawsuits cuba',
                 'secondary sanctions against cuba partners', 'sanciones secundarias cuba']},
    {'id': 'mass_migration_event', 'label': 'Mass departure by sea',
     'detail': 'A large, sudden wave of departures toward Florida that strains Coast Guard interdiction.',
     'plain': ('A 1980- or 1994-style exodus: a domestic crisis for Florida and a political crisis '
               'for Washington.'),
     'severity': 3, 'color': '#dc2626', 'icon': '🚤', 'category': 'regime_fracture',
     'phrases': ['cuba migration surge', 'balsero crisis', 'cuba mass exodus', 'coast guard overwhelmed cuba',
                 'cuban rafters surge', 'mass cuban arrivals florida', 'exodo masivo cuba', 'crisis de balseros']},
    {'id': 'regime_succession', 'label': 'Leadership removed or replaced',
     'detail': 'Diaz-Canel removed, resigns or dies; an emergency transfer of power.',
     'plain': ('Cuba has no tested path for a leader leaving under pressure; the first days would '
               'decide whether the system holds.'),
     'severity': 3, 'color': '#dc2626', 'icon': '👑', 'category': 'regime_fracture',
     'phrases': ['diaz-canel resigns', 'diaz-canel removed', 'diaz-canel steps down', 'diaz-canel renuncia',
                 'diaz-canel destituido', 'cuba martial law', 'ley marcial en cuba']},
    {'id': 'military_protest_suppression', 'label': 'Army sent against protesters',
     'detail': 'The regular army (FAR), not just the interior ministry, deployed against civilians.',
     'plain': 'It would mean the regime no longer trusts its police to hold the street.',
     'severity': 2, 'color': '#ef4444', 'icon': '🪖', 'category': 'regime_fracture',
     'phrases': ['cuban army protesters', 'far deployed cuba protest', 'cuba military fires protesters',
                 'cuba soldiers shoot', 'cuban army streets', 'militares disparan manifestantes']},
    {'id': 'lourdes_reactivation', 'label': 'Russian spy station reopened',
     'detail': 'The Lourdes signals-intelligence station near Havana (closed 2001) confirmed back in Russian use.',
     'plain': 'Russian eavesdropping on the US East Coast from 100 miles away -- a Cold War return.',
     'severity': 3, 'color': '#dc2626', 'icon': '📡', 'category': 'adversary_access',
     'phrases': ['lourdes reactivated', 'lourdes reopened', 'lourdes sigint confirmed',
                 'lourdes station active', 'lourdes back online']},
    {'id': 'plan_warship_mariel', 'label': 'Chinese warship docks in Cuba',
     'detail': 'A Chinese navy ship visits Mariel or another Cuban port.',
     'plain': 'The first Chinese naval presence in the Caribbean on Cuba\'s invitation.',
     'severity': 3, 'color': '#dc2626', 'icon': '🚢', 'category': 'adversary_access',
     'phrases': ['plan warship mariel', 'chinese navy mariel', 'china warship cuba port',
                 'chinese warship havana', 'china naval base cuba', 'buque de guerra chino cuba']},
    {'id': 'iran_tanker_cuba', 'label': 'Iranian oil tanker reaches Cuba',
     'detail': 'An Iranian tanker delivers oil to a Cuban port despite the US blockade.',
     'plain': 'A direct challenge to the US fuel blockade by a sanctioned state.',
     'severity': 2, 'color': '#ef4444', 'icon': '🛢️', 'category': 'adversary_access',
     'phrases': ['iran tanker cuba', 'iranian tanker havana', 'iran oil cuba shipment', 'tanquero irani cuba']},
    {'id': 'adversary_weapons_staging_cuba', 'label': 'Two outside powers arming Cuba (1962 pattern)',
     'detail': ('Weapons transfers to Cuba from two or more of Russia, Iran and China, each confirmed by '
                '2+ outlets.'),
     'plain': ('The closest modern echo of October 1962: hostile powers placing strike capability 90 '
               'miles from Florida.'),
     'severity': 3, 'color': '#dc2626', 'icon': '🚀', 'category': 'coalition_threat', 'phrases': []},
    {'id': 'kinetic_precursor_cadence_cuba', 'label': 'US steps that preceded the Venezuela raid',
     'detail': ('Three or more of: senior US intelligence visit, indictment of a Cuban leader, '
                'congressional war-powers warnings, public disclosure of a Cuban weapons threat, '
                '"pretext" language -- within the scan window.'),
     'plain': ('The sequence Washington followed in the weeks before the January 2026 Venezuela raid. '
               'It is a pattern match, not a forecast.'),
     'severity': 3, 'color': '#dc2626', 'icon': '⏱️', 'category': 'us_escalation', 'phrases': []},
    {'id': 'iran_advisor_presence_cuba', 'label': 'Iranian military advisers in Cuba',
     'detail': 'IRGC or Iranian military trainers reported in Cuba.',
     'plain': 'State-to-state military help from Iran, not proxy activity -- new for the hemisphere.',
     'severity': 2, 'color': '#ef4444', 'icon': '🎓', 'category': 'coalition_threat',
     'phrases': ['iranian military advisers cuba', 'irgc advisers cuba', 'iranian advisers havana',
                 'iran drone trainers cuba', 'asesores militares iranies cuba']},
]

WEAPONS_TRANSFER = {
    'russia': ['russian drones delivered to cuba', 'drones from russia to cuba', 'russia sends drones to cuba',
               'russian weapons shipment cuba', 'russia arms cuba', 'rusia envia drones a cuba'],
    'iran':   ['iranian drones delivered to cuba', 'drones from iran to cuba', 'iran sends drones to cuba',
               'shahed drones cuba', 'iran arms cuba', 'iran envia drones a cuba'],
    'china':  ['chinese weapons shipment cuba', 'china arms cuba', 'china sends weapons to cuba'],
}
CADENCE_INDICATORS = {
    'senior_intel_visit':    ['cia director havana', 'ratcliffe havana', 'director de la cia en la habana'],
    'indictment':            ['castro indicted', 'indictment of raul castro', 'acusacion contra raul castro',
                              'doj indicts cuban'],
    'congressional_warning': ['war powers cuba', 'congress warns cuba military', 'hegseth cuba'],
    'capability_disclosure': ['cuba drone threat', 'cuba attack drones', 'drones cubanos amenaza'],
    'pretext_language':      ['pretext for military action cuba', 'pretexto para una accion militar'],
}


def _status(grade):
    return {'corroborated': 'BREACHED', 'single_source': 'APPROACHING', 'rumint': 'WATCHING'}.get(grade)


def check_red_lines(articles, actor_results):
    """Evidence-graded red lines across every article. Returns BREACHED,
    APPROACHING and WATCHING entries (the page shows the status)."""
    out = []
    led = TripwireLedger()
    for a in articles or []:
        t = _atext(a)
        for rl in RED_LINES:
            for ph in rl['phrases']:
                if _fold(ph) in t:
                    led.add(rl['id'], a, t)
                    break
    for rl in RED_LINES:
        if not rl['phrases']:
            continue
        r = led.result(rl['id'])
        st = _status(r['grade'])
        if st:
            out.append({**{k: v for k, v in rl.items() if k != 'phrases'},
                        'status': st, 'outlets': r['outlets'], 'rumint_outlets': r.get('rumint_outlets', []),
                        'evidence': ('Confirmed by ' + ', '.join(r['outlets'][:4]) if st == 'BREACHED'
                                     else 'One outlet so far: ' + ', '.join(r['outlets'][:1]) if st == 'APPROACHING'
                                     else 'Rumour or hedged wording only.'),
                        'source': rl['plain']})

    # Two adversaries arming Cuba, each confirmed
    wl = TripwireLedger()
    for a in articles or []:
        t = _atext(a)
        for adv, phrases in WEAPONS_TRANSFER.items():
            if any(_fold(p) in t for p in phrases):
                wl.add(adv, a, t)
    confirmed = [adv for adv in WEAPONS_TRANSFER if wl.result(adv)['grade'] == 'corroborated']
    single = [adv for adv in WEAPONS_TRANSFER if wl.result(adv)['grade'] == 'single_source']
    rl = next(r for r in RED_LINES if r['id'] == 'adversary_weapons_staging_cuba')
    if len(confirmed) >= 2 or (confirmed and single):
        st = 'BREACHED' if len(confirmed) >= 2 else 'APPROACHING'
        out.append({**{k: v for k, v in rl.items() if k != 'phrases'}, 'status': st,
                    'evidence': ('Weapons transfers confirmed from ' + ' and '.join(x.title() for x in confirmed)
                                 + ((' (plus a single report on ' + ', '.join(x.title() for x in single) + ')') if single else '')),
                    'source': rl['plain'], 'adversaries_confirmed': confirmed})

    # US cadence (Venezuela 2026 pattern)
    found, outs = [], set()
    for key, phrases in CADENCE_INDICATORS.items():
        for a in articles or []:
            t = _atext(a)
            if any(_fold(p) in t for p in phrases) and not is_hedged(t):
                found.append(key)
                outs.add(outlet_of(a))
                break
    rl = next(r for r in RED_LINES if r['id'] == 'kinetic_precursor_cadence_cuba')
    if len(found) >= 3 and len(outs) >= 2:
        st = 'BREACHED'
    elif len(found) >= 2:
        st = 'APPROACHING'
    else:
        st = None
    if st:
        out.append({**{k: v for k, v in rl.items() if k != 'phrases'}, 'status': st,
                    'evidence': f"{len(found)} of the steps seen this cycle: " +
                                ', '.join(k.replace('_', ' ') for k in found),
                    'source': rl['plain'], 'indicators': found})
    rank = {'BREACHED': 0, 'APPROACHING': 1, 'WATCHING': 2}
    out.sort(key=lambda r: (rank.get(r['status'], 3), -r.get('severity', 0)))
    return out


# ============================================================
# HISTORICAL MATCHES
# ============================================================
def build_historical_matches(actor_results, vectors):
    matches = []
    us_p = vectors.get('us_pressure', 0)
    frac = vectors.get('regime_fracture', 0)
    adv = vectors.get('adversary_access', 0)
    civ = vectors.get('civilian_pressure_level', 0)
    if us_p >= 3 and civ >= 3:
        matches.append({'label': 'Special Period (1990s)', 'year': 1991, 'score': 70,
                        'similarity': ('A lost oil patron plus outside pressure produced years of '
                                       'blackouts and hunger after the USSR fell; the regime survived it.')})
    if us_p >= 3 and frac >= 2:
        matches.append({'label': 'Mariel Boatlift (1980)', 'year': 1980, 'score': 65,
                        'similarity': ('Pressure plus unrest: Havana opened the port and 125,000 people '
                                       'left for Florida in six months.')})
    if frac >= 3:
        matches.append({'label': '11 July protests (2021)', 'year': 2021, 'score': 60,
                        'similarity': ('Blackouts and shortages set off the largest protests in decades; '
                                       'the state answered with mass arrests.')})
    if adv >= 3:
        matches.append({'label': 'Russia\'s Caribbean return (2014)', 'year': 2014, 'score': 55,
                        'similarity': 'Russian warship visits and spy-station rumours during US-Russia friction.'})
    matches.sort(key=lambda m: -m['score'])
    return matches[:3]


# ============================================================
# SO WHAT
# ============================================================
def build_so_what(scan_data, red_lines_triggered, historical_matches):
    actors = scan_data.get('actors', {}) or {}

    def lvl(k):
        return (actors.get(k) or {}).get('escalation_level', 0)

    us_p = scan_data.get('us_pressure', max(lvl('us_government'), lvl('us_sanctions_regulatory'),
                                            lvl('us_military_posture')))
    frac = scan_data.get('regime_fracture', 0)
    adv = scan_data.get('adversary_access', max(lvl('russia_cuba_axis'), lvl('china_cuba_axis'),
                                                lvl('iran_cuba_axis')))
    civ = scan_data.get('civilian_pressure_level', 0)
    mig = scan_data.get('migration_out_level', 0)
    breached = [r for r in red_lines_triggered if r.get('status') == 'BREACHED']
    approaching = [r for r in red_lines_triggered if r.get('status') == 'APPROACHING']
    staging = any(r['id'] == 'adversary_weapons_staging_cuba' and r['status'] == 'BREACHED' for r in red_lines_triggered)
    cadence = any(r['id'] == 'kinetic_precursor_cadence_cuba' and r['status'] == 'BREACHED' for r in red_lines_triggered)
    coalition_threat = 5 if (staging and cadence) else 4 if (staging or cadence) else \
        3 if any(r.get('category') == 'coalition_threat' and r['status'] == 'BREACHED' for r in red_lines_triggered) else 0

    if coalition_threat >= 5:
        scenario, color, icon = 'Military crisis pattern: outside powers arming Cuba as Washington lines up a strike', '#7c0a02', '🚨'
    elif breached:
        scenario, color, icon = 'Red line crossed: ' + breached[0]['label'], '#dc2626', '🔴'
    elif civ >= 4 and us_p >= 2:
        scenario, color, icon = 'Siege conditions: blackouts and shortages under the US fuel blockade', '#f97316', '🟠'
    elif civ >= 3 or us_p >= 3:
        scenario, color, icon = 'Severe hardship and sustained US pressure; no confirmed break', '#f59e0b', '🟡'
    elif civ >= 2 or us_p >= 2 or adv >= 2:
        scenario, color, icon = 'Strain visible; nothing high-impact confirmed', '#3b82f6', '🔵'
    else:
        scenario, color, icon = 'Quiet cycle -- nothing high-impact confirmed', '#6b7280', '⚪'

    situation = []
    if civ >= 2:
        situation.append(MEANINGS['blackouts']['plain'] + ' ' + MEANINGS['blackouts']['local'])
    if us_p >= 2:
        situation.append(MEANINGS['us_pressure']['plain'])
    if frac >= 3:
        situation.append('Protest activity is confirmed by more than one outlet. ' + MEANINGS['protest']['plain'])
    elif frac >= 1:
        situation.append('Some protest reporting, not confirmed as a wave. ' + MEANINGS['protest']['not_implied'])
    if adv >= 2:
        situation.append(MEANINGS['patrons']['plain'])
    if mig >= 3:
        situation.append('Departures are rising, confirmed by more than one outlet. ' + MEANINGS['migration']['regional'])

    indicators = []
    for r in red_lines_triggered:
        if r['status'] == 'BREACHED':
            indicators.append({'icon': '🔴', 'text': 'Crossed (2+ outlets): ' + r['label']})
        elif r['status'] == 'APPROACHING':
            indicators.append({'icon': '🟠', 'text': 'Approaching (1 outlet): ' + r['label']})
    for hm in (historical_matches or [])[:2]:
        indicators.append({'icon': '🕰️', 'text': f"Past pattern: {hm['label']} -- {hm['similarity']}"})

    if breached:
        assessment = breached[0]['plain'] + ' Watch how Havana and Washington respond in the next 48 hours.'
    elif civ >= 3 and us_p >= 2:
        assessment = ('The question is not whether Cubans are suffering -- they are -- but whether hardship '
                      'turns into protest, departures, or a deal. Watch for protests over power cuts, boats '
                      'leaving, and any new US-Cuba talks.')
    elif approaching:
        assessment = (approaching[0]['label'] + ' is reported by one outlet only. It counts once a second '
                      'outlet confirms it.')
    else:
        assessment = 'No break in the picture this cycle. Hardship and US pressure are the standing conditions.'
    if coalition_threat >= 5:
        assessment = ('This now matches the 1962 shape in its essentials -- outside powers placing strike '
                      'capability near Florida while Washington lines up a response. In 1962 that took 13 days '
                      'to resolve; past timelines describe then, not now. ') + assessment

    watch = []
    if civ >= 2:
        watch.append('Grid deficit and hours without power (UNE daily reports)')
    if us_p >= 2:
        watch.append('US statements on the blockade, talks, or "regime change"')
    if adv >= 2:
        watch.append('Russian tankers and Chinese aid shipments reaching Cuban ports')
    watch.append('Protests over blackouts, especially in eastern cities')
    if mig >= 2:
        watch.append('Coast Guard interdictions in the Florida Straits')

    return {
        'scenario': scenario, 'scenario_color': color, 'scenario_icon': icon,
        'situation': ' '.join(situation) or 'Little reporting this cycle -- unread, not calm.',
        'indicators': indicators, 'assessment': assessment, 'watch_list': watch[:5],
        'us_pressure': us_p, 'regime_fracture': frac, 'adversary_access': adv,
        'coalition_threat': coalition_threat,
        'doctrine_1962_pattern': staging, 'doctrine_vz2026_cadence': cadence,
        'doctrine_pre_kinetic': staging and cadence,
        'historical_matches': historical_matches or [],
        'confidence_note': ('Built from open-source reporting. Historical patterns are comparisons, not '
                            'forecasts.'),
    }


# ============================================================
# TOP SIGNALS + TOP INDICATOR  (v1.2.0 -- the import the tracker always expected)
# ============================================================
PRIORITY_BY_LEVEL = {0: 2, 1: 4, 2: 7, 3: 10, 4: 12, 5: 14}


def _sig(category, level, short, long_text, ptype, mk=None, extra=None):
    s = {'category': category, 'theatre': 'cuba', 'level': int(level),
         'priority': PRIORITY_BY_LEVEL.get(int(level), 2), 'pressure_type': ptype,
         'short_text': short[:230], 'long_text': long_text}
    if mk:
        s['what_it_means'] = dict(MEANINGS.get(mk) or {})
        s['meaning'] = _meaning_sentence(mk)
    if extra:
        s.update(extra)
    return s


def build_top_signals(result):
    sigs = []
    civ = result.get('civilian_pressure_level', 0) or 0
    us_p = result.get('us_pressure', 0) or 0
    frac = result.get('regime_fracture', 0) or 0
    adv = result.get('adversary_access', 0) or 0
    mig = result.get('migration_out_level', 0) or 0
    if civ >= 2:
        lvl = min(4, civ)
        sigs.append(_sig('humanitarian_civilian_pressure', lvl,
                         'Cuba: blackouts and shortages are ' + ('severe' if civ >= 4 else 'widespread' if civ >= 3 else 'visible')
                         + ' -- power, water, food and medicine',
                         MEANINGS['blackouts']['plain'] + ' ' + MEANINGS['blackouts']['local'] + ' ' +
                         MEANINGS['blackouts']['global'], 'humanitarian', 'blackouts'))
    if us_p >= 2:
        sigs.append(_sig('us_pressure_cuba', min(4, us_p),
                         'Cuba: US pressure is ' + ('heavy' if us_p >= 3 else 'steady') + ' -- the fuel blockade and regime-change goal',
                         MEANINGS['us_pressure']['plain'] + ' ' + MEANINGS['us_pressure']['global'], 'economic', 'us_pressure'))
    if frac >= 3:
        sigs.append(_sig('regime_fracture', min(4, frac),
                         'Cuba: protest activity confirmed by 2+ outlets',
                         MEANINGS['protest']['plain'] + ' ' + MEANINGS['protest']['local'], 'governance', 'protest'))
    if adv >= 3:
        sigs.append(_sig('adversary_access', min(4, adv),
                         'Cuba: Russia / China / Iran activity is up -- ' + ('confirmed high-impact report' if adv >= 4 else 'more reporting than usual'),
                         MEANINGS['patrons']['plain'] + ' ' + MEANINGS['patrons']['global'], 'diplomatic', 'patrons'))
    if mig >= 3:
        sigs.append(_sig('migration_out', min(4, mig), 'Cuba: departures by sea rising, confirmed by 2+ outlets',
                         MEANINGS['migration']['plain'] + ' ' + MEANINGS['migration']['regional'], 'humanitarian', 'migration'))
    for r in (result.get('red_lines') or []):
        if r.get('status') != 'BREACHED':
            continue
        lvl = 4 if r.get('severity', 2) >= 3 else 3
        ptype = {'us_escalation': 'kinetic', 'coalition_threat': 'kinetic', 'adversary_access': 'diplomatic',
                 'regime_fracture': 'governance'}.get(r.get('category'), 'governance')
        sigs.append(_sig('red_line_' + r['id'], lvl, 'Cuba: ' + r['label'] + ' -- confirmed by 2+ outlets',
                         r.get('detail', '') + ' ' + r.get('plain', ''), ptype,
                         extra={'type': 'red_line', 'evidence': 'corroborated'}))
    vp = result.get('venezuela_pattern') or {}
    if vp.get('read'):
        vl = int(vp.get('level') or 2)
        sigs.append(_sig('us_venezuela_pattern', vl, 'Cuba: ' + vp.get('short', ''),
                         vp['read'] + ' ' + vp.get('not_implied', ''),
                         'kinetic' if vl >= 3 else 'diplomatic',
                         extra={'standing': vl < 3,
                                'what_it_means': {'plain': vp['read'], 'not_implied': vp.get('not_implied', ''),
                                                  **(vp.get('if_it_happens') or {})},
                                'meaning': vp['read'].split('. ')[0] + '.'}))
    level = result.get('theatre_level', 0)
    sigs.append(_sig('theatre_read', level, result.get('signal_text_short') or 'Cuba: no strong signal',
                     result.get('signal_text_long') or '', 'composite'))
    sigs.sort(key=lambda s: -s['priority'])
    return sigs[:10]


def build_top_indicator(result):
    civ = result.get('civilian_pressure_level', 0) or 0
    us_p = result.get('us_pressure', 0) or 0
    rls = result.get('red_lines') or []
    breached = [r for r in rls if r.get('status') == 'BREACHED']
    approaching = [r for r in rls if r.get('status') == 'APPROACHING']
    if breached:
        main = 'Red line crossed, confirmed by more than one outlet: ' + breached[0]['label'] + '. ' + breached[0].get('plain', '')
    elif civ >= 3 and us_p >= 2:
        main = ('Cuba is under siege conditions: the US fuel blockade has left the grid covering about a '
                'third of demand, with 20-hour outages. The question is whether hardship turns into protest, '
                'departures or a deal -- none is confirmed this cycle.')
    elif civ >= 2:
        main = 'Hardship is visible -- blackouts and shortages -- but no protest wave, defection or US military move is confirmed.'
    else:
        main = 'No protest wave, defection or US military move is confirmed in Cuba this cycle.'
    if approaching and not breached:
        main += ' Watching: ' + approaching[0]['label'] + ', reported by one outlet only.'
    if (result.get('oil_tanker_level') or 0) >= 4:
        main += (' Confirmed by 2+ outlets: an oil tanker reached Cuba despite the US blockade -- '
                 'a few days of extra power, and a test of whether Washington enforces at sea.')
    vp = result.get('venezuela_pattern') or {}
    if vp.get('level', 0) >= 3:
        main += ' ' + vp['read'].split(' Watch for')[0]
    elif vp.get('short'):
        once = len(vp.get('final_reported_once') or []) + len(vp.get('final_rumour') or [])
        main += (' Is Cuba next? ' + str(vp.get('in_place')) + ' of ' + str(vp.get('total')) +
                 ' steps that preceded the Maduro raid are in place, none of the final ones confirmed' +
                 (' (' + str(once) + ' reported once or rumoured).' if once else '.'))
    if (result.get('articles_scanned') or 0) < 30:
        main += ' Coverage is thin this cycle, so quiet may be unread rather than calm.'
    return main


# ============================================================
# RUMINT -- concept-seeding / posture-probing detection
# ------------------------------------------------------------
# A lightweight read that rides ALONGSIDE the threat level and never inflates
# it. Detects trial-balloon behavior: US Cuba regime-change / military-takeover
# signaling floated as a possible precursor to a move -- the Venezuela-precedent
# analog (a Maduro-style leadership-change operation, applied to Havana). Bands
# on an escalating-OBSERVABLE ladder --
#   Watch -> Active -> Corroborated
# -- where each rung is gated by a NEW present-tense signal, not a forecast.
# 'off' = no pill (absence stays honest).
#
# PORTABILITY: cloned from greenland_signal_interpreter.py. Like Greenland,
# Cuba is the INVERTED case (US is the primary inbound threat-language source).
# "specificity" is repurposed to "names a concrete MOVE-RUMOR" (invasion /
# blockade / troop / snatch-operation language); "Corroborated" gates on the
# announcement layer alone. Cuba's Pituffik-equivalent false-positive trap is
# GUANTANAMO -- a STANDING US base -- so Active additionally requires at least
# some regime-change framing, so routine Gitmo coverage does not trigger.
# ============================================================

# --- COUNTRY-SPECIFIC (Cuba: US regime-change / takeover signaling) ---
RUMINT_SUBJECT = 'US Cuba regime-change signaling'

# WATCH layer -- US INTEREST / intent framing (the VZ-precedent jawboning)
RUMINT_EXPANSION_KEYWORDS = [
    'regime change cuba', 'cuba regime change', 'cuban regime change',
    'remove the cuban regime', 'remove the regime in havana',
    'topple havana', 'topple the cuban regime', 'topple diaz-canel',
    'oust diaz-canel', 'remove diaz-canel', 'remove the cuban government',
    'leadership change cuba', 'change of leadership cuba',
    'new government in cuba', 'install a new government in cuba',
    'transition government cuba', 'end the cuban dictatorship',
    'end communism in cuba', 'cuba is next', 'cuba will be next',
    'after maduro cuba', 'maduro then cuba', 'venezuela then cuba',
    'do to cuba what', 'venezuela model cuba', 'venezuela playbook cuba',
    'same playbook as venezuela', 'cuba like venezuela',
    'maximum pressure cuba', 'us military option cuba', 'military option for cuba',
    'rubio cuba', 'marco rubio cuba', 'trump cuba regime', 'white house cuba regime',
    'liberate cuba', 'free cuba operation',
]

# ACTIVE layer -- concrete MOVE-RUMORS of a military takeover (still pre-fact)
RUMINT_TARGETS = [
    'invade cuba', 'invasion of cuba', 'us invasion cuba', 'military invasion cuba',
    'blockade cuba', 'naval blockade cuba', 'blockade of cuba', 'quarantine cuba',
    'us military operation cuba', 'military operation against cuba',
    'operation against cuba', 'strike cuba', 'us strike cuba', 'airstrikes cuba',
    'bomb cuba', 'troops to cuba', 'marines to cuba', 'deploy to cuba',
    'warships toward cuba', 'warships near cuba', 'carrier toward cuba',
    'carrier strike group cuba', 'navy toward cuba', 'fleet toward cuba',
    'guantanamo buildup', 'guantanamo reinforcement', 'gitmo buildup',
    'leaked cuba plan', 'leaked plan cuba', 'secret cuba operation',
    'secret plan cuba', 'contingency plan cuba',
    'snatch diaz-canel', 'capture diaz-canel', 'kidnap diaz-canel',
    'extract diaz-canel', 'detain diaz-canel', 'special operations cuba',
    'special forces cuba', 'covert operation cuba', 'no-fly zone cuba',
    'maritime exclusion cuba',
]

# CORROBORATED layer -- announcement-grade fact-claims (ships/blockade in place,
# operation underway, government changed)
RUMINT_CORROBORATION_KEYWORDS = [
    'naval blockade of cuba declared', 'us declares blockade cuba',
    'blockade of cuba in place', 'cuba blockade begins', 'blockade imposed cuba',
    'us invades cuba', 'invasion of cuba begins', 'us forces land cuba',
    'us troops land in cuba', 'marines land cuba',
    'us military operation in cuba underway', 'operation against cuba underway',
    'us launches operation cuba', 'warships off cuba', 'us warships off cuba',
    'fleet off cuba', 'carrier off cuba', 'navy off cuba', 'ships off cuba',
    'us strikes cuba', 'airstrikes on cuba', 'us bombs cuba',
    'diaz-canel removed', 'diaz-canel captured', 'diaz-canel detained',
    'diaz-canel ousted', 'regime toppled cuba', 'cuban government falls',
    'new government installed cuba', 'us installs government cuba',
    'transitional government cuba announced', 'us seizes havana', 'havana falls',
]

RUMINT_RECEPTION_VENUES = ['r/cuba', 'r/geopolitics', 'r/venezuela', 'r/LatinAmerica']
RUMINT_FRAMING_FLOOR = 2   # distinct interest-framing terms below which we stay silent


# --- GENERIC (portable across RUMINT-enabled countries; gate tuned for inverted model) ---
def _check_keywords(scan_data, keywords):
    """Match keywords against the RUMINT corpus (the unified Cuba article pool,
    which already folds in Bluesky/Telegram). URL slugs are de-hyphenated so
    multi-word keywords match headline slugs."""
    if not keywords:
        return 0
    corpus_parts = []
    for art in (scan_data.get('rumint_articles') or []):
        corpus_parts.append((art.get('title') or '').lower())
        corpus_parts.append((art.get('description') or '').lower())
        corpus_parts.append((art.get('content') or '').lower())
        corpus_parts.append((art.get('text') or '').lower())
        corpus_parts.append((art.get('body') or '').lower())
        corpus_parts.append((art.get('summary') or '').lower())
        _url = (art.get('url') or art.get('link') or '').lower()
        if _url:
            corpus_parts.append(_url.replace('-', ' ').replace('_', ' ').replace('/', ' '))
    for sig in (scan_data.get('rumint_reddit') or []):
        corpus_parts.append((sig.get('text') or sig.get('title') or '').lower())
    corpus = ' | '.join(corpus_parts)
    if not corpus:
        return 0
    return sum(1 for kw in keywords if kw.lower() in corpus)


def _count_terms_in_reception(scan_data, keywords, venues):
    """Distinct keyword count restricted to reddit signals whose source is a
    reception venue -- the 'is the public reacting?' read. (Cuba's reddit layer
    is graceful: returns 0 until reddit is wired into the RUMINT corpus.)"""
    if not keywords:
        return 0
    parts = []
    for sig in (scan_data.get('rumint_reddit') or []):
        src = (sig.get('source') or sig.get('subreddit') or '')
        if isinstance(src, dict):
            src = src.get('name', '')
        if src in venues:
            parts.append((sig.get('text') or sig.get('title') or '').lower())
    corpus = ' | '.join(parts)
    if not corpus:
        return 0
    return sum(1 for kw in keywords if kw.lower() in corpus)


def _band_rumint(framing, specificity, reception, corroboration, subject):
    """Band the RUMINT read on the escalating-observable ladder. Each rung is
    gated by a NEW present-tense signal, never a forecast. Announcement-grade
    language is self-justifying -- Corroborated fires even when interest-framing
    is below the floor. 'off' shows no pill (absence stays honest)."""
    if corroboration >= 1:
        band, label = 'corroborated', 'Corroborated'
        driver = (subject + ' has reached announcement-grade language in the corpus '
                  '(blockade in place, warships off Cuba, operation underway, or a '
                  'leadership-removal claim) -- the rumor layer has hardened into '
                  'reported fact-claims. Consistent with a takeover in motion; verify '
                  'against primary sources, and the reader completes the inference.')
        return {'active': True, 'band': band, 'label': label, 'driver': driver,
                'framing': framing, 'specificity': specificity,
                'reception': reception, 'corroboration': corroboration}
    # Active: a concrete move-rumor (or public echo), read as RUMINT only when at
    # least some regime-change framing is also present -- so the STANDING US base
    # at Guantanamo does not false-positive on its own.
    if framing >= 1 and (specificity >= 1 or reception >= 1):
        band, label = 'active', 'Active'
        echo = ' and echoing in public forums' if reception >= 1 else ''
        driver = (subject + ' has moved past interest to concrete move-rumors '
                  '(leaked operation plans, naval movement toward Cuba, or blockade / '
                  'troop / snatch-operation signaling)' + echo + ' -- a trial balloon '
                  'in flight. Consistent with the cadence that preceded the Venezuela '
                  'leadership-change operation; reader completes the inference.')
        return {'active': True, 'band': band, 'label': label, 'driver': driver,
                'framing': framing, 'specificity': specificity,
                'reception': reception, 'corroboration': corroboration}
    # Watch: interest-framing density, no concrete move yet.
    if framing >= RUMINT_FRAMING_FLOOR:
        band, label = 'watch', 'Watch'
        driver = (subject + ' is present as interest / intent rhetoric (the Venezuela-'
                  'precedent framing) but no concrete move-rumor yet. Baseline concept-'
                  'seeding; watching for escalation to leaked plans, naval movement, or '
                  'troop / operation signaling.')
        return {'active': True, 'band': band, 'label': label, 'driver': driver,
                'framing': framing, 'specificity': specificity,
                'reception': reception, 'corroboration': corroboration}
    return {'active': False, 'band': 'off', 'label': '', 'driver': '',
            'framing': framing, 'specificity': specificity,
            'reception': reception, 'corroboration': corroboration}


def _score_rumint(scan_data):
    """Compute the RUMINT read from the captured corpus. Framing / specificity /
    corroboration use the full corpus; reception is venue-filtered. Counts are
    distinct-term counts -- a volume proxy, never a probability."""
    framing       = _check_keywords(scan_data, RUMINT_EXPANSION_KEYWORDS)
    corroboration = _check_keywords(scan_data, RUMINT_CORROBORATION_KEYWORDS)
    specificity   = _check_keywords(scan_data, RUMINT_TARGETS)
    reception     = _count_terms_in_reception(
        scan_data, RUMINT_EXPANSION_KEYWORDS + RUMINT_TARGETS,
        RUMINT_RECEPTION_VENUES)
    return _band_rumint(framing, specificity, reception, corroboration, RUMINT_SUBJECT)


# ============================================================
# TOP-LEVEL INTERPRETER
# ============================================================
# ============================================================
# THE VENEZUELA PATTERN  (v1.3.0 -- Nov 4 2026)
# ------------------------------------------------------------
# The reader's unasked question: "Is Cuba next?" Washington removed Maduro in a
# raid on Jan 3 2026, and the President has said Cuba "is next". The answer is
# not a probability -- it is a CHECKLIST: the steps that came before the Maduro
# raid, and which of them are in place for Cuba.
#
# Three phases, in the order they appeared in Venezuela:
#   pressure     -- rhetoric, indictment, economic strangulation, threat framing
#   preparation  -- surveillance flights, contingency planning
#   final        -- the steps of Venezuela's LAST ~7 weeks: forces massing,
#                   deployment orders, strikes, airspace warnings, embassy
#                   drawdown, an ultimatum
#
# Pressure and preparation steps that are already true are carried as STANDING
# facts, dated and sourced (re-verify on the 45-day cycle, next ~Dec 19). The
# FINAL steps are never standing: they must appear in this cycle's news, and
# each is graded by outlet count (2+ outlets = confirmed; one = reported once;
# hedged = rumour). A keyword is not a war.
# ============================================================
VZ_PATTERN_ASOF = 'Nov 4 2026'

VZ_PATTERN = [
    # ── pressure ──
    {'id': 'regime_change_goal', 'phase': 'pressure',
     'label': 'Regime change stated as the goal',
     'precedent': 'Months of "Maduro must go" from Washington before the raid.',
     'standing': 'The President said after the Maduro raid that Cuba "is next", and told the UN General Assembly (Sep 2026) that he seeks "fundamental change" in Cuba.',
     'terms': []},
    {'id': 'leader_indictment', 'phase': 'pressure',
     'label': 'Leadership indicted in US courts',
     'precedent': 'Maduro indicted (2020); the reward for his capture raised to $50m (Aug 2025).',
     'standing': 'Raúl Castro has been indicted on US federal charges (2026).',
     'terms': []},
    {'id': 'economic_strangulation', 'phase': 'pressure',
     'label': 'Economy strangled (oil cut off)',
     'precedent': 'US blockade and seizure of Venezuelan oil tankers (Dec 2025).',
     'standing': 'US oil blockade since January 2026 (Executive Order 14380, tariffs on any supplier); the grid covers about a third of demand.',
     'terms': []},
    {'id': 'threat_framing', 'phase': 'pressure',
     'label': 'Cuba framed as a security threat',
     'precedent': 'Venezuela framed as a "narco-state"; the Cartel de los Soles designated a terrorist organisation (Nov 2025).',
     'standing': 'Defense Secretary Hegseth (May 2026) and Secretary Rubio (Apr-Jun 2026) call Cuba a national-security threat that hosts Chinese and Russian intelligence sites. Havana and Beijing deny it.',
     'terms': []},
    # ── preparation ──
    {'id': 'surveillance_flights', 'phase': 'preparation',
     'label': 'US surveillance flights off the coast',
     'precedent': 'Surveillance and bomber flights off Venezuela through autumn 2025.',
     'standing': 'At least 25 US Navy and Air Force intelligence flights off Cuba since February 2026, mostly near Havana and Santiago (CNN, May 2026).',
     'terms': []},
    {'id': 'contingency_planning', 'phase': 'preparation',
     'label': 'Military contingency planning reported',
     'precedent': 'Reported planning and a covert-action authorisation (Oct 2025).',
     'standing': 'The Army Reserve is reviewing which support units could serve Southern Command for 90-120 days (CBS, Sep 25 2026). No deployment orders reported.',
     'terms': []},
    # ── final (live only) ──
    {'id': 'force_massing', 'phase': 'final',
     'label': 'Forces massing near Cuba',
     'precedent': 'An aircraft carrier group arrived in the Caribbean about seven weeks before the raid (Nov 2025).',
     'terms': [('carrier', 'cuba'), ('carrier', 'caribbean'), ('portaaviones', 'cuba'),
               ('amphibious', 'cuba'), ('marines', 'deploy', 'cuba'), ('troops', 'deploy', 'cuba'),
               ('warships', 'cuba', 'buildup'), ('military buildup', 'cuba'), ('build-up', 'cuba'),
               ('despliegue militar', 'cuba'), ('tropas', 'cuba', 'despliegue'),
               ('bombers', 'cuba'), ('b-52', 'cuba'), ('b-1', 'cuba')]},
    {'id': 'deployment_orders', 'phase': 'final',
     'label': 'Deployment or mobilisation orders',
     'precedent': 'Forces ordered forward in the weeks before the raid.',
     'terms': [('deployment orders', 'cuba'), ('deployment order', 'southcom'), ('mobiliz', 'reserv', 'southcom'),
               ('mobilis', 'reserv', 'southcom'), ('call-up', 'cuba'), ('orden de despliegue', 'cuba'),
               ('movilizacion', 'reserv', 'cuba')]},
    {'id': 'kinetic_shaping', 'phase': 'final',
     'label': 'US strikes near or on Cuba',
     'precedent': 'US strikes on boats off Venezuela from September 2025.',
     'terms': [('strike', 'off cuba'), ('strike', 'near cuba'), ('strikes on cuba',), ('strike on cuba',),
               ('airstrike', 'cuba'), ('bombs', 'cuba', 'us'), ('ataque', 'estados unidos', 'cuba'),
               ('bombardeo', 'cuba')]},
    {'id': 'airspace_warning', 'phase': 'final',
     'label': 'Airspace warnings or closure',
     'precedent': 'FAA warning to airlines; the President declared Venezuelan airspace "closed" (Nov 29 2025).',
     'terms': [('faa', 'cuba', 'warn'), ('airspace', 'cuba', 'closed'), ('cuban airspace',), ('notam', 'cuba'),
               ('airlines', 'suspend', 'havana'), ('airlines', 'suspend', 'cuba'), ('espacio aereo', 'cuba')]},
    {'id': 'embassy_drawdown', 'phase': 'final',
     'label': 'US embassy drawdown or evacuation',
     'precedent': 'Diplomatic posts and citizens told to leave before a strike.',
     'terms': [('ordered departure', 'havana'), ('ordered departure', 'cuba'), ('embassy', 'havana', 'evacuat'),
               ('embassy', 'havana', 'clos'), ('embassy', 'havana', 'drawdown'), ('americans', 'leave cuba'),
               ('guantanamo', 'families', 'evacuat'), ('embajada', 'la habana', 'evacua')]},
    {'id': 'ultimatum', 'phase': 'final',
     'label': 'Ultimatum to Havana',
     'precedent': 'Public deadlines and offers of exit to Maduro in the final weeks.',
     'terms': [('ultimatum', 'cuba'), ('ultimatum', 'havana'), ('ultimatum', 'diaz-canel'),
               ('ultimatum', 'castro'), ('ultimatum', 'cuba'), ('deadline', 'diaz-canel'),
               ('diaz-canel', 'must leave'), ('ultimatum', 'la habana')]},
]

VZ_STATUS_TEXT = {
    'standing':     'in place (standing fact, dated)',
    'confirmed':    'confirmed this cycle by 2+ outlets',
    'reported_once': 'reported by one outlet this cycle -- not yet confirmed',
    'rumour':       'rumoured or hedged wording only',
    'not_seen':     'not seen',
}

VZ_PURPOSE = [
    {'label': 'Stated: foreign intelligence 90 miles from Florida',
     'text': ('US officials say China and Russia run listening posts in Cuba (Bejucal and others, '
              'reported since 2023). The concern is SPYING -- intercepting US military and space '
              'communications from the Florida coast to Cape Canaveral -- not attack.')},
    {'label': 'Stated: regime change',
     'text': ('The White House calls Cuba a failed state and wants its leaders gone. With Caracas '
              'now working with Washington, Havana has lost its oil lifeline and its closest ally.')},
    {'label': 'In play, rarely said: migration',
     'text': ('A Cuban collapse would send people to Florida by sea (Mariel 1980: 125,000 in six '
              'months). Every option -- a deal, an operation, or waiting -- is also about controlling that.')},
    {'label': 'What it is NOT, on current evidence: a launch pad',
     'text': ('Nothing reported puts Russian or Iranian offensive weapons in Cuba. That is the 1962 '
              'line, and the tracker watches it as a red line (weapons staging needs two adversaries '
              'and 2+ outlets).')},
]

VZ_IF_IT_HAPPENS = {
    'local':    'Fighting around Havana and the military; a grid already at a third of demand would fail further. Guantánamo becomes a base inside a war zone.',
    'regional': 'A sea departure toward Florida and onward routes through Mexico and Central America; Caribbean shipping and tourism disrupted.',
    'global':   ("Russia and China would protest, but neither defended Maduro. Little direct oil-price "
                 "effect: Cuba imports oil, it does not export it. The bigger signal is to Moscow and "
                 "Beijing about the hemisphere."),
}


def _vz_term_hit(text, terms):
    return any(all(t in text for t in combo) for combo in terms)


def build_venezuela_pattern(articles):
    """Checklist read: which steps that preceded the Maduro raid are in place
    for Cuba. Never a probability. Final steps must be in this cycle's news."""
    led = TripwireLedger()
    for a in articles or []:
        text = _atext(a)
        for step in VZ_PATTERN:
            if step['terms'] and _vz_term_hit(text, step['terms']):
                led.add(step['id'], a, text)
    steps = []
    for step in VZ_PATTERN:
        r = led.result(step['id']) if step['terms'] else {'grade': 'none', 'outlets': [], 'items': []}
        g = r.get('grade', 'none')
        if step.get('standing'):
            status = 'standing'
        else:
            status = {'corroborated': 'confirmed', 'single_source': 'reported_once',
                      'rumint': 'rumour'}.get(g, 'not_seen')
        steps.append({
            'id': step['id'], 'phase': step['phase'], 'label': step['label'],
            'status': status, 'status_text': VZ_STATUS_TEXT[status],
            'precedent': step['precedent'],
            'evidence': step.get('standing') or '',
            'as_of': VZ_PATTERN_ASOF if step.get('standing') else '',
            'outlets': r.get('outlets', [])[:4],
            'items': r.get('items', [])[:2],
        })
    in_place = [s for s in steps if s['status'] in ('standing', 'confirmed')]
    final = [s for s in steps if s['phase'] == 'final']
    f_conf = [s for s in final if s['status'] == 'confirmed']
    f_once = [s for s in final if s['status'] == 'reported_once']
    f_rum = [s for s in final if s['status'] == 'rumour']
    names = lambda xs: ', '.join(x['label'][:1].lower() + x['label'][1:] for x in xs)

    if len(f_conf) >= 2:
        level = 4
        read = (f'{len(f_conf)} of the final steps that came right before the Maduro raid are now '
                f'confirmed by 2+ outlets: {names(f_conf)}. In Venezuela these arrived in the last '
                'seven weeks. This is what preparing an operation looks like -- it is not proof one '
                'has been ordered.')
        short = f'Venezuela pattern: {len(f_conf)} final-stage steps confirmed ({names(f_conf)})'
    elif len(f_conf) == 1:
        level = 3
        read = (f'One of the final steps that came before the Maduro raid is confirmed: {names(f_conf)}. '
                'One step is a signal, not a pattern. Watch for the others: forces massing, deployment '
                'orders, airspace warnings, an embassy drawdown, an ultimatum.')
        short = f'Venezuela pattern: a final-stage step is confirmed ({names(f_conf)})'
    else:
        level = 2
        read = (f'{len(in_place)} of {len(steps)} steps that preceded the January raid on Maduro are in '
                'place for Cuba -- all of them pressure and planning, standing for months. None of the '
                'final steps from Venezuela\'s last weeks (forces massing, deployment orders, strikes, '
                'airspace warnings, embassy drawdown, an ultimatum) is confirmed. Read: a squeeze aimed '
                'at a deal or a collapse, with a military option being prepared -- not an operation '
                'under way.')
        short = (f'Venezuela pattern: {len(in_place)} of {len(steps)} steps in place; '
                 'no final-stage step confirmed')
    if f_once:
        read += f' Reported by one outlet only, not yet confirmed: {names(f_once)}.'
    if f_rum:
        read += f' Rumoured, not reported as fact: {names(f_rum)}.'
    return {
        'as_of': VZ_PATTERN_ASOF,
        'level': level,
        'in_place': len(in_place), 'total': len(steps),
        'final_confirmed': [s['id'] for s in f_conf],
        'final_reported_once': [s['id'] for s in f_once],
        'final_rumour': [s['id'] for s in f_rum],
        'read': read, 'short': short,
        'steps': steps,
        'purpose': VZ_PURPOSE,
        'if_it_happens': VZ_IF_IT_HAPPENS,
        'not_implied': ('A checklist against one precedent, not a forecast. Cuba is 90 miles from '
                        'Florida, so an operation might need less visible build-up than Venezuela did; '
                        'equally, Washington is holding talks with Havana and US forces are committed to '
                        'the Iran theatre. The final steps are the ones that would change this read.'),
    }


def interpret_signals(scan_data):
    actor_results = scan_data.get('actors', {})
    articles = scan_data.get('articles', [])
    red_lines_triggered = check_red_lines(articles, actor_results)
    vectors = {k: scan_data.get(k, 0) for k in ('us_pressure', 'regime_fracture', 'adversary_access',
                                                 'civilian_pressure_level')}
    historical_matches = build_historical_matches(actor_results, vectors)
    so_what = build_so_what(scan_data, red_lines_triggered, historical_matches)
    rumint = _score_rumint({'rumint_articles': articles,
                            'rumint_reddit': scan_data.get('rumint_reddit', [])})
    return {'red_lines': red_lines_triggered, 'so_what': so_what,
            'historical_matches': historical_matches, 'rumint': rumint}


print('[Cuba Interpreter] Module loaded -- v1.3.0 (evidence-graded red lines, Venezuela-pattern checklist)')
