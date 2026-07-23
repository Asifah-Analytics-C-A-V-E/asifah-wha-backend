"""
Asifah Analytics -- Principal Appearance Cadence Engine
v1.0.0 -- July 23 2026  |  portable primitive, Cuba profile first

═══════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════
The elite-fracture detector (Slice 2) can only see absence when the PRESS
REMARKS ON IT -- "Raul ausente", "no ha sido visto". That is a real ceiling: a
quiet disappearance stays invisible until a journalist notices and writes it
down, which is exactly the window where the signal is most valuable.

This module measures the appearance itself. It learns how often each principal
normally shows up in the corpus, then reports when that stops -- the same
inversion the platform already uses for claiming actors (Hezbollah, the
Houthis, al-Shabaab), where silence IS the signal.

═══════════════════════════════════════════════════════════════════════
THE TWO FAILURE MODES THIS IS BUILT AGAINST
═══════════════════════════════════════════════════════════════════════
1. CORPUS-HEALTH BLINDNESS -- the lesson the Tempo Baseline Engine was built
   to fix. If the RSS feeds break, every principal's appearance count drops to
   zero and a naive detector reports that the entire leadership has vanished.
   It would be hallucinating menace from its own outage. Here every daily
   record carries a corpus denominator, and absence calls are SUPPRESSED when
   corpus health falls below CORPUS_HEALTH_FLOOR of baseline. Feed death reads
   as feed death.

2. FIXED THRESHOLDS -- useless across principals. Diaz-Canel appears in the
   corpus most days; Raul Castro, 94 and semi-retired, may not surface for
   weeks and nothing is wrong. A single "N days missing" rule would either
   scream about Raul constantly or never fire for Diaz-Canel. Baselines are
   therefore LEARNED PER PRINCIPAL from observed history.

═══════════════════════════════════════════════════════════════════════
DOCTRINE
═══════════════════════════════════════════════════════════════════════
Absence-honest throughout. Until MIN_DAYS_READY of history exists the engine
reports "baseline accumulating" and refuses to characterise anything -- it does
not borrow a default and pretend. History is never zero-filled: a day with no
record is a gap, reported as a gap.

Convergence, not prediction. A cadence break is a fact about the past tense --
this principal has not appeared in N days against a learned norm of M. It is
never a forecast about why, or what follows.

STORAGE
  cadence:{country}:daily   -- Redis list, newest first, 120 entries, NO TTL

COPYRIGHT (c) 2025-2026 Asifah Analytics. All rights reserved.
"""

import os
import json
import unicodedata
from datetime import datetime, timezone, timedelta

import requests

__version__ = '1.0.0'

# ============================================================
# CONFIG
# ============================================================
UPSTASH_REDIS_URL   = (os.environ.get('UPSTASH_REDIS_URL')
                       or os.environ.get('UPSTASH_REDIS_REST_URL') or '')
UPSTASH_REDIS_TOKEN = (os.environ.get('UPSTASH_REDIS_TOKEN')
                       or os.environ.get('UPSTASH_REDIS_REST_TOKEN') or '')

HISTORY_CAP        = 120   # ~4 months of daily records
MIN_DAYS_READY     = 10    # below this we say "baseline accumulating" and stop
BASELINE_WINDOW    = 30    # rolling window for the learned norm
CORPUS_HEALTH_FLOOR = 0.55 # below this share of baseline corpus, suppress absence calls


def _fold(s):
    if not s:
        return ''
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s))
                   if not unicodedata.combining(c)).lower()


