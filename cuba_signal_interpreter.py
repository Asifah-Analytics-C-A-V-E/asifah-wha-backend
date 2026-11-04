"""
cuba_signal_interpreter.py
Asifah Analytics -- WHA Backend Module
v1.2.0 -- Nov 4, 2026   (v1.1.0 May 17 2026)

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
        main = 'Hardship is visible -- blackouts and shortages -- but nothing high-impact is confirmed.'
    else:
        main = 'Nothing high-impact is confirmed in Cuba this cycle.'
    if approaching and not breached:
        main += ' Watching: ' + approaching[0]['label'] + ', reported by one outlet only.'
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


print('[Cuba Interpreter] Module loaded -- v1.2.0 (evidence-graded red lines, build_top_signals present)')
