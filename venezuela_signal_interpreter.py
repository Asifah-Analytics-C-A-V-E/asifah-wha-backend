"""
Venezuela Signal Interpreter — v1.1.0 (Nov 4 2026)   [v1.0.0 May 21 2026]

Red lines + executive summary + so-what factor + commodity coupling +
coalition signals. Imported by rhetoric_tracker_venezuela.py at scan time.

═══════════════════════════════════════════════════════════════════
v1.1.0 (Nov 4 2026)
═══════════════════════════════════════════════════════════════════
- EVIDENCE-GRADED RED LINES. A red line used to "fire" on one phrase in
  one headline. Now each has a status:
     breached    -- 2+ distinct outlets, unhedged wording
     approaching -- exactly one outlet
     watching    -- hedged wording or social media only (rumour lane)
  Only BREACHED red lines go in `red_lines` (and red_lines_count), so the
  BLUF's "N red lines breached" is true. The rest are in red_lines_watch.
- MILESTONES. Under the US plan a vacancy declaration and an election
  date are transition steps, not ruptures. They moved out of RED_LINES
  into `milestones`.
- NEW RED LINE: transition spoiler (postponement, a court blocking the
  vote, an attack on a candidate).
- PLAIN LANGUAGE everywhere: no "L3", no actor_key names in reader text.
- Stale May-2026 claims removed (90-day cap, the Hague trip, the James
  Story quote, USS Nimitz).

KEY PATTERNS (as of Nov 4 2026 -- re-verify)
1. A US-backed transition toward 2027 elections: Machado back in the
   country (Oct 25), Rodríguez promising elections (Oct 29), Rubio-Blanco
   talks (Nov 3).
2. Cabello remains the wild card: indicted, and positioned to spoil.
3. Essequibo: an ICJ ruling is expected soon.
4. Earthquake aftermath (Jun 24) strains state capacity.
5. Chavismo residual: Maduro's New York case (new charges Oct 15).

Author: Asifah Analytics
"""

import re


# ════════════════════════════════════════════════════════════════════
# EVIDENCE HELPERS (mirror the tracker's rules)
# ════════════════════════════════════════════════════════════════════
CORROBORATION = 2
SOCIAL = ('reddit', 'bluesky', 'telegram')

_HEDGE_RX = re.compile(
    r"\b(could|may|might|would|warns?|warning of|fears?|feared|risk of|"
    r"threat(?:ens)? to|possible|possibly|potential|rumou?rs?|rumou?red|"
    r"reportedly considering|weighs|mulls|if\b|unconfirmed|alleged plan|"
    r"podr[íi]a|podr[íi]an|posible|posiblemente|advierte|teme|temen|"
    r"rumores?|presunto plan|no confirmad[oa]|eventual)\b",
    re.IGNORECASE)
_MONTH_MAY_RX = re.compile(
    r"\b(?:in|of|since|by|until|early|late|mid-?|next|last|this|on)\s+May\b|\bMay\s+\d",
    re.IGNORECASE)


def _hedged(text):
    return bool(_HEDGE_RX.search(_MONTH_MAY_RX.sub(' ', text or '')))


ACTOR_PLAIN = {
    'us_government':            'the US government',
    'us_sanctions_regulatory':  'US sanctions policy',
    'us_military_posture':      'US military posture',
    'us_vz_envoys':             'the US-Venezuela diplomatic channel',
    'vz_delcy_rodriguez':       'Delcy Rodríguez',
    'vz_jorge_rodriguez':       'the National Assembly',
    'vz_yvan_gil':              'the foreign ministry',
    'vz_diosdado_cabello':      'Diosdado Cabello',
    'vz_internal_security':     'the security forces',
    'vz_opposition':            'the opposition',
    'vz_chavismo_residual':     'Maduro loyalists',
    'russia_vz_axis':           'Russia',
    'china_vz_axis':            'China',
    'iran_vz_axis':             'Iran',
    'hizballah_vz_signals':     'Hizballah-linked networks',
    'essequibo_guyana_dispute': 'the Essequibo dispute',
}


