"""
Asifah Analytics -- Patron Axis Reader
v1.0.0 -- July 23 2026  |  portable primitive, Cuba profile first

═══════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════
"Who is propping this regime up, and can they still afford to?"

Cuba's tracker could answer the first half with keywords -- PDVSA shipments,
Maduro visits, Russian tankers. It would then own a second copy of vocabulary
that Venezuela's and DPRK's own trackers already maintain properly, and the two
copies would drift apart within a month.

So this reads their CROSS-THEATER FINGERPRINTS instead. Emit once, consume many:
the patron trackers stay the authority on their own theaters, and Cuba consumes
a level rather than re-deriving one.

═══════════════════════════════════════════════════════════════════════
THE ANALYTICAL POINT: CAPACITY, NOT INTENT
═══════════════════════════════════════════════════════════════════════
The naive patron read asks "is Caracas still supporting Havana?" That is the
less interesting half. Venezuela's own fingerprint carries `inbound.us_level` --
how hard Venezuela itself is being squeezed -- and a patron under acute pressure
is a lifeline at risk regardless of intent. Willingness is not capability.

That produces a causal chain the platform can now actually observe end to end:

    US pressure on Venezuela  ->  Venezuelan oil lifeline degrades
      ->  Cuban fuel and power scarcity deepens
      ->  civilian pressure rises  ->  internal fracture risk

Every link is independently sourced from a different tracker. That is a compound
read in the doctrinal sense: not one feed asserting a story, but separate
instruments agreeing.

═══════════════════════════════════════════════════════════════════════
POLARITY WARNINGS CARRIED FROM THE SOURCE
═══════════════════════════════════════════════════════════════════════
DPRK's fingerprint ships an explicit `polarity_note`: it escalates when its
leverage DECAYS, so a low integrity reading means HIGH pressure. Reading its
level as a stability score inverts the meaning. This module surfaces that note
rather than silently flattening it -- the wrong-mode failure ("confident
nonsense") is the one that looks most like a working system.

═══════════════════════════════════════════════════════════════════════
DOCTRINE
═══════════════════════════════════════════════════════════════════════
Absence-honest. A patron with no fingerprint is reported as NOT OBSERVABLE --
never as "not supporting". Stale fingerprints are surfaced with their age rather
than used silently. Convergence, not prediction.

COPYRIGHT (c) 2025-2026 Asifah Analytics. All rights reserved.
"""

import os
import json
from datetime import datetime, timezone

import requests

__version__ = '1.0.0'

UPSTASH_REDIS_URL   = (os.environ.get('UPSTASH_REDIS_URL')
                       or os.environ.get('UPSTASH_REDIS_REST_URL') or '')
UPSTASH_REDIS_TOKEN = (os.environ.get('UPSTASH_REDIS_TOKEN')
                       or os.environ.get('UPSTASH_REDIS_REST_TOKEN') or '')

FRESHNESS_HOURS = 24     # platform standard for spoke reads


# ============================================================
# REDIS
# ============================================================
def _redis_get(key):
    if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
        return None
    if not UPSTASH_REDIS_URL.startswith('http'):
        print("[Patron Axis] ABORT -- UPSTASH_REDIS_URL is not an https REST URL.")
        return None
    try:
        r = requests.get('%s/get/%s' % (UPSTASH_REDIS_URL, key),
                         headers={'Authorization': 'Bearer %s' % UPSTASH_REDIS_TOKEN},
                         timeout=8)
        if r.status_code != 200:
            return None
        val = (r.json() or {}).get('result')
        return json.loads(val) if val else None
    except Exception as e:
        print('[Patron Axis] GET %s error: %s' % (key, str(e)[:100]))
        return None


