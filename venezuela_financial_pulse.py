"""
venezuela_financial_pulse.py -- Asifah Analytics WHA Backend -- v1.1.0 Jul 2026
Cloned from iran_financial_pulse.py (contract donor). Three tiles:
  IBC (^IBC, INVERTED inflation-hedge read) / USDVES (VES=X, INVERTED,
  official-indicative -- parallel rate runs wider) / BRENT (export benchmark).
Convergence: IBC 7d up + USD/VES 7d up = capital-flight pattern.
Redis: pulse:venezuela:financial (TTL 12h). BVC Mon-Fri 0930-1300 UTC-4.
Endpoint: GET /api/venezuela/financial-pulse (?force=true)

v1.1.0 (Jul 27 2026) -- Iran-remnant repair. The v1.0.0 clone carried five
undefined Tehran symbols (HIST_KEY_BRENT, CHROME_UA, HIST_KEY_TEDPIX,
HIST_KEY_IRR, TEDPIX_MIRRORS) and reported country='iran'; both public
endpoints returned HTTP 500. Also fixed: _append_history crashed on
float(None) whenever a source was unreachable, so one dead feed took the
whole endpoint down. Absence-honest now: a dead source yields a stale tile
with a last-known value and an explicit source_status, never an exception.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from flask import request, jsonify

VERSION = '1.1.0'
CACHE_KEY = 'pulse:venezuela:financial'
HIST_KEY_IBC = 'pulse:venezuela:hist:ibc'
HIST_KEY_VES = 'pulse:venezuela:hist:ves'
HIST_KEY_BRENT = 'pulse:venezuela:hist:brent'
CACHE_TTL_HOURS = 12
HIST_MAX_POINTS = 30

# Yahoo rejects generic agents intermittently; Chrome UA + host failover is
# the canonical platform pattern (query1 -> query2).
CHROME_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
             '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
YAHOO_HOSTS = ['https://query1.finance.yahoo.com',
               'https://query2.finance.yahoo.com']

# ------------------------------------------------------------
# Redis REST helpers (Upstash) -- both env-name conventions
# ------------------------------------------------------------
REDIS_URL = (os.environ.get('UPSTASH_REDIS_REST_URL')
             or os.environ.get('UPSTASH_REDIS_URL', '')).rstrip('/')
REDIS_TOKEN = (os.environ.get('UPSTASH_REDIS_REST_TOKEN')
               or os.environ.get('UPSTASH_REDIS_TOKEN', ''))

_memory_cache = {}


def _redis_get(key):
    if not REDIS_URL or not REDIS_TOKEN:
        return _memory_cache.get(key)
    try:
        r = requests.get(f'{REDIS_URL}/get/{key}',
                         headers={'Authorization': f'Bearer {REDIS_TOKEN}'},
                         timeout=(5, 10))
        if r.status_code == 200:
            raw = r.json().get('result')
            if raw:
                return json.loads(raw)
            return None
    except Exception as e:
        print(f'[VZ Pulse] Redis GET failed ({e}); memory fallback')
    return _memory_cache.get(key)


def _redis_set(key, value):
    _memory_cache[key] = value
    if not REDIS_URL or not REDIS_TOKEN:
        return
    try:
        requests.post(REDIS_URL,
                      headers={'Authorization': f'Bearer {REDIS_TOKEN}'},
                      json=['SET', key, json.dumps(value)],
                      timeout=(5, 10))
    except Exception as e:
        print(f'[VZ Pulse] Redis SET failed ({e}); memory only')


# ------------------------------------------------------------
# Own-history sparklines (NGX donor pattern): scraped sources have
# no historical series, so we accumulate one scan at a time.
# Entries: {'date': 'YYYY-MM-DD', 'value': float}. One per day.
#
# ABSENCE-HONEST: a failed fetch appends NOTHING. We never zero-fill and
# never carry a fabricated point forward -- the series simply does not
# advance that day, and the tile is flagged stale.
# ------------------------------------------------------------
def _append_history(hist_key, value):
    hist = _redis_get(hist_key) or []
    if not isinstance(hist, list):
        hist = []
    if value is None:
        return hist
    try:
        value = float(value)
    except (TypeError, ValueError):
        return hist
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    hist = [h for h in hist
            if isinstance(h, dict) and h.get('date') != today
            and isinstance(h.get('value'), (int, float))]
    hist.append({'date': today, 'value': value})
    hist = sorted(hist, key=lambda h: h['date'])[-HIST_MAX_POINTS:]
    _redis_set(hist_key, hist)
    return hist


def _hist_change_pct(hist, days_back=1):
    """% change between latest point and the point days_back earlier
    (by position, since scans are ~daily). None if not enough data."""
    if not hist or len(hist) < days_back + 1:
        return None
    latest = hist[-1]['value']
    prior = hist[-1 - days_back]['value']
    if not prior:
        return None
    return round((latest - prior) / prior * 100, 2)


def _last_known(hist):
    """Most recent accumulated value, or None if the series is empty."""
    return hist[-1]['value'] if hist else None


# ------------------------------------------------------------
# Tier logic (canonical thresholds)
# ------------------------------------------------------------
def _tier_standard(chg):
    if chg is None:
        return 'stable'
    if chg <= -2:
        return 'stress'
    if chg <= -1:
        return 'warning'
    if chg >= 2:
        return 'rally'
    return 'stable'


def _tier_inverted(chg):
    """USD/VES and IBC: RISING = weaker bolivar / hedging flight = stress."""
    if chg is None:
        return 'stable'
    if chg >= 2:
        return 'stress'
    if chg >= 1:
        return 'warning'
    if chg <= -2:
        return 'rally'
    return 'stable'


# ------------------------------------------------------------
# Fetchers
# ------------------------------------------------------------
def _fetch_yahoo_quote(symbol, label):
    """Last close via Yahoo chart API. {'value','source'} or None."""
    for host in YAHOO_HOSTS:
        try:
            r = requests.get(f'{host}/v8/finance/chart/{symbol}',
                             params={'range': '5d', 'interval': '1d'},
                             headers={'User-Agent': CHROME_UA},
                             timeout=(5, 15))
            if r.status_code != 200:
                continue
            res = (r.json().get('chart', {}).get('result') or [None])[0]
            if not res:
                continue
            quote = ((res.get('indicators') or {}).get('quote') or [{}])[0]
            closes = [c for c in (quote.get('close') or []) if c is not None]
            if closes:
                print(f'[VZ Pulse] {label} {closes[-1]:,.2f} via {host}')
                return {'value': float(closes[-1]), 'source': f'Yahoo ({symbol})'}
        except Exception as e:
            print(f'[VZ Pulse] {label} fetch failed on {host}: {e}')
    print(f'[VZ Pulse] {label} unreachable on all hosts')
    return None


def _fetch_ibc():
    return _fetch_yahoo_quote('%5EIBC', 'IBC')


def _fetch_ves():
    return _fetch_yahoo_quote('VES%3DX', 'USDVES')


def _fetch_brent():
    """Brent has a real Yahoo history, so it carries its own 22-point
    sparkline and true 24h change rather than accumulated own-history."""
    for host in YAHOO_HOSTS:
        try:
            url = f'{host}/v8/finance/chart/BZ%3DF?range=1mo&interval=1d'
            r = requests.get(url, headers={'User-Agent': CHROME_UA},
                             timeout=(5, 15))
            if r.status_code != 200:
                continue
            result = (r.json().get('chart') or {}).get('result')
            if not result:
                continue
            res = result[0]
            meta = res.get('meta') or {}
            quote = ((res.get('indicators') or {}).get('quote') or [{}])[0]
            closes = [c for c in (quote.get('close') or []) if c is not None]
            if not closes:
                continue
            price = meta.get('regularMarketPrice')
            if price is None:
                price = closes[-1]
            if len(closes) >= 2:
                # 0.05% relative tolerance (float-noise lesson, Jun 12)
                if abs(price - closes[-1]) <= abs(price) * 0.0005:
                    prev = closes[-2]
                else:
                    prev = closes[-1]
            else:
                prev = price
            chg = round((price - prev) / prev * 100, 2) if prev else 0.0
            return {'value': round(float(price), 2),
                    'change_pct_24h': chg,
                    'sparkline': [round(float(c), 2) for c in closes[-22:]],
                    'source': 'Yahoo Finance (BZ=F)'}
        except Exception as e:
            print(f'[VZ Pulse] Brent {host} failed: {e}')
            continue
    print('[VZ Pulse] Brent unreachable on all hosts')
    return None


# ------------------------------------------------------------
# Market status -- Bolsa de Valores de Caracas trades Mon-Fri,
# 09:30-13:00 Caracas time (UTC-4, no DST).
# ------------------------------------------------------------
def _bvc_market_status():
    now = datetime.now(timezone.utc) - timedelta(hours=4)
    if now.weekday() >= 5:
        return 'closed'
    mins = now.hour * 60 + now.minute
    return 'open' if (9 * 60 + 30) <= mins <= (13 * 60) else 'closed'


def _build_financial_pulse():
    ibc, ves, brent = _fetch_ibc(), _fetch_ves(), _fetch_brent()

    ibc_hist = _append_history(HIST_KEY_IBC, (ibc or {}).get('value'))
    ves_hist = _append_history(HIST_KEY_VES, (ves or {}).get('value'))
    brent_hist = _append_history(HIST_KEY_BRENT, (brent or {}).get('value'))

    # Live value when the fetch succeeded; last-known accumulated point when
    # it did not. Either way the tile carries an explicit `stale` flag.
    ibc_val = (ibc or {}).get('value') or _last_known(ibc_hist)
    ves_val = (ves or {}).get('value') or _last_known(ves_hist)
    brent_val = (brent or {}).get('value') or _last_known(brent_hist)

    ibc_chg = _hist_change_pct(ibc_hist)
    ves_chg = _hist_change_pct(ves_hist)
    # Brent carries a true 24h change from Yahoo when live.
    brent_chg = (brent or {}).get('change_pct_24h')
    if brent_chg is None:
        brent_chg = _hist_change_pct(brent_hist)

    ibc_7d, ves_7d = _hist_change_pct(ibc_hist, 7), _hist_change_pct(ves_hist, 7)

    brent_spark = ((brent or {}).get('sparkline')
                   or [h['value'] for h in brent_hist])

    tiles = {
        'IBC': {'name': 'IBC', 'ticker': 'Caracas All-Share', 'value': ibc_val,
                'change_pct_24h': ibc_chg, 'tier': _tier_inverted(ibc_chg),
                'source': (ibc or {}).get('source', 'last-known (Yahoo unreachable)'),
                'sparkline': [h['value'] for h in ibc_hist],
                'note': 'Bolivar-denominated inflation hedge -- INVERTED read: rising IBC '
                        'alongside a weakening bolivar signals capital flight, not confidence.',
                'stale': ibc is None},
        'USDVES': {'name': 'USD/VES', 'ticker': 'indicative rate', 'value': ves_val,
                'change_pct_24h': ves_chg, 'tier': _tier_inverted(ves_chg),
                'source': (ves or {}).get('source', 'last-known (Yahoo unreachable)'),
                'sparkline': [h['value'] for h in ves_hist],
                'note': 'Rising = bolivar weakening. Official-indicative rate; the parallel '
                        'rate typically runs wider -- directional, not precise.',
                'stale': ves is None},
        'BRENT': {'name': 'Brent', 'ticker': 'BZ=F', 'value': brent_val,
                'change_pct_24h': brent_chg, 'tier': _tier_standard(brent_chg),
                'source': (brent or {}).get('source', 'last-known (Yahoo unreachable)'),
                'sparkline': brent_spark,
                'note': "Venezuela's export benchmark -- Orinoco heavy crude sells at "
                        'discounts off Brent-linked formulas. Oil is the fiscal spine.',
                'stale': brent is None},
    }

    # Per-source status so a reader (and the GPI) can tell a quiet market
    # from a dead feed. Absence-honest: the gap is surfaced, not smoothed.
    source_status = {
        'ibc': 'live' if ibc else 'unreachable',
        'usdves': 'live' if ves else 'unreachable',
        'brent': 'live' if brent else 'unreachable',
    }
    live_count = sum(1 for v in source_status.values() if v == 'live')

    conv = bool(ibc_7d and ves_7d and ibc_7d > 0 and ves_7d > 0)
    convergence = {'active': conv, 'ibc_7d_pct': ibc_7d, 'ves_7d_pct': ves_7d,
        'note': ('IBC rising alongside bolivar depreciation is consistent with capital-flight '
                 'hedging into equities rather than market confidence -- the pattern that has '
                 'historically accompanied Venezuelan currency stress.') if conv else
                ('No capital-flight convergence detected this cycle (requires both IBC and '
                 'USD/VES 7-day trends rising). History accumulates one point per scan.')}

    return {'market_status': _bvc_market_status(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'tiles': tiles,
            'source_status': source_status,
            'sources_live': live_count,
            'degraded': live_count < 3,
            'capital_flight_convergence': convergence}


def _is_fresh(payload):
    try:
        ts = payload.get('financial_pulse', {}).get('updated_at', '')
        then = datetime.fromisoformat(ts)
        return (datetime.now(timezone.utc) - then).total_seconds() / 3600 < CACHE_TTL_HOURS
    except Exception:
        return False


# ------------------------------------------------------------
# Flask endpoint registration
# ------------------------------------------------------------
def register_venezuela_financial_pulse_endpoints(app):

    @app.route('/api/venezuela/financial-pulse', methods=['GET', 'OPTIONS'])
    def api_venezuela_financial_pulse():
        if request.method == 'OPTIONS':
            return '', 200
        force = request.args.get('force', 'false').lower() == 'true'
        if not force:
            cached = _redis_get(CACHE_KEY)
            if cached and _is_fresh(cached):
                cached['cached'] = True
                return jsonify(cached)
        try:
            pulse = _build_financial_pulse()
        except Exception as e:
            print(f'[VZ Pulse] build failed -- {type(e).__name__}: {e}')
            pulse = None

        if pulse:
            payload = {'success': True, 'country': 'venezuela',
                       'financial_pulse': pulse,
                       'last_updated': pulse['updated_at'],
                       'cached': False, 'version': VERSION}
            # Only overwrite the cache when at least one source answered --
            # never let a total outage erase a good snapshot.
            if pulse.get('sources_live', 0) > 0:
                _redis_set(CACHE_KEY, payload)
            return jsonify(payload)

        cached = _redis_get(CACHE_KEY)
        if cached:
            cached['cached'] = True
            cached['stale'] = True
            return jsonify(cached)
        return jsonify({'success': False, 'country': 'venezuela',
                        'error': 'Financial pulse unavailable (all sources '
                                 'unreachable, no cache)',
                        'version': VERSION}), 503

    @app.route('/api/venezuela/financial-pulse/debug', methods=['GET', 'OPTIONS'])
    def api_venezuela_financial_pulse_debug():
        if request.method == 'OPTIONS':
            return '', 200
        cached = _redis_get(CACHE_KEY)
        ibc_hist = _redis_get(HIST_KEY_IBC) or []
        ves_hist = _redis_get(HIST_KEY_VES) or []
        brent_hist = _redis_get(HIST_KEY_BRENT) or []
        pulse = (cached or {}).get('financial_pulse') or {}
        return jsonify({
            'module': 'venezuela_financial_pulse',
            'version': VERSION,
            'redis_configured': bool(REDIS_URL and REDIS_TOKEN),
            'cache_present': bool(cached),
            'cache_fresh': _is_fresh(cached) if cached else False,
            'tiles_cached': list(pulse.get('tiles', {}).keys()),
            'source_status_cached': pulse.get('source_status'),
            'ibc_history_points': len(ibc_hist),
            'ves_history_points': len(ves_hist),
            'brent_history_points': len(brent_hist),
            'yahoo_hosts': YAHOO_HOSTS,
            'bvc_market_status_now': _bvc_market_status(),
        })

    print(f'[VZ Pulse] Endpoints registered (v{VERSION})')