# ════════════════════════════════════════════════════════════════════
# RED LINES
# 'plain' says what crossing the line would MEAN, in one sentence.
# ════════════════════════════════════════════════════════════════════
RED_LINES = {
    'rl_detente_collapse': {
        'name':       'US-Venezuela cooperation collapses',
        'severity':   5,
        'category':   'kinetic',
        'short_text': '🚨 US-Venezuela cooperation collapses -- military pressure returns',
        'long_text':  ('The cooperation track has broken: renewed strike threats, embassy '
                       'withdrawal, sanctions snapped back, or Washington publicly abandoning '
                       'the Rodríguez government.'),
        'plain':      ('If this holds, the military option is back on the table and the '
                       'election plan loses its sponsor.'),
        'triggers':   ['us reverses venezuela', 'second wave venezuela', 'detente collapse',
                       'venezuela ultimatum', 'sanctions reimposed venezuela',
                       'embassy withdrawn venezuela', 'trump threatens venezuela',
                       'us strike venezuela imminent', 'pentagon escalates venezuela'],
    },
    'rl_delcy_ousted': {
        'name':       'Rodríguez removed outside the process',
        'severity':   5,
        'category':   'regime_legitimacy',
        'short_text': '🚨 Rodríguez out -- removed, arrested or resigns outside the transition plan',
        'long_text':  ('Delcy Rodríguez has been removed, arrested, or resigned in a way that '
                       'is not the planned vacancy declaration.'),
        'plain':      ('The transition would lose its manager mid-process; watch Cabello, the '
                       'high command and Washington within hours.'),
        'triggers':   ['delcy arrested', 'delcy ousted', 'rodriguez ousted', 'delcy detention',
                       'delcy removed by', 'rodríguez destituida', 'golpe contra delcy'],
    },
    'rl_military_uprising': {
        'name':       'Armed forces split or coup',
        'severity':   5,
        'category':   'kinetic',
        'short_text': '🚨 Armed forces split -- defections, mutiny or a coup attempt',
        'long_text':  ('Units of the FANB have defected, mutinied, or moved against the '
                       'government, or troops have fired on civilians.'),
        'plain':      ('The new high command built in March would have failed its first real '
                       'test; force, not the election plan, would decide what happens next.'),
        'triggers':   ['fanb defects', 'military coup venezuela', 'golpe de estado venezuela',
                       'venezuela military uprising', 'soldiers fire on civilians',
                       'militares se alzan', 'alzamiento militar'],
    },
    'rl_transition_spoiler': {
        'name':       'Move against the election process',
        'severity':   4,
        'category':   'regime_legitimacy',
        'short_text': '⚠️ Move against the election process -- postponement, court block or attack',
        'long_text':  ('Elections postponed or suspended, a court or the Assembly blocking the '
                       'vote, a leading candidate detained or attacked.'),
        'plain':      ('This is the clearest sign that someone inside the system has decided '
                       'the transition costs them too much.'),
        'triggers':   ['elections postponed venezuela', 'elecciones aplazadas',
                       'elecciones suspendidas', 'postpones elections', 'machado arrested',
                       'machado detenida', 'machado attacked', 'atentado contra machado',
                       'attack on machado', 'tsj blocks', 'tsj suspende',
                       'cabello rejects elections', 'cabello rechaza elecciones',
                       'assembly blocks elections'],
    },
    'rl_mass_opposition': {
        'name':       'General strike or parallel government',
        'severity':   4,
        'category':   'regime_legitimacy',
        'short_text': '⚠️ General strike or a parallel government declared',
        'long_text':  ('A general strike, a declared victory outside any vote, or a parallel '
                       'government. Big rallies alone are normal in a campaign and do not count.'),
        'plain':      ('The opposition would be leaving the negotiated path, which forces '
                       'Washington to choose between its partners.'),
        'triggers':   ['general strike venezuela', 'paro nacional venezuela',
                       'opposition declares victory', 'parallel government venezuela',
                       'gobierno paralelo'],
    },
    'rl_cabello_event': {
        'name':       'Cabello event (arrest, flight or open defiance)',
        'severity':   5,
        'category':   'regime_legitimacy',
        'short_text': '🚨 Cabello event -- arrested, extradited, flees or defies the government',
        'long_text':  ('Diosdado Cabello -- indicted in the US and still powerful at home -- has '
                       'been arrested or extradited, has fled, or has openly defied the government.'),
        'plain':      ('Cabello is the person best placed to spoil the transition; any move by '
                       'or against him changes who can.'),
        'triggers':   ['cabello arrested', 'cabello extradited', 'cabello flees',
                       'cabello defies delcy', 'cabello coup', 'cabello detention',
                       'cabello detenido', 'cabello huye'],
    },
    'rl_maduro_custody': {
        'name':       'Maduro case turning point',
        'severity':   4,
        'category':   'chavismo_residual',
        'short_text': '⚠️ Maduro case turning point -- verdict, plea deal, or death in custody',
        'long_text':  ('A decisive event in Maduro\'s New York case: a verdict, a plea deal, a '
                       'death or hunger strike in custody, or an extradition.'),
        'plain':      ('Loyalists would have a rallying point -- or lose their last one -- just '
                       'as the election plan needs calm.'),
        'triggers':   ['maduro dies in custody', 'maduro hunger strike', 'maduro convicted',
                       'maduro acquitted', 'maduro plea deal', 'maduro found guilty',
                       'maduro extradited argentina', 'cilia flores released'],
    },
    'rl_essequibo_escalation': {
        'name':       'Essequibo turns military',
        'severity':   5,
        'category':   'kinetic',
        'short_text': '🚨 Essequibo -- troops cross, oil blocks seized, or Guyana mobilises',
        'long_text':  ('The dispute with Guyana has left the courtroom: Venezuelan troops in '
                       'Essequibo, Guyana mobilising, ExxonMobil evacuating, or foreign forces '
                       'deploying to defend Guyana.'),
        'plain':      ('A border war in the middle of a transition would hand nationalists the '
                       'agenda and put US and UK forces in the frame.'),
        'triggers':   ['venezuela invades guyana', 'venezuela seizes essequibo',
                       'venezuela troops essequibo', 'guyana mobilizes', 'guyana mobilises',
                       'exxon evacuates guyana', 'oil block seized'],
    },
    'rl_hezbollah_event': {
        'name':       'Hizballah operative or designation in Venezuela',
        'severity':   4,
        'category':   'special_watch',
        'short_text': '⚠️ Hizballah in Venezuela -- arrest, raid or designation',
        'long_text':  ('An arrest, raid or sanctions designation tying Hizballah to Venezuela '
                       '(Margarita Island, diaspora finance, dual-use trade).'),
        'plain':      ('It would test the interim government\'s promise to Washington to end '
                       'Hizballah and Iran activity, and connect to the Tri-Border Area.'),
        'triggers':   ['hezbollah cell arrested venezuela', 'hezbollah attack venezuela',
                       'hezbollah uranium venezuela', 'us designates hezbollah venezuela',
                       'margarita raid', 'hezbollah operative captured venezuela',
                       'hezbolá detenidos venezuela'],
    },
    'rl_humanitarian_crisis': {
        'name':       'Humanitarian emergency',
        'severity':   5,
        'category':   'humanitarian',
        'short_text': '🚨 Humanitarian emergency -- famine, grid collapse or mass exodus',
        'long_text':  ('Declared famine, total grid collapse, a mass-exodus surge, or the health '
                       'system failing.'),
        'plain':      ('People would be leaving faster than any election can help, and the '
                       'shock would land on Colombia, Brazil and Peru first.'),
        'triggers':   ['venezuela famine declared', 'venezuela hambruna declarada',
                       'venezuela total grid collapse', 'venezuela mass exodus',
                       'venezuela healthcare implodes', 'venezuela border emergency'],
    },
    'rl_economic_collapse': {
        'name':       'Economic collapse',
        'severity':   5,
        'category':   'economic',
        'short_text': '🚨 Economic collapse -- currency gone, oil halted, or default',
        'long_text':  'Total bolívar collapse, PDVSA ceasing operations, or a declared default.',
        'plain':      ('The money that keeps the state and the transition running would stop; '
                       'humanitarian strain usually follows within weeks.'),
        'triggers':   ['pdvsa total halt', 'pdvsa cease operations',
                       'venezuela sovereign default oil', 'venezuela bolivar zero',
                       'venezuela currency total collapse'],
    },
}