# ============================================================
# PROFILES
# ============================================================
CUBA_PROFILE = {
    'country': 'cuba',
    'display': 'Cuba',
    'patrons': {
        'venezuela': {
            'name': 'Venezuela',
            # Both conventions are live on the platform; try each. This is the
            # param-naming split, handled defensively rather than assumed away.
            'keys': ['crosstheater:venezuela:fingerprint', 'fingerprint:venezuela:current'],
            'lifeline': 'oil',
            'dependency': 'high',
            'note': ('The oil lifeline. Cuban thermoelectric generation and transport '
                     'fuel have run on Venezuelan crude since the Chavez era; the '
                     'blackout cycle tracks shipment volume more closely than it '
                     'tracks generating capacity.'),
            'capacity_field': 'inbound.us_level',
            'capacity_note': ('Venezuela is itself a contested node. US pressure on '
                              'Caracas is pressure on Havana one step removed.'),
        },
        'russia': {
            'name': 'Russia',
            'keys': ['crosstheater:russia:fingerprint', 'fingerprint:russia:current'],
            'lifeline': 'oil, wheat, debt relief',
            'dependency': 'medium',
            'note': ('Post-2022 Russia has restored a Cuban presence -- oil cargoes, '
                     'wheat, debt rescheduling, naval visits. Capacity is constrained '
                     'by its own war economy.'),
        },
        'china': {
            'name': 'China',
            'keys': ['crosstheater:china:fingerprint', 'fingerprint:china:current'],
            'lifeline': 'credit, infrastructure, SIGINT',
            'dependency': 'medium',
            'note': ('Largest creditor and the most capable patron. Presence is '
                     'commercial and signals-related rather than fuel-based.'),
        },
        'iran': {
            'name': 'Iran',
            'keys': ['crosstheater:iran:fingerprint', 'fingerprint:iran:current'],
            'lifeline': 'sanctions-evasion tradecraft, fuel cargoes',
            'dependency': 'low',
            'note': ('Sanctions-evasion partner more than a supplier; the useful '
                     'export is method, not volume.'),
        },
        'dprk': {
            'name': 'DPRK',
            'keys': ['crosstheater:dprk:fingerprint'],
            'lifeline': 'arms, labour',
            'dependency': 'low',
            # DPRK's own fingerprint declares inverted polarity. Carry it.
            'inverted_polarity': True,
            'expeditionary_check': True,
            'note': ('Historically an arms and labour relationship. The fingerprint '
                     'carries INVERTED polarity -- Pyongyang escalates as leverage '
                     'decays -- so its level is not a support measure.'),
        },
    },
}

PROFILES = {'cuba': CUBA_PROFILE}


# ============================================================
# HELPERS
# ============================================================
def _dig(d, dotted):
    cur = d
    for part in (dotted or '').split('.'):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _age_hours(fp):
    for f in ('ts', 'updated_at', 'generated_at', 'scan_date'):
        v = (fp or {}).get(f)
        if not v:
            continue
        try:
            t = datetime.fromisoformat(str(v).replace('Z', '+00:00'))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            return round((datetime.now(timezone.utc) - t).total_seconds() / 3600.0, 1)
        except Exception:
            continue
    return None


def _level_of(fp):
    for f in ('level', 'theatre_score', 'score', 'escalation_level'):
        v = (fp or {}).get(f)
        if v is not None:
            try:
                return int(float(v))
            except (TypeError, ValueError):
                continue
    return None