# ============================================================
# PROFILES
# ============================================================
CUBA_PROFILE = {
    'country': 'cuba',
    'display': 'Cuba',
    'principals': {
        'raul_castro': {
            'name':  'Raul Castro',
            'role':  'Former First Secretary; residual authority',
            'terms': ['raul castro', 'raul modesto castro', 'general de ejercito raul'],
            # Semi-retired and 94 -- long gaps are his NORMAL. The learned
            # baseline matters more here than for any other principal.
            'sensitivity': 1.0,
        },
        'diaz_canel': {
            'name':  'Miguel Diaz-Canel',
            'role':  'President / PCC First Secretary',
            'terms': ['diaz-canel', 'diaz canel', 'presidente cubano',
                      'primer secretario del partido'],
            # Appears near-daily; a gap is loud precisely because his norm is dense.
            'sensitivity': 1.25,
        },
        'marrero': {
            'name':  'Manuel Marrero',
            'role':  'Prime Minister',
            'terms': ['manuel marrero', 'primer ministro cubano'],
            'sensitivity': 0.9,
        },
        'lopez_callejas': {
            'name':  'Luis Alberto Rodriguez Lopez-Callejas',
            'role':  'GAESA -- military economic apparatus',
            'terms': ['lopez-callejas', 'lopez callejas', 'gaesa'],
            # Rarely visible by design; presence is more informative than absence.
            'sensitivity': 0.8,
        },
    },
    # Corpus-health probe: terms that should ALWAYS appear if the feeds are alive.
    # If these collapse, the outage is ours, not Havana's.
    'corpus_probe': ['cuba', 'cubano', 'la habana', 'havana'],
}

PROFILES = {'cuba': CUBA_PROFILE}


# ============================================================
# REDIS
# ============================================================
def _redis_cmd(cmd, timeout=8):
    if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
        return False, None
    if not UPSTASH_REDIS_URL.startswith('http'):
        print("[Cadence] ABORT -- UPSTASH_REDIS_URL is not an https REST URL "
              "(starts with '%s...')." % UPSTASH_REDIS_URL[:10])
        return False, None
    try:
        r = requests.post(
            UPSTASH_REDIS_URL,
            headers={'Authorization': 'Bearer %s' % UPSTASH_REDIS_TOKEN},
            json=cmd, timeout=timeout)
        if r.status_code != 200:
            print("[Cadence] Redis %s FAILED: HTTP %s %s"
                  % (cmd[0], r.status_code, r.text[:120]))
            return False, None
        return True, r.json().get('result')
    except Exception as e:
        print("[Cadence] Redis %s EXCEPTION: %s: %s"
              % (cmd[0], type(e).__name__, str(e)[:120]))
        return False, None


def _history_key(country):
    return 'cadence:%s:daily' % country


def read_history(country, limit=HISTORY_CAP):
    ok, res = _redis_cmd(['LRANGE', _history_key(country), '0', str(max(0, limit - 1))])
    if not ok or not res:
        return []
    out = []
    for item in res:
        try:
            out.append(json.loads(item))
        except Exception:
            continue
    return out


# ============================================================
# DAILY RECORD
# ============================================================
def _count_appearances(articles, terms):
    """Count ARTICLES mentioning the principal, not raw term hits -- one story
    syndicated twenty times is one appearance, not twenty."""
    n = 0
    for a in (articles or []):
        if not isinstance(a, dict):
            continue
        blob = _fold('%s %s' % (a.get('title') or '', a.get('description') or ''))
        if any(_fold(t) in blob for t in terms):
            n += 1
    return n


def record_scan(articles, country='cuba'):
    """Write today's appearance counts + corpus denominator.

    One record per UTC day; a same-day rerun REPLACES rather than appends, so a
    twice-daily scan cannot inflate the archive or double-count appearances.
    """
    profile = PROFILES.get(country) or CUBA_PROFILE
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    corpus_total = len(articles or [])
    corpus_probe_hits = _count_appearances(articles, profile['corpus_probe'])

    counts = {}
    for pid, p in profile['principals'].items():
        counts[pid] = _count_appearances(articles, p['terms'])

    record = {
        'date':          today,
        'recorded_at':   datetime.now(timezone.utc).isoformat(),
        'corpus_total':  corpus_total,
        'corpus_probe':  corpus_probe_hits,
        'appearances':   counts,
    }
    payload = json.dumps(record)

    head = read_history(country, limit=1)
    if head and (head[0] or {}).get('date') == today:
        ok, _ = _redis_cmd(['LSET', _history_key(country), '0', payload])
        action = 'REPLACED'
    else:
        ok, _ = _redis_cmd(['LPUSH', _history_key(country), payload])
        _redis_cmd(['LTRIM', _history_key(country), '0', str(HISTORY_CAP - 1)])
        action = 'WROTE'

    if ok:
        print('[Cadence] %s %s record (corpus %d, probe %d) -- %s'
              % (action, today, corpus_total, corpus_probe_hits,
                 ', '.join('%s:%d' % (k, v) for k, v in counts.items())))
    return {'success': bool(ok), 'action': action, 'date': today, 'record': record}