# Transition milestones -- progress, not rupture (moved out of RED_LINES).
MILESTONE_TEXT = {
    3: 'Binding transition step reported',
    4: 'Campaign phase reported',
    5: 'Voting or results reported',
}


def _scan_articles(scan_data):
    """Every item the scan saw, with its outlet. Falls back to the old shape."""
    arts = scan_data.get('articles')
    if isinstance(arts, list) and arts:
        return arts
    out = []
    for actor in (scan_data.get('actors', {}) or {}).values():
        for a in (actor.get('top_articles') or []):
            src = a.get('source') or {}
            out.append({'title': a.get('title', ''), 'description': a.get('description', ''),
                        'url': a.get('url', ''), 'feed_type': a.get('feed_type', ''),
                        'outlet': (a.get('outlet') or (src.get('name') if isinstance(src, dict) else src)
                                   or 'unknown').lower()})
    return out


def evaluate_red_lines(scan_data):
    """Grade every red line. Returns list of dicts with a status, most severe first."""
    articles = _scan_articles(scan_data)
    results = []
    for rl_id, rl in RED_LINES.items():
        firm, soft, first = set(), set(), None
        for art in articles:
            text = ((art.get('title') or '') + ' ' + (art.get('description') or '')).lower()
            hit = next((t for t in rl['triggers'] if t in text), None)
            if not hit:
                continue
            outlet = (art.get('outlet') or 'unknown').lower()
            if _hedged(text) or art.get('feed_type') in SOCIAL:
                soft.add(outlet)
            else:
                firm.add(outlet)
            if first is None or (outlet in firm and first.get('hedged')):
                first = {'matched_phrase': hit, 'article_title': art.get('title', ''),
                         'url': art.get('url', ''), 'hedged': outlet not in firm}
        if not firm and not soft:
            continue
        if len(firm) >= CORROBORATION:
            status = 'breached'
        elif firm:
            status = 'approaching'
        else:
            status = 'watching'
        results.append({
            'rl_id':          rl_id,
            'name':           rl['name'],
            'severity':       rl['severity'],
            'category':       rl['category'],
            'status':         status,
            'status_text':    {'breached': 'Breached -- 2+ outlets',
                               'approaching': 'Approaching -- 1 outlet, not yet corroborated',
                               'watching': 'Watching -- rumour or hedged wording only'}[status],
            'short_text':     rl['short_text'],
            'long_text':      rl['long_text'],
            'description':    rl['long_text'],
            'plain':          rl['plain'],
            'outlets':        sorted(firm)[:6],
            'rumint_outlets': sorted(soft)[:6],
            'matched_phrase': (first or {}).get('matched_phrase'),
            'article_title':  (first or {}).get('article_title'),
            'url':            (first or {}).get('url'),
        })
    rank = {'breached': 0, 'approaching': 1, 'watching': 2}
    results.sort(key=lambda r: (rank[r['status']], -r['severity']))
    return results