# ============================================================
# PATRON READ
# ============================================================
def read_patron(pid, pdef):
    """Read one patron's fingerprint. Absence-honest: not found is 'not
    observable', never 'not supporting'."""
    fp, used_key = None, None
    for k in pdef['keys']:
        fp = _redis_get(k)
        if fp:
            used_key = k
            break

    if not fp:
        return {
            'id': pid, 'name': pdef['name'], 'present': False, 'fresh': False,
            'level': None, 'age_hours': None, 'key_used': None,
            'lifeline': pdef.get('lifeline'), 'dependency': pdef.get('dependency'),
            'status': 'not_observable',
            'assessment': ('No fingerprint published by the %s tracker. This is an '
                           'absence of observation, NOT an assessment that support has '
                           'stopped.' % pdef['name']),
        }

    age = _age_hours(fp)
    fresh = (age is not None and age <= FRESHNESS_HOURS)
    lvl = _level_of(fp)

    out = {
        'id': pid, 'name': pdef['name'], 'present': True, 'fresh': fresh,
        'level': lvl, 'age_hours': age, 'key_used': used_key,
        'lifeline': pdef.get('lifeline'), 'dependency': pdef.get('dependency'),
        'note': pdef.get('note'),
        'status': 'live' if fresh else 'stale',
    }

    # Patron capacity -- can this patron still afford to prop anyone?
    cap_field = pdef.get('capacity_field')
    if cap_field:
        stress = _dig(fp, cap_field)
        if stress is not None:
            try:
                stress = int(float(stress))
            except (TypeError, ValueError):
                stress = None
        out['patron_stress'] = stress
        out['capacity_note'] = pdef.get('capacity_note')
        if stress is not None:
            if stress >= 4:
                out['capacity'] = 'strained'
                out['capacity_read'] = ('%s is itself under acute pressure (L%d). A '
                                        'patron at this level is a lifeline at risk '
                                        'irrespective of intent -- willingness is not '
                                        'capability.' % (pdef['name'], stress))
            elif stress >= 2:
                out['capacity'] = 'pressured'
                out['capacity_read'] = ('%s is under moderate pressure (L%d); lifeline '
                                        'continuity is a live question rather than an '
                                        'assumption.' % (pdef['name'], stress))
            else:
                out['capacity'] = 'unconstrained'
                out['capacity_read'] = ('%s shows no acute external pressure this cycle.'
                                        % pdef['name'])

    # Inverted-polarity patrons: carry the source's own warning through
    if pdef.get('inverted_polarity'):
        out['inverted_polarity'] = True
        out['polarity_note'] = fp.get('polarity_note') or (
            'Source tracker declares inverted polarity: escalation rises as leverage '
            'decays. Do not read this level as a support or stability measure.')
        for f in ('leverage_integrity', 'leverage_state'):
            if f in fp:
                out[f] = fp[f]

    # Expeditionary presence -- the direct "are they physically here?" test
    if pdef.get('expeditionary_check'):
        hosts = fp.get('expeditionary_hosts') or []
        hosts_l = [str(h).lower() for h in hosts]
        out['expeditionary_hosts'] = hosts
        out['expeditionary_band'] = fp.get('expeditionary_band')
        out['host_match'] = any('cuba' in h for h in hosts_l)
        if out['host_match']:
            out['assessment'] = ('%s expeditionary footprint lists Cuba among its hosts '
                                 '-- a direct presence signal rather than an inference '
                                 'from rhetoric.' % pdef['name'])

    if 'assessment' not in out:
        if not fresh:
            out['assessment'] = ('Fingerprint present but %.0fh old (freshness gate %dh). '
                                 'Surfaced with its age rather than used as current.'
                                 % (age or 0, FRESHNESS_HOURS))
        else:
            out['assessment'] = ('%s fingerprint live at L%s.'
                                 % (pdef['name'], lvl if lvl is not None else '?'))
    return out


# ============================================================
# MAIN
# ============================================================
def compute_patron_axis(country='cuba', civilian_pressure_level=None):
    """
    Read every configured patron and compute the composite lifeline read.

    `civilian_pressure_level` (0-5, from the local tracker) enables the compound
    read: a strained oil patron co-occurring with domestic scarcity is a
    different object from either alone.
    """
    profile = PROFILES.get(country) or CUBA_PROFILE
    reads = [read_patron(pid, pdef) for pid, pdef in profile['patrons'].items()]

    live    = [r for r in reads if r.get('fresh')]
    stale   = [r for r in reads if r.get('present') and not r.get('fresh')]
    missing = [r for r in reads if not r.get('present')]
    strained = [r for r in live if r.get('capacity') == 'strained']

    # Band on OBSERVABLE support breadth, never on absence.
    if not live:
        band, label, color = 'unobservable', 'PATRON AXIS NOT OBSERVABLE', '#6b7280'
    elif strained:
        band, label, color = 'lifeline_at_risk', 'LIFELINE AT RISK -- PATRON UNDER PRESSURE', '#dc2626'
    elif len(live) >= 3:
        band, label, color = 'broad', 'BROAD PATRON SUPPORT OBSERVABLE', '#f59e0b'
    elif len(live) >= 1:
        band, label, color = 'partial', 'PARTIAL PATRON SUPPORT OBSERVABLE', '#3b82f6'
    else:
        band, label, color = 'unobservable', 'PATRON AXIS NOT OBSERVABLE', '#6b7280'

    compound = _compound_read(profile, live, strained, civilian_pressure_level)

    return {
        'module': 'patron_axis', 'version': __version__,
        'country': country,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'band': band, 'band_label': label, 'color': color,
        'patrons_live': len(live), 'patrons_total': len(reads),
        'patrons_stale': [r['name'] for r in stale],
        'patrons_not_observable': [r['name'] for r in missing],
        'strained_patrons': [r['name'] for r in strained],
        'reads': reads,
        'compound_read': compound,
        'prose': _prose(profile, band, live, stale, missing, strained, compound),
        'disclaimer': ('This is a CONVERGENCE indicator, NOT a probability of action. '
                       'Patron levels are read from each patron tracker own-published '
                       'fingerprint; absence of a fingerprint is absence of observation, '
                       'not evidence that support has ceased.'),
        'methodology': ('Reads cross-theater fingerprints published by the patron '
                        'trackers rather than re-deriving them from Cuban-corpus '
                        'keywords -- emit once, consume many. Capacity is assessed '
                        'separately from intent: a patron under acute pressure is a '
                        'lifeline at risk regardless of willingness.'),
    }


