"""
mexico_stability.py -- Mexico Financial Pulse module (WHA backend)
v1.0.0 -- June 12, 2026

Powers the Financial Pulse card on mexico-stability.html.
Clones the canonical financial_pulse contract established by the Russia
(Europe backend) and Nigeria (Africa backend) pulse cards:

    financial_pulse: {
        market_status: 'open' | 'closed',
        updated_at:    ISO timestamp,
        tiles: {
            KEY: { name, ticker, value, change_pct_24h, tier,
                   source, sparkline[], note }
        }
    }

Three tiles, all Yahoo Finance (query1 -> query2 host failover with
Chrome User-Agent, per platform canon established on the US NYSE card):

    IPC     -- ^MXX   S&P/BMV IPC, the Bolsa Mexicana benchmark.
               Standard polarity: drawdown = stress.
    MXNUSD  -- MXN=X  USD/MXN exchange rate.
               INVERTED polarity: rising = weaker peso = stress.
    WTI     -- CL=F   WTI crude. Mexican export crude prices off
               WTI-linked formulas, so this is the Pemex
               state-oil-revenue proxy (the way Brent is Nigeria's).

Caching: Redis-first with 12-hour TTL, lazy refresh on request
(no background thread, no cross-worker lock needed -- the refresh is
three fast Yahoo calls and only the requesting worker performs it).
?force=true bypasses cache. In-memory fallback when Redis unavailable.

Endpoints:
    GET /api/mexico/stability            -- cache-first pulse payload
    GET /api/mexico/stability?force=true -- force fresh Yahoo pull
    GET /api/mexico/stability/debug      -- cache + env diagnostics
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from flask import request, jsonify

VERSION = '1.0.0'
CACHE_KEY = 'stability:mexico:financial_pulse'
CACHE_TTL_HOURS = 12

# ------------------------------------------------------------
# Redis REST helpers (Upstash) -- both env-name conventions
# supported per platform canon (REST_URL vs URL).
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
        r = requests.get(
            f'{REDIS_URL}/get/{key}',
            headers={'Authorization': f'Bearer {REDIS_TOKEN}'},
            timeout=(5, 10),
        )
        if r.status_code == 200:
            raw = r.json().get('result')
            if raw:
                return json.loads(raw)
    except Exception as e:
        print(f'[Mexico Pulse] Redis GET failed ({e}); memory fallback')
        return _memory_cache.get(key)
    return None


def _redis_set(key, value):
    _memory_cache[key] = value
    if not REDIS_URL or not REDIS_TOKEN:
        return
    try:
        requests.post(
            REDIS_URL,
            headers={'Authorization': f'Bearer {REDIS_TOKEN}'},
            json=['SET', key, json.dumps(value)],
            timeout=(5, 10),
        )
    except Exception as e:
        print(f'[Mexico Pulse] Redis SET failed ({e}); memory only')


# ------------------------------------------------------------
# Yahoo Finance chart fetch -- canonical pattern:
# query1 -> query2 host failover + Chrome User-Agent.
# ------------------------------------------------------------
YAHOO_HOSTS = [
    'https://query1.finance.yahoo.com',
    'https://query2.finance.yahoo.com',
]
CHROME_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
             'AppleWebKit/537.36 (KHTML, like Gecko) '
             'Chrome/124.0.0.0 Safari/537.36')


def _fetch_yahoo_chart(ticker):
    """
    Returns {'price', 'change_pct', 'sparkline'} or None.
    Pulls 1 month of daily closes; sparkline is the close series.
    24h change logic: if the live regularMarketPrice equals the final
    bar (market closed), compare last two completed closes; if it
    differs (intraday), compare live price vs the last completed close.
    """
    encoded = requests.utils.quote(ticker, safe='')
    for host in YAHOO_HOSTS:
        try:
            url = (f'{host}/v8/finance/chart/{encoded}'
                   f'?range=1mo&interval=1d')
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
                # 0.05% relative tolerance: Yahoo's live price and close
                # array differ by float noise, so exact equality never
                # matched and every tile reported +0.00%.
                if abs(price - closes[-1]) <= abs(price) * 0.0005:
                    prev = closes[-2]   # same bar; compare prior session
                else:
                    prev = closes[-1]   # intraday; compare vs last close
            else:
                prev = price

            change_pct = 0.0
            if prev:
                change_pct = round((price - prev) / prev * 100, 2)

            return {
                'price': round(float(price), 4),
                'change_pct': change_pct,
                'sparkline': [round(float(c), 2) for c in closes[-22:]],
            }
        except Exception as e:
            print(f'[Mexico Pulse] Yahoo {host} failed for {ticker}: {e}')
            continue
    return None


# ------------------------------------------------------------
# Tier logic -- canonical thresholds from the US NYSE card.
# ------------------------------------------------------------
def _tier_standard(chg):
    """Equity/commodity polarity: drawdown = stress."""
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
    """FX polarity for USD/MXN: RISING = weaker peso = stress."""
    if chg is None:
        return 'stable'
    if chg >= 2:
        return 'stress'
    if chg >= 1:
        return 'warning'
    if chg <= -2:
        return 'rally'
    return 'stable'


def _bmv_market_status():
    """
    BMV trading hours: 08:30-15:00 Mexico City, Mon-Fri.
    Mexico abolished DST in 2022, so Mexico City is UTC-6 year-round.
    """
    now_mx = datetime.now(timezone.utc) + timedelta(hours=-6)
    if now_mx.weekday() >= 5:
        return 'closed'
    minutes = now_mx.hour * 60 + now_mx.minute
    if 8 * 60 + 30 <= minutes < 15 * 60:
        return 'open'
    return 'closed'


# ------------------------------------------------------------
# Pulse builder
# ------------------------------------------------------------
def _build_financial_pulse():
    ipc = _fetch_yahoo_chart('^MXX')
    mxn = _fetch_yahoo_chart('MXN=X')
    wti = _fetch_yahoo_chart('CL=F')

    tiles = {}

    if ipc:
        tiles['IPC'] = {
            'name': 'S&P/BMV IPC',
            'ticker': '^MXX',
            'value': ipc['price'],
            'change_pct_24h': ipc['change_pct'],
            'tier': _tier_standard(ipc['change_pct']),
            'source': 'Yahoo Finance',
            'sparkline': ipc['sparkline'],
            'note': 'Domestic equity sentiment -- Bolsa Mexicana benchmark',
        }

    if mxn:
        tiles['MXNUSD'] = {
            'name': 'USD/MXN',
            'ticker': 'MXN=X',
            'value': mxn['price'],
            'change_pct_24h': mxn['change_pct'],
            'tier': _tier_inverted(mxn['change_pct']),
            'source': 'Yahoo Finance',
            'sparkline': mxn['sparkline'],
            'note': 'INVERTED polarity: rising = weaker peso',
        }

    if wti:
        tiles['WTI'] = {
            'name': 'WTI Crude',
            'ticker': 'CL=F',
            'value': wti['price'],
            'change_pct_24h': wti['change_pct'],
            'tier': _tier_standard(wti['change_pct']),
            'source': 'Yahoo Finance (NYMEX WTI)',
            'sparkline': wti['sparkline'],
            'note': 'Pemex state-oil-revenue baseline (Mexican crude '
                    'prices off WTI-linked formulas)',
        }

    if not tiles:
        return None

    return {
        'market_status': _bmv_market_status(),
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'tiles': tiles,
    }


def _is_fresh(payload):
    try:
        ts = payload.get('financial_pulse', {}).get('updated_at', '')
        then = datetime.fromisoformat(ts)
        age_hours = (datetime.now(timezone.utc) - then).total_seconds() / 3600
        return age_hours < CACHE_TTL_HOURS
    except Exception:
        return False


# ------------------------------------------------------------
# Flask endpoint registration
# ------------------------------------------------------------
def register_mexico_stability_endpoints(app):

    @app.route('/api/mexico/stability', methods=['GET', 'OPTIONS'])
    def api_mexico_stability():
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
            payload = {
                'success': True,
                'country': 'mexico',
                'financial_pulse': pulse,
                'last_updated': pulse['updated_at'],
                'cached': False,
                'version': VERSION,
            }
            _redis_set(CACHE_KEY, payload)
            return jsonify(payload)

        # Yahoo entirely down -- serve stale cache honestly if we have one
        cached = _redis_get(CACHE_KEY)
        if cached:
            cached['cached'] = True
            cached['stale'] = True
            return jsonify(cached)

        return jsonify({
            'success': False,
            'country': 'mexico',
            'error': 'Financial pulse unavailable (Yahoo unreachable, '
                     'no cache)',
            'version': VERSION,
        }), 503

    @app.route('/api/mexico/stability/debug', methods=['GET'])
    def api_mexico_stability_debug():
        cached = _redis_get(CACHE_KEY)
        return jsonify({
            'module': 'mexico_stability',
            'version': VERSION,
            'redis_configured': bool(REDIS_URL and REDIS_TOKEN),
            'cache_key': CACHE_KEY,
            'cache_present': bool(cached),
            'cache_fresh': _is_fresh(cached) if cached else False,
            'cache_updated_at': (cached or {}).get('last_updated', None),
            'tiles_cached': list(((cached or {}).get('financial_pulse')
                                  or {}).get('tiles', {}).keys()),
        })

    print(f'[Mexico Pulse] Endpoints registered (v{VERSION})')