def check_red_lines(scan_data):
    """Back-compat: BREACHED red lines only."""
    return [r for r in evaluate_red_lines(scan_data) if r['status'] == 'breached']


def build_milestones(scan_data):
    """Transition steps with 2+ outlets (stage 3+), from the tracker's transition read."""
    tr = scan_data.get('transition') or {}
    out, seen = [], set()
    for sig in (tr.get('stage_signals') or []):
        lvl = sig.get('level', 0)
        if lvl < 3 or sig.get('phrase') in seen:
            continue
        seen.add(sig.get('phrase'))
        out.append({
            'stage':     lvl,
            'name':      MILESTONE_TEXT.get(lvl, 'Transition step'),
            'phrase':    sig.get('phrase'),
            'article':   sig.get('article'),
            'outlet':    sig.get('outlet'),
            'url':       sig.get('url'),
            'evidence':  sig.get('evidence'),
        })
    return out[:6]


# ════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY  (full sentences, no level codes)
# ════════════════════════════════════════════════════════════════════
LEVEL_WORDS = {0: 'quiet', 1: 'low', 2: 'elevated', 3: 'high', 4: 'very high', 5: 'at crisis level'}


def build_executive_summary(scan_data, red_lines_all=None):
    level   = scan_data.get('theatre_level', 0)
    label   = scan_data.get('theatre_label', 'Stable')
    actors  = scan_data.get('actors', {}) or {}
    tr      = scan_data.get('transition') or {}
    l5_gate = scan_data.get('l5_gate', {}) or {}
    red_lines_all = red_lines_all or []
    breached = [r for r in red_lines_all if r['status'] == 'breached']
    approaching = [r for r in red_lines_all if r['status'] == 'approaching']

    def a(key):
        return (actors.get(key, {}) or {}).get('actor_score', 0)

    # Headline: the main story in one line.
    if l5_gate.get('any'):
        headline = 'Venezuela: crisis conditions confirmed'
    elif breached:
        headline = f'Venezuela: red line breached -- {breached[0]["name"]}'
    elif tr.get('spoiler_grade') == 'corroborated':
        headline = 'Venezuela: the election process is under attack'
    elif tr.get('stage', 0) >= 2:
        headline = 'Venezuela: the transition toward elections is the main story'
    else:
        headline = f'Venezuela reads "{label}" -- no single development dominates'

    parts = []
    stage = tr.get('stage', 0)
    if stage >= 2:
        parts.append(f'The transition has reached this point: {tr.get("stage_text")}.')
    elif stage == 1:
        parts.append('Elections and the transition are being discussed, but this cycle shows no binding step.')
    else:
        parts.append('This cycle\'s reporting says little about the transition itself -- unread, not stalled.')

    if a('vz_opposition') >= 2:
        parts.append('The opposition is active and visible.')
    if a('vz_diosdado_cabello') >= 3 and not any(r['rl_id'] == 'rl_cabello_event' for r in red_lines_all):
        parts.append('Diosdado Cabello is in the news at a level that matters: he is the most likely spoiler.')
    if scan_data.get('diplomatic_level', 0) >= 2:
        parts.append('The US-Venezuela channel is working, which keeps military pressure in the background.')

    pressures = []
    if scan_data.get('civilian_pressure_level', 0) >= 3:
        pressures.append('everyday hardship')
    if scan_data.get('oil_extraction_level', 0) >= 3:
        pressures.append('oil-sector stress')
    if scan_data.get('essequibo_level', 0) >= 3:
        pressures.append('the Essequibo dispute')
    if scan_data.get('earthquake_political_level', 0) >= 2:
        pressures.append('anger over earthquake relief')
    if pressures:
        parts.append('Pressure is coming from ' + ', '.join(pressures) + '.')

    if breached:
        parts.append(f'Red line breached (2+ outlets): {breached[0]["name"]}. {breached[0]["plain"]}')
    elif approaching:
        parts.append(f'One red line is approaching on a single outlet\'s report: {approaching[0]["name"]}. '
                     f'It counts once a second outlet confirms it.')
    else:
        parts.append('No red line is breached.')

    return {'headline': headline, 'paragraph': ' '.join(parts)}