def _compound_read(profile, live, strained, civ_press):
    """The chain worth naming: patron under pressure + local scarcity."""
    if civ_press is None:
        return None
    try:
        civ = int(civ_press)
    except (TypeError, ValueError):
        return None

    oil_patrons = [r for r in live if (r.get('lifeline') or '').startswith('oil')]
    oil_strained = [r for r in oil_patrons if r.get('capacity') == 'strained']

    if oil_strained and civ >= 3:
        return {
            'active': True, 'severity': 'high',
            'headline': ('Oil-lifeline patron under pressure while domestic scarcity is '
                         'elevated -- independent layers converging'),
            'detail': ('%s (the Cuban oil lifeline) reads as strained by external pressure '
                       'in the same cycle that Cuban civilian-pressure signals sit at L%d. '
                       'These are two independently sourced layers -- the patron own-published '
                       'tracker and the Cuban corpus -- pointing at the same mechanism: '
                       'pressure applied to Caracas transmits to Havana as fuel and power '
                       'scarcity. This is the pattern that has historically preceded the '
                       'sharpest phases of Cuban domestic unrest, the post-Soviet Special '
                       'Period being the reference case. CONVERGENCE indicator, not a '
                       'prediction of unrest.'
                       % (', '.join(r['name'] for r in oil_strained), civ)),
        }
    if oil_strained:
        return {
            'active': True, 'severity': 'watch',
            'headline': 'Oil-lifeline patron under pressure; domestic scarcity not yet elevated',
            'detail': ('%s reads as strained, but Cuban civilian-pressure signals remain '
                       'at L%d. The transmission lag between patron stress and domestic '
                       'scarcity is the thing to watch, not the patron level alone.'
                       % (', '.join(r['name'] for r in oil_strained), civ)),
        }
    if civ >= 4 and not oil_patrons:
        return {
            'active': True, 'severity': 'watch',
            'headline': 'Domestic scarcity elevated with no observable oil-patron support',
            'detail': ('Civilian pressure at L%d with no oil-lifeline patron fingerprint '
                       'fresh this cycle. Absence of observation is not absence of '
                       'supply -- but the platform cannot currently see who, if anyone, '
                       'is covering the gap.' % civ),
        }
    return {'active': False, 'severity': 'none',
            'headline': 'No patron-scarcity convergence this cycle', 'detail': ''}


def _prose(profile, band, live, stale, missing, strained, compound):
    disp = profile['display']
    if band == 'unobservable':
        return ('%s patron axis: no patron fingerprint is fresh this cycle. The platform '
                'cannot observe who is currently propping Havana -- which is a statement '
                'about our instrumentation, not about Cuban supply lines.' % disp)

    parts = ['%s patron axis: %d of %d patrons observable this cycle (%s).'
             % (disp, len(live), len(live) + len(stale) + len(missing),
                ', '.join(r['name'] for r in live))]

    for r in live:
        if r.get('capacity_read'):
            parts.append(r['capacity_read'])
        if r.get('inverted_polarity'):
            parts.append('%s carries INVERTED polarity from its own tracker -- escalation '
                         'rises as leverage decays, so its level is not a support measure.'
                         % r['name'])
        if r.get('host_match'):
            parts.append(r.get('assessment', ''))

    if compound and compound.get('active'):
        parts.append(compound['headline'] + '.')

    if missing:
        parts.append('Not observable: %s -- no fingerprint published, which is an absence '
                     'of observation rather than an assessment that support has stopped.'
                     % ', '.join(r['name'] for r in missing))
    if stale:
        parts.append('Stale beyond the %dh gate: %s.'
                     % (FRESHNESS_HOURS, ', '.join(r['name'] for r in stale)))
    return ' '.join(p for p in parts if p)