# ============================================================
# ANALYSIS
# ============================================================
def _corpus_health(history):
    """Today's corpus against the window median.

    THE guard. Without it a dead feed reads as a vanished leadership.
    """
    if len(history) < 2:
        return {'ready': False, 'ratio': None, 'healthy': True,
                'note': 'insufficient history to judge corpus health'}
    today = (history[0] or {}).get('corpus_probe') or 0
    prior = sorted((h or {}).get('corpus_probe') or 0
                   for h in history[1:BASELINE_WINDOW + 1])
    if not prior:
        return {'ready': False, 'ratio': None, 'healthy': True, 'note': 'no prior corpus'}
    mid = len(prior) // 2
    median = prior[mid] if len(prior) % 2 else (prior[mid - 1] + prior[mid]) / 2.0
    if median <= 0:
        return {'ready': False, 'ratio': None, 'healthy': True,
                'note': 'baseline corpus median is zero'}
    ratio = round(today / median, 2)
    healthy = ratio >= CORPUS_HEALTH_FLOOR
    return {
        'ready': True, 'ratio': ratio, 'healthy': healthy,
        'today': today, 'median': median, 'floor': CORPUS_HEALTH_FLOOR,
        'note': ('corpus at %.0f%% of baseline -- absence calls %s'
                 % (ratio * 100, 'active' if healthy else 'SUPPRESSED (feed outage suspected)')),
    }


def _principal_cadence(history, pid, pdef):
    """Learned norm + current gap for one principal."""
    seen_days, gap_days, days_since = [], [], None
    run = 0
    for i, h in enumerate(history):
        c = ((h or {}).get('appearances') or {}).get(pid, 0)
        if c > 0:
            if days_since is None:
                days_since = i
            seen_days.append(i)
            if run > 0:
                gap_days.append(run)
            run = 0
        else:
            run += 1
    if days_since is None:
        days_since = len(history)

    appearances = len(seen_days)
    if gap_days:
        gap_days.sort()
        m = len(gap_days) // 2
        typical_gap = gap_days[m] if len(gap_days) % 2 else (gap_days[m - 1] + gap_days[m]) / 2.0
        longest_gap = max(gap_days)
    else:
        typical_gap, longest_gap = None, None

    window = min(len(history), BASELINE_WINDOW)
    rate = round(appearances / window, 2) if window else 0

    return {
        'id': pid, 'name': pdef['name'], 'role': pdef['role'],
        'appearances_in_window': appearances,
        'window_days': window,
        'appearance_rate': rate,
        'typical_gap_days': typical_gap,
        'longest_observed_gap': longest_gap,
        'days_since_last_seen': days_since,
        'sensitivity': pdef.get('sensitivity', 1.0),
    }


def _band_absence(c, corpus_ok):
    """Band the gap against the principal's OWN learned norm."""
    if not corpus_ok:
        return 'suppressed', ('Corpus health below floor -- absence not assessed. '
                              'A quiet feed is not a quiet principal.')
    typical = c['typical_gap_days']
    days = c['days_since_last_seen']
    if typical is None:
        if c['appearances_in_window'] == 0:
            return 'never_seen', ('No appearance recorded in the observed window; no norm '
                                  'has been established, so no deviation can be claimed.')
        return 'normal', 'Appearing without an established gap pattern.'

    baseline = max(typical, 1.0) / max(c['sensitivity'], 0.1)
    ratio = days / baseline if baseline else 0

    if ratio >= 3.0:
        return 'acute', ('%d days since last appearance against a learned norm of about '
                         '%.0f -- roughly %.1fx the observed gap.' % (days, typical, ratio))
    if ratio >= 2.0:
        return 'anomalous', ('%d days since last appearance against a norm of about %.0f '
                             '(%.1fx).' % (days, typical, ratio))
    if ratio >= 1.5:
        return 'notable', ('%d days since last appearance; norm is about %.0f (%.1fx).'
                           % (days, typical, ratio))
    return 'normal', ('%d days since last appearance, within the observed norm of about '
                      '%.0f.' % (days, typical))