# ════════════════════════════════════════════════════════════════════
# SO WHAT FACTOR
# ════════════════════════════════════════════════════════════════════
def build_so_what_factor(scan_data, red_lines_all):
    diplomatic_lvl = scan_data.get('diplomatic_level', 0)
    civ_press_lvl  = scan_data.get('civilian_pressure_level', 0)
    oil_lvl        = scan_data.get('oil_extraction_level', 0)
    essequibo_lvl  = scan_data.get('essequibo_level', 0)
    l5_gate        = scan_data.get('l5_gate', {}) or {}
    suppressed     = l5_gate.get('l5_ceasefire_suppressed_sources', []) or []
    actors         = scan_data.get('actors', {}) or {}
    tr             = scan_data.get('transition') or {}
    cabello_lvl    = (actors.get('vz_diosdado_cabello', {}) or {}).get('actor_score', 0)
    commodity_alert = ((scan_data.get('commodity_pressure') or {}).get('alert_level') or '').lower()
    breached = [r for r in (red_lines_all or []) if r['status'] == 'breached']

    if l5_gate.get('kinetic') and l5_gate.get('any'):
        scenario, factor = 'kinetic_l5_active', 'MILITARY CRISIS'
        description = ('Military or border conflict is confirmed and the cooperation track is not '
                       'holding it back. Local: the transition stops being the story. Regional: '
                       'Colombia, Guyana and the Caribbean brace for spillover. Global: US forces '
                       'are back in the frame and oil markets will price it.')
        watch_for = ['US naval and air movements in the Caribbean', 'Statements from the high command',
                     'Russia / China condemnation language', 'Civilian movement toward borders']
    elif l5_gate.get('humanitarian') and l5_gate.get('any'):
        scenario, factor = 'humanitarian_l5_active', 'HUMANITARIAN EMERGENCY'
        description = ('Conditions have crossed into a humanitarian emergency. Local: survival '
                       'crowds out politics. Regional: Colombia, Brazil and Peru absorb the first '
                       'wave of departures. Global: a UN appeal and donor politics follow.')
        watch_for = ['UN OCHA appeal', 'Colombian border measures', 'Brazil and Peru border posture',
                     'Who delivers relief -- and who gets credit']
    elif l5_gate.get('economic') and l5_gate.get('any'):
        scenario, factor = 'economic_l5_active', 'ECONOMIC COLLAPSE'
        description = ('The oil economy has stopped working. Local: salaries and services fail '
                       'first. Regional: migration pressure rises within weeks. Global: the US '
                       'arrangement built on Venezuelan oil is under direct strain.')
        watch_for = ['Bolívar exchange rate', 'PDVSA output confirmation',
                     'IMF / IDB engagement', 'US oil-marketing arrangement']
    elif breached:
        rl = breached[0]
        scenario, factor = 'red_line_breached', 'RED LINE BREACHED'
        description = f'{rl["name"]} -- confirmed by 2+ outlets. {rl["plain"]}'
        watch_for = ['A second, independent confirmation of scale', 'Washington\'s response',
                     'Whether the election timetable is mentioned at all']
    elif tr.get('spoiler_grade') == 'corroborated':
        scenario, factor = 'transition_under_strain', 'TRANSITION UNDER STRAIN'
        description = ('More than one outlet reports a move against the election process. Local: '
                       'this is the moment the interim government shows whether it owns the '
                       'transition or only manages it. Regional: neighbours that absorbed eight '
                       'million Venezuelans watch for a new exodus. Global: Washington\'s plan has '
                       'its first real test.')
        watch_for = ['Rodríguez\'s response within 48 hours', 'Cabello\'s position',
                     'US statements on consequences', 'Opposition call to the street']
    elif suppressed:
        scenario, factor = 'detente_suppressing_pressure', 'COOPERATION HOLDING PRESSURE BACK'
        description = ('Serious military or border pressure is in the reporting, but the US-Venezuela '
                       'cooperation track is holding it back. That track is now the load-bearing '
                       'wall: if it cracks, the reading jumps fast.')
        watch_for = ['Sanctions waivers and oil licences', 'Direct US statements on Rodríguez',
                     'Cabello positioning', 'Election-plan deadlines']
    elif cabello_lvl >= 4:
        scenario, factor = 'cabello_volatility', 'CABELLO WILD CARD'
        description = ('High-impact reporting on Diosdado Cabello, confirmed by 2+ outlets. He is '
                       'indicted in the US and still powerful at home -- the person with the most '
                       'to lose from an election and the most ability to disrupt one.')
        watch_for = ['Cabello public appearances', 'Security-force posture toward the opposition',
                     'US actions against senior PSUV figures']
    elif essequibo_lvl >= 3:
        scenario, factor = 'essequibo_escalation_watch', 'ESSEQUIBO PRESSURE'
        description = ('The Essequibo dispute is escalating beyond the ICJ case. Local: '
                       'nationalism is the easiest card for anyone who wants to slow the '
                       'transition. Regional: Guyana, CARICOM and Brazil are exposed. Global: '
                       'ExxonMobil\'s Stabroek blocks sit in the disputed zone.')
        watch_for = ['The ICJ ruling and Caracas\'s response to it', 'Guyana defence announcements',
                     'ExxonMobil operating posture', 'Any referendum revival']
    elif tr.get('stage', 0) >= 2:
        scenario, factor = 'transition_in_motion', 'TRANSITION IN MOTION'
        description = ('The US-backed transition is moving: ' + tr.get('stage_text', '') + '. '
                       'Local: every binding step (a vacancy declaration, a new electoral council, '
                       'a date) raises the stakes for those who lose power in a fair vote. '
                       'Regional: a credible vote is the best chance in a decade of migrants '
                       'returning. Global: it decides whether the Maduro operation is remembered '
                       'as a transition or a takeover.')
        watch_for = ['A vacancy declaration or election date (needs 2 outlets)',
                     'Naming of a new electoral council (CNE)',
                     'Security for Machado and opposition campaigning',
                     'Whether Washington keeps the pace after the US midterms']
    elif civ_press_lvl >= 3 or oil_lvl >= 3:
        scenario, factor = 'structural_pressure_elevated', 'EVERYDAY PRESSURE BUILDING'
        description = ('Hardship or oil-sector stress is widely reported. These are slow pressures, '
                       'but they are what turns a political spoiler into a street crisis.')
        watch_for = ['Blackout duration', 'PDVSA monthly output', 'Bolívar parallel rate',
                     'Food and medicine shortages']
    elif diplomatic_lvl >= 3:
        scenario, factor = 'detente_steady', 'COOPERATION STEADY'
        description = ('US-Venezuela cooperation is the dominant frame and nothing in this cycle '
                       'challenges it. Steady is not the same as settled: the plan still needs '
                       'binding steps toward a vote.')
        watch_for = ['Oil licence actions', 'Political prisoner releases',
                     'Binding transition steps', 'Russia / China / Iran quiet or not']
    elif commodity_alert == 'surge':
        scenario, factor = 'commodity_surge_pressure', 'COMMERCIAL MOVES AHEAD OF POLITICS'
        description = ('Commodity pressure on Venezuela is at surge while political reporting is '
                       'quiet. Money is moving before the rhetoric -- usually oil licences, new '
                       'offtake deals, or sponsors repositioning.')
        watch_for = ['US licence actions for oil majors', 'PDVSA export volumes',
                     'New oil partners and who backs them', 'Chinese and Russian tanker continuity']
    elif commodity_alert in ('high', 'elevated'):
        scenario, factor = 'commodity_pressure_building', 'COMMODITY PRESSURE BUILDING'
        description = ('Commodity pressure is elevated. Watch whether politics follows the money '
                       'over the next cycles.')
        watch_for = ['Oil-sector regulatory moves', 'Food import flows', 'Gold / Orinoco mining reporting']
    else:
        scenario, factor = 'baseline_quiet', 'QUIET CYCLE'
        description = ('Little high-impact reporting this cycle. In a country mid-transition, a '
                       'quiet cycle is worth noting but is not evidence that the hard steps are done.')
        watch_for = ['First binding transition step', 'Any move against the process']

    for rl in [r for r in (red_lines_all or []) if r['status'] != 'watching'][:3]:
        tag = 'BREACHED' if rl['status'] == 'breached' else 'APPROACHING (1 outlet)'
        watch_for.insert(0, f"{rl['name']} -- {tag}")

    return {'scenario': scenario, 'factor': factor, 'description': description,
            'watch_for': watch_for}


