"""
wha_market_quotes.py -- Asifah Analytics -- WHA backend market quotes
v1.0.0 -- November 3, 2026

Market Watch had two Western Hemisphere cards (the US NYSE read and Mexico).
This module adds six, in the canonical Financial Pulse shape used by every
other card (tiles + market_status), so Market Watch and future stability pages
read one shape:

    argentina  Merval (^MERV)        USD/ARS (ARS=X)   Soybeans (ZS=F)
    brazil     Bovespa (^BVSP)       USD/BRL (BRL=X)   Soybeans (ZS=F)
    chile      S&P IPSA (^IPSA)      USD/CLP (CLP=X)   Copper (HG=F)
    colombia   MSCI Colombia (GXG)   USD/COP (COP=X)   Coffee (KC=F)
    peru       MSCI Peru (EPU)       USD/PEN (PEN=X)   Copper (HG=F)
    canada     S&P/TSX (^GSPTSE)     USD/CAD (CAD=X)   WTI (CL=F)

Colombia and Peru are read through US-listed country funds (GXG, EPU): their
local indices are thin on free feeds. The tile says so -- a substitute is
labelled, never disguised.

THE COMMODITY TILE IS THE COUNTRY'S EXPORT, so its polarity is STANDARD (a
rising price is good news for the exporter). Currencies are USD/XXX, so a
RISING number is a WEAKER local currency (polarity inverted).

Argentina's peso is a crawling, managed currency: it falls a little almost
every day by design. Its tile therefore uses a wider band (2.0%) so routine
crawl does not read as stress; a jump through the band is still flagged.

Server-side for the same reasons as asia_market_quotes.py (CORS, Yahoo's
User-Agent rules). Market closure is not a failure: the chart endpoint
returns the last close. A blank card means the FETCH failed.

CACHE: wha:market:<country> (6h). ?force goes through the WHA backend's public
force gate (one forced refetch per path per 15 minutes).
ENDPOINTS:
  GET /api/wha/market/<country>
  GET /debug/wha-market

COPYRIGHT (c) 2025-2026 Asifah Analytics. All rights reserved.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import quote as urlquote
from flask import jsonify, request

__version__ = '1.0.0'

CACHE_TTL = 6 * 3600
TIMEOUT = 12
BROWSER_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')


def _url_tok():
    return ((os.environ.get('UPSTASH_REDIS_URL') or os.environ.get('UPSTASH_REDIS_REST_URL') or '').rstrip('/'),
            os.environ.get('UPSTASH_REDIS_TOKEN') or os.environ.get('UPSTASH_REDIS_REST_TOKEN') or '')


def _redis_get(key):
    url, tok = _url_tok()
    if not (url and tok):
        return None
    try:
        r = requests.get(f'{url}/get/{key}', headers={'Authorization': f'Bearer {tok}'}, timeout=6)
        raw = r.json().get('result') if r.status_code == 200 else None
        return json.loads(raw) if raw else None
    except Exception:
        return None


def _redis_set(key, value, ttl=CACHE_TTL):
    url, tok = _url_tok()
    if not (url and tok):
        return False
    try:
        r = requests.post(url, headers={'Authorization': f'Bearer {tok}'},
                          json=['SET', key, json.dumps(value), 'EX', str(int(ttl))], timeout=8)
        return r.status_code == 200
    except Exception:
        return False


# ── instrument helpers ───────────────────────────────────────────────────
def _eq(key, name, symbol, unit, session, note, tile=None, substitute=False):
    return {'key': key, 'name': name, 'symbol': symbol, 'tile': tile or key.upper(), 'unit': unit,
            'polarity': 'standard', 'band': 1.0, 'session': session, 'note': note,
            'substitute': substitute}


def _fx(code, name_local, band=0.5, extra=''):
    return {'key': 'fx', 'name': 'USD / %s' % code, 'symbol': '%s=X' % code, 'tile': 'USD_%s' % code,
            'unit': '%s per USD' % code, 'polarity': 'inverted', 'band': band, 'session': 'fx',
            'note': 'A RISING number means a WEAKER %s.%s' % (name_local, (' ' + extra) if extra else ''),
            'substitute': False}


def _cm(key, name, symbol, unit, note):
    return {'key': key, 'name': name, 'symbol': symbol, 'tile': key.upper(), 'unit': unit,
            'polarity': 'standard', 'band': 1.5, 'session': 'fx', 'note': note, 'substitute': False}


SOY_NOTE = ('CBOT soybeans: the country\'s largest export. A rising price is good news for the '
            'exporter -- and China, the dominant buyer, decides much of it.')
COPPER_NOTE = 'COMEX copper: the country\'s largest export. Rising = more export revenue.'

COUNTRIES = {
    'argentina': {'code': 'AR', 'card_label': 'Argentina Financial Pulse', 'instruments': [
        _eq('merval', 'Merval', '^MERV', 'ARS', 'ba',
            'Buenos Aires headline index, priced in pesos -- part of any rise is inflation, so read it with the peso.'),
        _fx('ARS', 'peso', band=2.0, extra=('Managed crawl: the peso falls a little almost every day by design, '
                                            'so only a jump through the 2% band is flagged.')),
        _cm('soy', 'Soybeans', 'ZS=F', 'USD/bu', SOY_NOTE)]},
    'brazil': {'code': 'BR', 'card_label': 'Brazil Financial Pulse', 'instruments': [
        _eq('bovespa', 'Bovespa', '^BVSP', 'BRL', 'b3',
            'Sao Paulo headline index; commodity-heavy (Vale, Petrobras) and sensitive to China demand.'),
        _fx('BRL', 'real'),
        _cm('soy', 'Soybeans', 'ZS=F', 'USD/bu', SOY_NOTE)]},
    'chile': {'code': 'CL', 'card_label': 'Chile Financial Pulse', 'instruments': [
        _eq('ipsa', 'S&P IPSA', '^IPSA', 'CLP', 'scl', 'Santiago headline index.'),
        _fx('CLP', 'peso', extra='The peso tracks copper closely.'),
        _cm('copper', 'Copper', 'HG=F', 'USD/lb', COPPER_NOTE + ' Chile is the world\'s largest producer.')]},
    'colombia': {'code': 'CO', 'card_label': 'Colombia Financial Pulse', 'instruments': [
        _eq('gxg', 'MSCI Colombia (GXG)', 'GXG', 'USD', 'nyse',
            'SUBSTITUTE: a US-listed Colombia fund (in dollars), used because the local COLCAP index is '
            'thin on free feeds. It moves with both Colombian shares and the peso.', tile='COLOMBIA_ETF',
            substitute=True),
        _fx('COP', 'peso'),
        _cm('coffee', 'Coffee (arabica)', 'KC=F', 'USc/lb',
            'ICE arabica coffee; Colombia is a top-three producer.')]},
    'peru': {'code': 'PE', 'card_label': 'Peru Financial Pulse', 'instruments': [
        _eq('epu', 'MSCI Peru (EPU)', 'EPU', 'USD', 'nyse',
            'SUBSTITUTE: a US-listed Peru fund (in dollars), heavy in miners and banks.', tile='PERU_ETF',
            substitute=True),
        _fx('PEN', 'sol', extra='The sol is one of the region\'s steadier currencies; a sharp move is news.'),
        _cm('copper', 'Copper', 'HG=F', 'USD/lb', COPPER_NOTE + ' Peru is the world\'s #2 producer.')]},
    'canada': {'code': 'CA', 'card_label': 'Canada Financial Pulse', 'instruments': [
        _eq('tsx', 'S&P/TSX Composite', '^GSPTSE', 'CAD', 'nyse', 'Toronto headline index; banks and energy.'),
        _fx('CAD', 'Canadian dollar', extra='US tariffs and oil both move it.'),
        _cm('wti', 'WTI Crude', 'CL=F', 'USD/bbl',
            'US oil benchmark. Canada is the largest foreign supplier of US crude; a rising price is export revenue.')]},
}


# ── fetch ────────────────────────────────────────────────────────────────
def _fetch_quote(symbol):
    sym = urlquote(symbol, safe='')
    for host in ('query1', 'query2'):
        try:
            r = requests.get(f'https://{host}.finance.yahoo.com/v8/finance/chart/{sym}',
                             params={'range': '1mo', 'interval': '1d'},
                             headers={'User-Agent': BROWSER_UA}, timeout=TIMEOUT)
            if r.status_code != 200:
                continue
            res = ((r.json().get('chart') or {}).get('result') or [None])[0]
            if not res:
                continue
            meta = res.get('meta') or {}
            raw = ((res.get('indicators') or {}).get('quote') or [{}])[0].get('close') or []
            stamps = res.get('timestamp') or []
            points = [{'time': datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat(),
                       'value': round(float(c), 4)} for ts, c in zip(stamps, raw) if isinstance(c, (int, float))]
            closes = [c for c in raw if isinstance(c, (int, float))]
            if not closes:
                continue
            last = meta.get('regularMarketPrice') or closes[-1]
            prev = closes[-2] if len(closes) > 1 else (meta.get('chartPreviousClose') or last)
            first = closes[0]
            return {'price': round(float(last), 4),
                    'change_pct_1d': round(((last - prev) / prev) * 100, 2) if prev else 0.0,
                    'change_pct_30d': round(((last - first) / first) * 100, 2) if first else 0.0,
                    'spark_points': points[-21:], 'source': f'Yahoo/{host}'}
        except Exception as e:
            print(f'[WHA Market] {symbol} via {host}: {str(e)[:90]}')
    return None


# ── sessions (approximate: fixed offsets, no holidays) ──────────────────
_SESSIONS = {
    'ba':   (-3, 11 * 60, 17 * 60),        # Buenos Aires 11:00-17:00 ART
    'b3':   (-3, 10 * 60, 17 * 60),        # Sao Paulo 10:00-17:00 BRT
    'scl':  (-3, 9 * 60 + 30, 16 * 60),    # Santiago (summer offset) 09:30-16:00
    'nyse': (-5, 9 * 60 + 30, 16 * 60),    # New York / Toronto 09:30-16:00 ET (standard time)
}


def _session_status(session, now=None):
    now = now or datetime.now(timezone.utc)
    if session not in _SESSIONS:
        return 'open' if now.weekday() < 5 else 'closed'
    off, a, b = _SESSIONS[session]
    local = now.astimezone(timezone(timedelta(hours=off)))
    if local.weekday() >= 5:
        return 'closed'
    m = local.hour * 60 + local.minute
    if a <= m <= b:
        return 'open'
    if a - 90 <= m < a:
        return 'pre-market'
    if b < m <= b + 120:
        return 'after-hours'
    return 'closed'


def _aggregate(statuses):
    u = set(statuses)
    if not u:
        return 'closed'
    if u == {'open'}:
        return 'open'
    if u == {'closed'}:
        return 'closed'
    return 'partial' if 'open' in u else ('pre-market' if 'pre-market' in u else
                                          'after-hours' if 'after-hours' in u else 'closed')


def _tier(chg, polarity, band):
    chg = float(chg or 0)
    if polarity == 'inverted':
        chg = -chg
    if chg <= -2 * band:
        return 'stress'
    if chg <= -band:
        return 'warning'
    if chg >= 2 * band:
        return 'rally'
    return 'stable'


def build_financial_pulse(country, quotes, now=None):
    cfg = COUNTRIES[country]
    tiles, st = {}, []
    for inst in cfg['instruments']:
        q = quotes.get(inst['key'])
        if not q:
            continue
        status = _session_status(inst['session'], now)
        st.append(status)
        tiles[inst['tile']] = {
            'name': inst['name'], 'ticker': inst['symbol'], 'value': q['price'],
            'change_pct_24h': q['change_pct_1d'], 'change_pct_30d': q['change_pct_30d'],
            'tier': _tier(q['change_pct_1d'], inst['polarity'], inst['band']),
            'polarity': inst['polarity'], 'note': inst['note'], 'source': 'Yahoo Finance',
            'is_substitute': inst['substitute'], 'market_status': status,
            'timestamp': q.get('fetched_at'), 'sparkline': q.get('spark_points') or [],
        }
    return {'country': cfg['code'], 'card_label': cfg['card_label'], 'market_status': _aggregate(st),
            'last_refreshed': datetime.now(timezone.utc).isoformat(), 'tiles': tiles,
            'tile_order': [i['tile'] for i in cfg['instruments'] if i['tile'] in tiles]}


def _restatus(payload, country):
    fp = payload.get('financial_pulse')
    if isinstance(fp, dict):
        sess = {i['tile']: i['session'] for i in COUNTRIES[country]['instruments']}
        st = []
        for k, t in (fp.get('tiles') or {}).items():
            t['market_status'] = _session_status(sess.get(k, 'fx'))
            st.append(t['market_status'])
        fp['market_status'] = _aggregate(st)
    return payload


def build_country_market(country, force=False):
    key = 'wha:market:%s' % country
    if not force:
        cached = _redis_get(key)
        if cached and cached.get('financial_pulse'):
            cached['from_cache'] = True
            return _restatus(cached, country)
    now_iso = datetime.now(timezone.utc).isoformat()
    quotes = {}
    for inst in COUNTRIES[country]['instruments']:
        q = _fetch_quote(inst['symbol'])
        quotes[inst['key']] = None if q is None else dict(q, fetched_at=now_iso)
    live = [k for k, v in quotes.items() if v]
    payload = {'success': bool(live), 'country': country, 'live_count': len(live),
               'expected_count': len(quotes), 'missing': [k for k, v in quotes.items() if not v],
               'financial_pulse': build_financial_pulse(country, quotes),
               'note': ('Source: Yahoo Finance, 1-month daily, fetched server-side. USD/XXX rising = local '
                        'currency weakening. Session times are approximate (no holidays or daylight saving). '
                        'Market data is context for the stability read, not a stability score in itself.'),
               'updated_at': now_iso, 'module_version': __version__}
    if live:
        _redis_set(key, payload)
    else:
        print(f'[WHA Market] {country}: all instruments failed -- cache NOT written (a blank card is a '
              'fetch failure, not a quiet market)')
    return payload


def register_wha_market_endpoints(app, force_gate=None):
    @app.route('/api/wha/market/<country>', methods=['GET'])
    def wha_market_country(country):
        country = (country or '').lower()
        if country not in COUNTRIES:
            return jsonify({'success': False, 'error': f'unknown market {country}',
                            'available': sorted(COUNTRIES)}), 404
        force = request.args.get('force', '').lower() in ('true', '1', 'yes')
        if force and force_gate is not None:
            force = bool(force_gate(request.path))
        try:
            return jsonify(build_country_market(country, force=force))
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)[:200]}), 500

    @app.route('/debug/wha-market', methods=['GET'])
    def debug_wha_market():
        rows = {}
        for c in COUNTRIES:
            cached = _redis_get('wha:market:%s' % c) or {}
            rows[c] = {'instruments': [i['symbol'] for i in COUNTRIES[c]['instruments']],
                       'cache_present': bool(cached), 'live_count': cached.get('live_count'),
                       'missing': cached.get('missing'), 'updated_at': cached.get('updated_at')}
        return jsonify({'module': 'wha_market_quotes v%s' % __version__, 'countries': rows})

    print('[WHA Market] v%s routes: /api/wha/market/<%s>' % (__version__, '|'.join(COUNTRIES)))