def compute_cadence(country='cuba'):
    """Full cadence read. Absence-honest until the baseline is ready."""
    profile = PROFILES.get(country) or CUBA_PROFILE
    history = read_history(country)

    if len(history) < MIN_DAYS_READY:
        return {
            'module': 'principal_cadence', 'version': __version__,
            'country': country, 'ready': False,
            'days_banked': len(history), 'days_required': MIN_DAYS_READY,
            'band': 'accumulating',
            'principals': [],
            'prose': ('%s principal-cadence baseline accumulating: %d of %d days banked. '
                      'No appearance norm can be asserted yet, so no absence is claimed. '
                      'Cadence history accrues in wall-clock time and cannot be backfilled.'
                      % (profile['display'], len(history), MIN_DAYS_READY)),
            'disclaimer': ('This is a CONVERGENCE indicator, NOT a probability of action.'),
        }

    health = _corpus_health(history)
    corpus_ok = health.get('healthy', True)

    results, worst = [], 'normal'
    order = {'normal': 0, 'never_seen': 0, 'suppressed': 0,
             'notable': 1, 'anomalous': 2, 'acute': 3}
    for pid, pdef in profile['principals'].items():
        c = _principal_cadence(history, pid, pdef)
        band, note = _band_absence(c, corpus_ok)
        c['band'] = band
        c['assessment'] = note
        results.append(c)
        if order.get(band, 0) > order.get(worst, 0):
            worst = band

    results.sort(key=lambda r: -order.get(r['band'], 0))
    flagged = [r for r in results if r['band'] in ('notable', 'anomalous', 'acute')]

    # Caught by the build test: with an unhealthy corpus every principal banded
    # 'suppressed', but the top-level band still resolved to 'normal' -- a
    # consumer reading only that field would see reassurance during a feed
    # outage, which is the precise failure this module exists to prevent.
    # An outage is not normality; say so at the top level too.
    if not corpus_ok:
        worst = 'suppressed'

    return {
        'module': 'principal_cadence', 'version': __version__,
        'country': country, 'ready': True,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'days_banked': len(history),
        'corpus_health': health,
        'band': worst,
        'flagged_count': len(flagged),
        'principals': results,
        'prose': _prose(profile, results, flagged, health, corpus_ok),
        'disclaimer': ('This is a CONVERGENCE indicator, NOT a probability of action. '
                       'A cadence break states that a principal has not appeared against '
                       'a learned norm. It does not assert why, nor what follows.'),
        'methodology': ('Per-principal learned baselines over a %d-day rolling window; a '
                        'fixed threshold would be meaningless across principals whose '
                        'normal visibility differs by an order of magnitude. Absence calls '
                        'are gated on corpus health so a feed outage cannot masquerade as '
                        'a disappearance.' % BASELINE_WINDOW),
    }


def _prose(profile, results, flagged, health, corpus_ok):
    disp = profile['display']
    if not corpus_ok:
        return ('%s principal-cadence: absence assessment SUSPENDED this cycle -- %s. '
                'The corpus is too thin to distinguish a quiet leadership from a quiet '
                'feed, and the honest reading is that we cannot tell.'
                % (disp, health.get('note', 'corpus health below floor')))
    if not flagged:
        return ('%s principal-cadence: all tracked principals appearing within their own '
                'observed norms. Baselines are per-principal -- long gaps are normal for '
                'semi-retired figures and would be loud for the sitting president.' % disp)

    lead = flagged[0]
    parts = ['%s principal-cadence: %d principal%s outside observed norms.'
             % (disp, len(flagged), '' if len(flagged) == 1 else 's')]
    for r in flagged[:3]:
        parts.append('%s (%s) -- %s %s' % (r['name'], r['role'], r['band'].upper(),
                                           r['assessment']))
    if lead['band'] in ('anomalous', 'acute'):
        parts.append('Unusual quiet from a principal whose own record shows a denser '
                     'cadence is the pattern that has historically preceded announced '
                     'transitions rather than followed them -- in Cuba 2006 the absence '
                     'came first and the announcement afterwards. Convergence, not '
                     'prediction: this states that the appearance record has broken, '
                     'not why.')
    return ' '.join(parts)