# ════════════════════════════════════════════════════════════════════
# COMMODITY COUPLING SIGNALS
# ════════════════════════════════════════════════════════════════════
COMMODITY_COUPLINGS = {
    'oil': {
        'related_actors': ['us_sanctions_regulatory', 'us_government', 'iran_vz_axis',
                           'russia_vz_axis', 'china_vz_axis'],
        'icon': '🛢️', 'color': '#71717a', 'name': 'Oil',
        'narrative_long': (
            'Oil-market pressure on Venezuela is coinciding with active reporting on US '
            'sanctions or a sponsor state. Oil pays for the Venezuelan state and anchors the '
            'US arrangement, so the two moving together matters more than either alone. '
            'Watch: oil licences, PDVSA output, tanker traffic, new offtake partners.'),
    },
    'gold': {
        'related_actors': ['us_sanctions_regulatory', 'vz_diosdado_cabello',
                           'vz_internal_security', 'hizballah_vz_signals'],
        'icon': '🥇', 'color': '#facc15', 'name': 'Gold',
        'narrative_long': (
            'Gold pressure is coinciding with reporting on the security apparatus, Cabello or '
            'illicit-finance networks. The Orinoco Mining Arc has been the main sanctions-evasion '
            'channel; the gold held at the Bank of England is now a live diplomatic file. '
            'Watch: gold designations, export routes (UAE, Türkiye, Iran).'),
    },
    'wheat': {
        'related_actors': ['russia_vz_axis', 'vz_delcy_rodriguez'],
        'icon': '🌾', 'color': '#84cc16', 'name': 'Wheat',
        'narrative_long': (
            'Wheat pressure is coinciding with reporting on Russia or the government. Most '
            'Venezuelan wheat is imported; bread and flour shortages have triggered protests '
            'before. Watch: import flows, bread-price reports, Black Sea grain signals.'),
    },
}


