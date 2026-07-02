"""
venezuela_financial_pulse.py -- Asifah Analytics WHA Backend -- v1.0.0 Jul 2026
Cloned from iran_financial_pulse.py (contract donor). Three tiles:
  IBC (^IBC, INVERTED inflation-hedge read) / USDVES (VES=X, INVERTED,
  official-indicative -- parallel rate runs wider) / BRENT (export benchmark).
Convergence: IBC 7d up + USD/VES 7d up = capital-flight pattern.
Redis: pulse:venezuela:financial (TTL 14h > 12h refresh). BVC Mon-Fri 0930-1300 UTC-4.
Endpoint: GET /api/venezuela/financial-pulse (?force=true)
"""

import os
import re
import json
import requests
from datetime import datetime, timezone, timedelta
from flask import request, jsonify

VERSION = '1.0.0'
CACHE_KEY = 'pulse:venezuela:financial'
HIST_KEY_IBC = 'pulse:venezuela:hist:ibc'
HIST_KEY_VES = 'pulse:venezuela:hist:ves'
CACHE_TTL_HOURS = 12
HIST_MAX_POINTS = 30

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
    except Exception as e:
        print(f'[VZ Pulse] Redis GET failed ({e}); memory fallback')
        return _memory_cache.get(key)
    return None


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
# ------------------------------------------------------------
def _append_history(hist_key, value):
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    hist = _redis_get(hist_key) or []
    if not isinstance(hist, list):
        hist = []
    hist = [h for h in hist if h.get('date') != today]
    hist.append({'date': today, 'value': float(value)})
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
    """USD/IRR: RISING = weaker rial = stress."""
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
def _fetch_yahoo_quote(symbol, label):
    """Last close via Yahoo chart API. {'value','source'} or None."""
    for host in YAHOO_HOSTS:
        try:
            r = requests.get(f'{host}/v8/finance/chart/{symbol}',
                             params={'range': '5d', 'interval': '1d'},
                             headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r.status_code != 200:
                continue
            res = (r.json().get('chart', {}).get('result') or [None])[0]
            if not res:
                continue
            closes = [c for c in (res.get('indicators', {}).get('quote') or [{}])[0].get('close', []) if c]
            if closes:
                print(f'[VZ Pulse] {label} {closes[-1]:,.2f} via {host}')
                return {'value': float(closes[-1]), 'source': f'Yahoo ({symbol})'}
        except Exception as e:
            print(f'[VZ Pulse] {label} fetch failed on {host}: {e}')
    return None

def _fetch_ibc():
    return _fetch_yahoo_quote('%5EIBC', 'IBC')

def _fetch_ves():
    return _fetch_yahoo_quote('VES%3DX', 'USDVES')

YAHOO_HOSTS = ['https://query1.finance.yahoo.com',
               'https://query2.finance.yahoo.com']


def _fetch_brent():
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
    return None


# ------------------------------------------------------------
# Market status -- Tehran Stock Exchange trades the IRANIAN week:
# Saturday-Wednesday, 09:00-12:30 Tehran (UTC+3:30, no DST since 2022).
# ------------------------------------------------------------
def _bvc_market_status():
    now = datetime.now(timezone.utc) - timedelta(hours=4)
    if now.weekday() >= 5:
        return 'closed'
    mins = now.hour * 60 + now.minute
    return 'open' if (9 * 60 + 30) <= mins <= (13 * 60) else 'closed'

def _build_financial_pulse():
    ibc, ves, brent = _fetch_ibc(), _fetch_ves(), _fetch_brent()
    ibc_hist   = _append_history(HIST_KEY_IBC,   (ibc or {}).get('value'))
    ves_hist   = _append_history(HIST_KEY_VES,   (ves or {}).get('value'))
    brent_hist = _append_history(HIST_KEY_BRENT, (brent or {}).get('value'))
    ibc_val, ves_val, brent_val = ((x or {}).get('value') for x in (ibc, ves, brent))
    ibc_chg, ves_chg, brent_chg = (_hist_change_pct(h) for h in (ibc_hist, ves_hist, brent_hist))
    ibc_7d, ves_7d = _hist_change_pct(ibc_hist, 7), _hist_change_pct(ves_hist, 7)
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
                'sparkline': [h['value'] for h in brent_hist],
                'note': "Venezuela's export benchmark -- Orinoco heavy crude sells at "
                        'discounts off Brent-linked formulas. Oil is the fiscal spine.',
                'stale': brent is None},
    }
    conv = bool(ibc_7d and ves_7d and ibc_7d > 0 and ves_7d > 0)
    convergence = {'active': conv, 'ibc_7d_pct': ibc_7d, 'ves_7d_pct': ves_7d,
        'note': ('IBC rising alongside bolivar depreciation is consistent with capital-flight '
                 'hedging into equities rather than market confidence -- the pattern that has '
                 'historically accompanied Venezuelan currency stress.') if conv else
                ('No capital-flight convergence detected this cycle (requires both IBC and '
                 'USD/VES 7-day trends rising). History accumulates one point per scan.')}
    return {'market_status': _bvc_market_status(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'tiles': tiles, 'capital_flight_convergence': convergence}

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
        pulse = _build_financial_pulse()
        if pulse:
            payload = {'success': True, 'country': 'iran',
                       'financial_pulse': pulse,
                       'last_updated': pulse['updated_at'],
                       'cached': False, 'version': VERSION}
            _redis_set(CACHE_KEY, payload)
            return jsonify(payload)
        cached = _redis_get(CACHE_KEY)
        if cached:
            cached['cached'] = True
            cached['stale'] = True
            return jsonify(cached)
        return jsonify({'success': False, 'country': 'iran',
                        'error': 'Financial pulse unavailable (all sources '
                                 'unreachable, no cache)',
                        'version': VERSION}), 503

    @app.route('/api/venezuela/financial-pulse/debug', methods=['GET'])
    def api_venezuela_financial_pulse_debug():
        cached = _redis_get(CACHE_KEY)
        ted_hist = _redis_get(HIST_KEY_TEDPIX) or []
        irr_hist = _redis_get(HIST_KEY_IRR) or []
        return jsonify({
            'module': 'venezuela_financial_pulse',
            'version': VERSION,
            'redis_configured': bool(REDIS_URL and REDIS_TOKEN),
            'cache_present': bool(cached),
            'cache_fresh': _is_fresh(cached) if cached else False,
            'tiles_cached': list(((cached or {}).get('financial_pulse')
                                  or {}).get('tiles', {}).keys()),
            'tedpix_history_points': len(ted_hist),
            'irr_history_points': len(irr_hist),
            'tedpix_mirrors': [m[0] for m in TEDPIX_MIRRORS],
            'tse_market_status_now': _bvc_market_status(),
        })

    print(f'[VZ Pulse] Endpoints registered (v{VERSION})')