# ============================================================
# SELF-TEST
# ============================================================
if __name__ == '__main__':
    print('Patron Axis Reader v%s -- self-test\n' % __version__)
    now = datetime.now(timezone.utc).isoformat()

    FAKE = {}
    globals()['_redis_get'] = lambda k: FAKE.get(k)

    print('TEST 1 -- nothing published (absence-honest)')
    r = compute_patron_axis('cuba', civilian_pressure_level=2)
    print('  band:', r['band_label'])
    print(' ', r['prose'][:140], '...')
    assert r['band'] == 'unobservable'
    assert all(x['status'] == 'not_observable' for x in r['reads'])
    print('  OK -- reads as NOT OBSERVABLE, never as "not supporting"\n')

    print('TEST 2 -- Venezuela strained + Cuban scarcity high (the chain)')
    FAKE['crosstheater:venezuela:fingerprint'] = {
        'ts': now, 'country': 'venezuela', 'node_class': 'contested_node',
        'level': 4, 'inbound': {'us_level': 5, 'russia_level': 2,
                                'iran_level': 2, 'china_level': 1}}
    FAKE['crosstheater:russia:fingerprint'] = {'ts': now, 'level': 3}
    r2 = compute_patron_axis('cuba', civilian_pressure_level=4)
    print('  band:', r2['band_label'])
    vz = [x for x in r2['reads'] if x['id'] == 'venezuela'][0]
    print('  VZ capacity:', vz['capacity'], '| stress L%s' % vz['patron_stress'])
    print('  compound:', r2['compound_read']['headline'])
    assert r2['band'] == 'lifeline_at_risk'
    assert vz['capacity'] == 'strained'
    assert r2['compound_read']['severity'] == 'high'
    print('\n  DETAIL:\n  ', r2['compound_read']['detail'][:330], '...')
    print('\n  OK -- patron CAPACITY read, and the cross-theater chain fires\n')

    print('TEST 3 -- DPRK inverted polarity is carried, not flattened')
    FAKE['crosstheater:dprk:fingerprint'] = {
        'ts': now, 'theatre': 'dprk', 'level': 2,
        'leverage_integrity': 0.3, 'leverage_state': 'decaying',
        'polarity_note': ('INVERTED -- the DPRK escalates when leverage DECAYS. '
                          'Low integrity = HIGH escalation pressure.'),
        'expeditionary_band': 'active', 'expeditionary_hosts': ['Russia', 'Cuba']}
    r3 = compute_patron_axis('cuba', civilian_pressure_level=4)
    dp = [x for x in r3['reads'] if x['id'] == 'dprk'][0]
    print('  inverted flag:', dp.get('inverted_polarity'))
    print('  polarity note carried:', (dp.get('polarity_note') or '')[:70], '...')
    print('  expeditionary host match (Cuba):', dp.get('host_match'))
    assert dp.get('inverted_polarity') and dp.get('host_match')
    print('  OK -- source polarity warning preserved; direct presence detected\n')

    print('TEST 4 -- stale fingerprint surfaced with its age')
    old = (datetime.now(timezone.utc).replace(year=2026, month=7, day=1)).isoformat()
    FAKE['crosstheater:china:fingerprint'] = {'ts': old, 'level': 3}
    r4 = compute_patron_axis('cuba', civilian_pressure_level=1)
    cn = [x for x in r4['reads'] if x['id'] == 'china'][0]
    print('  china status:', cn['status'], '| age %sh' % cn['age_hours'])
    assert cn['status'] == 'stale' and not cn['fresh']
    print('  OK -- stale is surfaced, not silently used\n')

    print('ALL PATRON-AXIS TESTS PASSED')