def _commodity_coupling_signal(commodity_id, commodity_data, actor_results):
    coupling = COMMODITY_COUPLINGS.get(commodity_id)
    if not coupling:
        return None
    alert_level = commodity_data.get('alert_level', 'normal') if isinstance(commodity_data, dict) else 'normal'
    commodity_lvl = {'normal': 0, 'baseline': 0, 'low': 1, 'elevated': 2, 'warning': 2,
                     'high': 3, 'severe': 4, 'critical': 5}.get(str(alert_level).lower(), 0)
    pressure_score = commodity_data.get('commodity_pressure', 0) if isinstance(commodity_data, dict) else 0
    for thr, lv in ((80, 5), (65, 4), (50, 3), (35, 2), (20, 1)):
        if (pressure_score or 0) >= thr:
            commodity_lvl = max(commodity_lvl, lv)
            break
    if commodity_lvl < 2:
        return None
    related_top, related_max = [], 0
    for actor_key in coupling['related_actors']:
        score = (actor_results.get(actor_key, {}) or {}).get('actor_score', 0)
        if score >= 2:
            related_top.append({'actor': actor_key, 'score': score})
            related_max = max(related_max, score)
    if related_max < 2:
        return None
    level = min(5, max(commodity_lvl, related_max))
    who = ', '.join(ACTOR_PLAIN.get(t['actor'], t['actor']) for t in related_top[:3])
    return {
        'category':      'commodity_coupling',
        'commodity':     commodity_id,
        'theatre':       'venezuela',
        'level':         level,
        'short_text':    (f"Venezuela: {coupling['name'].lower()} pressure is moving together with "
                          f"reporting on {who}"),
        'long_text':     coupling['narrative_long'],
        'icon':          coupling['icon'],
        'color':         coupling['color'],
        'priority':      9 + level,
        'pressure_type': 'economic',
        'related_actors': related_top,
    }