# ============================================================
# SELF-TEST
# ============================================================
if __name__ == '__main__':
    print('Principal Cadence Engine v%s -- self-test\n' % __version__)

    def synth(days, raul_every=14, dc_every=1, corpus=40, corpus_from=None,
              raul_stops_at=None):
        """Build newest-first history."""
        hist = []
        for i in range(days):
            c = corpus if (corpus_from is None or i >= corpus_from) else 3
            app = {'raul_castro': 0, 'diaz_canel': 0, 'marrero': 0, 'lopez_callejas': 0}
            if raul_stops_at is None or i >= raul_stops_at:
                if i % raul_every == 0:
                    app['raul_castro'] = 1
            if i % dc_every == 0:
                app['diaz_canel'] = 2
            hist.append({'date': (datetime.now(timezone.utc) - timedelta(days=i)).strftime('%Y-%m-%d'),
                         'corpus_total': c, 'corpus_probe': c, 'appearances': app})
        return hist

    import types as _t
    mod = _t.SimpleNamespace()

    print('TEST 1 -- baseline not yet ready')
    globals()['read_history'] = lambda country, limit=HISTORY_CAP: synth(4)
    r = compute_cadence('cuba')
    print('  ready:', r['ready'], '| band:', r['band'])
    print(' ', r['prose'][:130], '...')
    assert r['ready'] is False
    print('  OK -- refuses to characterise on thin history\n')

    print('TEST 2 -- healthy corpus, everyone within their own norm')
    globals()['read_history'] = lambda country, limit=HISTORY_CAP: synth(40)
    r = compute_cadence('cuba')
    print('  band:', r['band'], '| flagged:', r['flagged_count'])
    raul = [p for p in r['principals'] if p['id'] == 'raul_castro'][0]
    print('  Raul: rate %.2f/day, typical gap %s d, %d d since seen -> %s'
          % (raul['appearance_rate'], raul['typical_gap_days'],
             raul['days_since_last_seen'], raul['band']))
    assert r['flagged_count'] == 0
    print('  OK -- sparse-but-normal Raul is NOT flagged\n')

    print('TEST 3 -- Raul stops appearing (the scenario)')
    # History is NEWEST-FIRST, so "appears only where i >= 14" means he was
    # showing up on a 7-day cadence until a fortnight ago and has not since.
    globals()['read_history'] = lambda country, limit=HISTORY_CAP: synth(
        40, raul_every=7, raul_stops_at=14)
    r = compute_cadence('cuba')
    raul = [p for p in r['principals'] if p['id'] == 'raul_castro'][0]
    print('  Raul band:', raul['band'], '|', raul['assessment'])
    print('  overall band:', r['band'], '| flagged:', r['flagged_count'])
    assert raul['band'] in ('anomalous', 'acute'), raul['band']
    print('  OK -- cadence break detected against his OWN learned norm\n')

    print('TEST 4 -- feed outage must NOT read as disappearance')
    globals()['read_history'] = lambda country, limit=HISTORY_CAP: synth(40, corpus_from=1)
    r = compute_cadence('cuba')
    print('  corpus health:', r['corpus_health']['note'])
    print('  band:', r['band'])
    bands = {p['band'] for p in r['principals']}
    assert r['band'] == 'suppressed' or bands == {'suppressed'}, bands
    print(' ', r['prose'][:150], '...')
    print('  OK -- outage reported as outage, not as a vanished leadership\n')

    print('ALL CADENCE TESTS PASSED')