def build_commodity_coupling_signals(scan_data):
    commodity_pressure = scan_data.get('commodity_pressure', {}) or {}
    fps = (scan_data.get('commodity_fingerprints', {}) or {}).get('fingerprints', {}) or {}
    actor_results = scan_data.get('actors', {}) or {}
    signals = []
    for commodity_id in ('oil', 'gold', 'wheat'):
        sig = _commodity_coupling_signal(commodity_id, fps.get(commodity_id) or commodity_pressure,
                                         actor_results)
        if sig:
            signals.append(sig)
    return signals


def build_coalition_signals(scan_data):
    """Fires ONLY when >=2 sponsor hubs (Iran/Russia/China) are elevated at once."""
    coalition    = scan_data.get('coalition', {}) or {}
    hub_presence = scan_data.get('hub_presence', {}) or {}
    level  = coalition.get('level', 0)
    detail = coalition.get('detail', {}) or {}
    hub_count = detail.get('hub_count', 0)
    if hub_count < 2 or level < 3:
        return []
    elevated = detail.get('elevated_hubs', {}) or {}
    names = [h.title() for h, _ in sorted(elevated.items(), key=lambda x: -x[1])]
    roles = [f"{h.title()} ({(hub_presence.get(h, {}) or {}).get('role')})"
             for h in elevated if (hub_presence.get(h, {}) or {}).get('role')]
    return [{
        'category':      'coalition_convergence',
        'theatre':       'venezuela',
        'level':         level,
        'short_text':    (f"Venezuela: {' and '.join(names)} are active at the same time -- "
                          f"outside sponsors converging"),
        'long_text':     (f"{hub_count} outside sponsors show elevated activity in Venezuela at once: "
                          f"{'; '.join(roles) if roles else ', '.join(names)}. Several patrons moving "
                          f"together gives Caracas options beyond Washington, which weakens US leverage "
                          f"over the transition. This is a convergence indicator, not a probability of "
                          f"action; each hub is sourced separately."),
        'icon':          '🕸️',
        'color':         '#be185d',
        'priority':      9 + level,
        'pressure_type': 'kinetic',
    }]


# ════════════════════════════════════════════════════════════════════
# MAIN WRAPPER
# ════════════════════════════════════════════════════════════════════
def interpret_venezuela_signals(scan_data):
    red_lines_all         = evaluate_red_lines(scan_data)
    red_lines_breached    = [r for r in red_lines_all if r['status'] == 'breached']
    red_lines_watch       = [r for r in red_lines_all if r['status'] != 'breached']
    executive_summary     = build_executive_summary(scan_data, red_lines_all)
    commodity_top_signals = build_commodity_coupling_signals(scan_data)
    coalition_top_signals = build_coalition_signals(scan_data)
    so_what               = build_so_what_factor(scan_data, red_lines_all)
    milestones            = build_milestones(scan_data)

    for sig in commodity_top_signals[:2]:
        so_what['watch_for'].insert(0, sig['short_text'])
    if coalition_top_signals:
        so_what['watch_for'].insert(0, coalition_top_signals[0]['short_text'])
        so_what['description'] = (so_what['description'].rstrip() +
                                  ' Several outside sponsors are active at once, which gives '
                                  'Caracas options beyond Washington.')
    eq = scan_data.get('earthquake_political_level', 0)
    if eq >= 2:
        so_what['watch_for'].insert(0, 'Earthquake relief -- delays, anger, and who gets credit')
        so_what['description'] = (so_what['description'].rstrip() +
                                  ' The earthquake response is also testing the government; '
                                  'outside sponsors can use relief as a way in.')

    return {
        'red_lines':             red_lines_breached,
        'red_lines_count':       len(red_lines_breached),
        'red_lines_watch':       red_lines_watch,
        'red_lines_all':         red_lines_all,
        'milestones':            milestones,
        'executive_summary':     executive_summary,
        'commodity_top_signals': commodity_top_signals,
        'coalition_top_signals': coalition_top_signals,
        'coalition':             scan_data.get('coalition', {}),
        'so_what':               so_what,
    }


print(f'[VZ Interpreter] Module loaded — {len(RED_LINES)} red lines, evidence-graded (v1.1.0)')
