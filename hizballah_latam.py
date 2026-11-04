"""
hizballah_latam.py -- Asifah Analytics -- WHA backend SHARED MODULE
v1.0.0 -- Nov 4 2026

One read of Hizballah (and Iran-linked) activity in Latin America, for every
page that needs it: Paraguay and Argentina stability (Tri-Border Area),
Venezuela (Margarita Island, via the node its tracker already writes), Brazil
(Foz do Iguacu) and -- later -- the ME Hizballah / Lebanon read.

THE HONESTY RULE (Rachel, WHA build plan, Phase 3)
  The local effect is mostly CRIME AND MONEY: smuggling, laundering, trade-
  based finance, ties to the Brazilian PCC. The headline So What is money
  flowing to Lebanon. This module does NOT inflate local kinetic risk: a
  plot or attack reaches the top rung only when 2+ separate outlets report it
  as fact. The 1992 / 1994 Buenos Aires bombings are history, not a forecast.

TWO LANES, NEVER MERGED
  corroborated  2+ separate outlets, unhedged, describing an EVENT
                (designation/sanction, arrest/prosecution/extradition, seizure,
                foiled plot).
  rumint        one outlet, hedged wording ("alleged", "could", "reportedly")
                or social-only. In scope, labelled, timestamped -- and it
                graduates when a second outlet reports the same event class.

LEVELS (per country)
  0  nothing reported this cycle -- "unread, not calm": this network is
     built to be quiet, so absence is not evidence of absence
  1  commentary / anniversary / background only, or rumour only
  2  one outlet reports an enforcement event (not yet corroborated)
  3  enforcement event corroborated by 2+ outlets (designation, arrest,
     extradition, seizure, money-laundering case)
  4  plot or attack corroborated by 2+ outlets (never from one outlet)

SOURCES
  Google News RSS searches (EN / ES / PT) -- free, no key. Outlet is the real
  paper behind Google News (evidence_gate.outlet_of). Items older than 10
  days are dropped. Venezuela also folds in hizballah_latam:venezuela, the
  Margarita node rhetoric_tracker_venezuela 1.1.0 writes.

OUTPUT
  Redis  hizballah_latam:summary         full payload (TTL 30h)
  Redis  hizballah_latam:read:<country>  one country's read (TTL 30h) --
         deliberately NOT spoke:* (Hizballah is not a hub wheel) and NOT
         hizballah_latam:<country> (that is the Venezuela tracker's key).
  GET    /api/wha/hizballah-latam              cached payload
  GET    /api/wha/hizballah-latam?force=true   rescan (public force gate)
  GET    /api/wha/hizballah-latam/<country>    one country

No paid calls. Background refresh every 12h (warm-up 150s).

COPYRIGHT (c) 2025-2026 Asifah Analytics. All rights reserved.
"""

import os
import re
import json
import time
import threading
import unicodedata
from datetime import datetime, timezone
from urllib.parse import quote_plus

import requests

try:
    import feedparser
except ImportError:          # requirements.txt has it; degrade honestly if not
    feedparser = None

try:
    from evidence_gate import outlet_of, is_hedged, drop_stale
except ImportError:
    def outlet_of(a):
        return str(a.get('source') or 'unknown').lower()
    def is_hedged(t):
        return False
    def drop_stale(a, max_age_days=10):
        return list(a), 0

__version__ = '1.0.0'

UPSTASH_REDIS_URL = os.environ.get('UPSTASH_REDIS_URL') or os.environ.get('UPSTASH_REDIS_REST_URL')
UPSTASH_REDIS_TOKEN = os.environ.get('UPSTASH_REDIS_TOKEN') or os.environ.get('UPSTASH_REDIS_REST_TOKEN')

SUMMARY_KEY = 'hizballah_latam:summary'
READ_KEY = 'hizballah_latam:read:%s'
VZ_NODE_KEY = 'hizballah_latam:venezuela'
TTL_SECONDS = 30 * 3600
SCAN_INTERVAL_SECONDS = 12 * 3600
CORROBORATION = 2
UA = 'Mozilla/5.0 (compatible; AsifahAnalytics-WHA/hizballah_latam %s; +https://asifahanalytics.com)' % __version__

# ── Searches (Google News RSS) ───────────────────────────────────────────
_GN = 'https://news.google.com/rss/search?q=%s&hl=%s&gl=%s&ceid=%s'
QUERIES = [
    ('Hezbollah "Tri-Border"', 'en', 'US', 'US:en'),
    ('Hezbollah Paraguay', 'en', 'US', 'US:en'),
    ('Hezbollah Argentina', 'en', 'US', 'US:en'),
    ('Hezbollah Brazil', 'en', 'US', 'US:en'),
    ('Hezbollah Venezuela', 'en', 'US', 'US:en'),
    ('Hezbollah Latin America sanctions', 'en', 'US', 'US:en'),
    ('Hezbolá "Triple Frontera"', 'es-419', 'AR', 'AR:es-419'),
    ('Hezbolá Paraguay', 'es-419', 'PY', 'PY:es-419'),
    ('Hezbolá Argentina AMIA', 'es-419', 'AR', 'AR:es-419'),
    ('Hezbolá Venezuela', 'es-419', 'VE', 'VE:es-419'),
    ('Hezbollah "Tríplice Fronteira"', 'pt-BR', 'BR', 'BR:pt-419'),
    ('Hezbollah Brasil prisão', 'pt-BR', 'BR', 'BR:pt-419'),
]

HIZ_TERMS = ('hezbollah', 'hizballah', 'hizbollah', 'hizbullah', 'hezbola', 'hizbula', 'hizbola')

COUNTRIES = {
    'paraguay':  ('paraguay', 'ciudad del este', 'asuncion', 'pedro juan caballero', 'encarnacion'),
    'argentina': ('argentin', 'buenos aires', 'puerto iguazu', 'amia', 'misiones'),
    'brazil':    ('brazil', 'brasil', 'foz do iguacu', 'foz de iguazu', 'sao paulo', 'curitiba'),
    'venezuela': ('venezuel', 'margarita', 'nueva esparta', 'caracas', 'porlamar'),
    'colombia':  ('colombia',),
    'chile':     ('chile', 'iquique'),
    'peru':      ('peru', 'lima'),
    'bolivia':   ('bolivia',),
}
TBA_TERMS = ('tri-border', 'triple frontera', 'triplice fronteira', 'triple frontier', 'tres fronteras')

# Event classes. Order = precedence when one headline matches several.
EVENTS = [
    ('plot', 4, ('foiled', 'plot to attack', 'planned attack', 'bomb plot', 'attack plot', 'atentado frustrado',
                 'planeaba un atentado', 'plano de atentado', 'atentado planejado', 'explosives found',
                 'explosivos')),
    ('designation', 3, ('sanction', 'sanciona', 'sancion', 'ofac', 'treasury designat', 'designates',
                        'designa', 'terrorist designation', 'rewards for justice', 'recompensa')),
    ('arrest', 3, ('arrest', 'arrested', 'detained', 'detenido', 'detienen', 'capturado', 'preso', 'presos',
                   'prisao', 'preso', 'extradit', 'extradic', 'charged', 'indicted', 'imputado', 'acusado',
                   'condenado', 'convicted', 'sentenced')),
    ('seizure', 3, ('seized', 'seizure', 'incaut', 'decomis', 'apreens', 'laundering', 'lavado de dinero',
                    'lavagem de dinheiro', 'money laundering', 'smuggling ring', 'contrabando')),
]
COMMENTARY = ('anniversary', 'aniversario', 'homenaje', 'commemorat', 'years since', 'anos del atentado',
              'analysis', 'analisis', 'opinion', 'column', 'columna')

EVENT_TEXT = {
    'plot':        'a plot or attack',
    'designation': 'a terrorism designation or sanctions',
    'arrest':      'arrests, charges or extraditions',
    'seizure':     'a seizure or money-laundering case',
}

COUNTRY_DISPLAY = {'paraguay': 'Paraguay', 'argentina': 'Argentina', 'brazil': 'Brazil',
                   'venezuela': 'Venezuela', 'colombia': 'Colombia', 'chile': 'Chile',
                   'peru': 'Peru', 'bolivia': 'Bolivia'}

STANDING = {
    'paraguay': ('Ciudad del Este is the Tri-Border Area\'s commercial hub. Paraguay listed Hizballah as a '
                 'terrorist organisation in 2019, and in 2023 the US sanctioned former president Horacio Cartes '
                 'for corruption, citing ties to Hizballah members (he denies it).'),
    'argentina': ('Argentina suffered the 1992 Israeli embassy and 1994 AMIA bombings, which its courts attribute '
                  'to Iran and Hizballah; it listed Hizballah as a terrorist organisation in 2019.'),
    'brazil':    ('Foz do Iguacu is the Brazilian side of the Tri-Border Area. Brazil does not list Hizballah as a '
                  'terrorist organisation; arrests there are usually framed as crime or fraud cases.'),
    'venezuela': ('Margarita Island has long been reported as a Hizballah finance and logistics node; the interim '
                  'government has promised Washington to end Hizballah and Iranian activity.'),
}


def _has(text, terms):
    """Left-bounded match: 'lima' must not match 'climate', 'argentin' still
    matches 'argentina' / 'argentine'."""
    return any(re.search(r'(?<![a-z0-9])' + re.escape(t), text) for t in terms)


def _fold(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s or '') if not unicodedata.combining(c)).lower()


# ── Redis ───────────────────────────────────────────────────────────────
def _redis_get(key):
    if not (UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN):
        return None
    try:
        r = requests.get(f'{UPSTASH_REDIS_URL}/get/{key}',
                         headers={'Authorization': f'Bearer {UPSTASH_REDIS_TOKEN}'}, timeout=6)
        raw = r.json().get('result')
        return json.loads(raw) if raw else None
    except Exception:
        return None


def _redis_set(key, value, ttl=TTL_SECONDS):
    if not (UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN):
        return False
    try:
        r = requests.post(f'{UPSTASH_REDIS_URL}/setex/{key}/{int(ttl)}',
                          headers={'Authorization': f'Bearer {UPSTASH_REDIS_TOKEN}'},
                          data=json.dumps(value, default=str), timeout=8)
        return r.status_code == 200
    except Exception:
        return False


# ── Fetch ───────────────────────────────────────────────────────────────
def _fetch_query(q, hl, gl, ceid):
    if feedparser is None:
        return []
    url = _GN % (quote_plus(q), hl, gl, ceid)
    try:
        r = requests.get(url, headers={'User-Agent': UA}, timeout=12)
        if r.status_code != 200:
            return []
        feed = feedparser.parse(r.content)
    except Exception:
        return []
    out = []
    for e in feed.entries[:25]:
        src = e.get('source') or {}
        out.append({
            'title': e.get('title', '')[:300],
            'description': re.sub(r'<[^>]+>', ' ', e.get('summary', ''))[:400],
            'url': e.get('link', ''),
            'outlet': (src.get('title') if isinstance(src, dict) else '') or '',
            'source': 'news.google.com',
            'published': e.get('published', ''),
            'feed_type': 'rss',
            'lang': hl[:2],
        })
    return out


def fetch_articles():
    seen, arts, feeds_ok = set(), [], 0
    for q in QUERIES:
        got = _fetch_query(*q)
        feeds_ok += 1 if got else 0
        for a in got:
            key = a['url'] or a['title']
            if key and key not in seen:
                seen.add(key)
                arts.append(a)
        time.sleep(0.4)
    return arts, feeds_ok


# ── Classify ────────────────────────────────────────────────────────────
def _countries_in(text):
    hits = [c for c, terms in COUNTRIES.items() if _has(text, terms)]
    if _has(text, TBA_TERMS):
        for c in ('paraguay', 'argentina', 'brazil'):
            if c not in hits:
                hits.append(c)
    return hits


def _event_of(text):
    for cls, lvl, terms in EVENTS:
        if _has(text, terms):
            return cls, lvl
    return None, 1


def classify(articles):
    """Returns {country: {'events': {cls: {'reported': set, 'rumint': set, 'items': []}},
                           'mentions': int, 'items': []}}"""
    out = {}
    for a in articles:
        text = _fold(a.get('title', '') + ' ' + a.get('description', ''))
        if not _has(text, HIZ_TERMS):
            continue
        countries = _countries_in(text)
        if not countries:
            continue
        cls, _ = _event_of(text)
        commentary = _has(text, COMMENTARY)
        if commentary and cls != 'plot':
            cls = None          # anniversary / analysis pieces are background, not events
        outlet = outlet_of(a)
        hedged = is_hedged(text) or a.get('feed_type') in ('reddit', 'bluesky', 'telegram', 'social')
        for c in countries:
            rec = out.setdefault(c, {'events': {}, 'mentions': 0, 'items': []})
            rec['mentions'] += 1
            if len(rec['items']) < 6:
                rec['items'].append({'title': a.get('title', ''), 'outlet': outlet, 'url': a.get('url', ''),
                                     'published': a.get('published', ''), 'event': cls or 'background',
                                     'lane': 'rumint' if hedged else 'reported'})
            if cls:
                ev = rec['events'].setdefault(cls, {'reported': set(), 'rumint': set()})
                (ev['rumint'] if hedged else ev['reported']).add(outlet)
    return out


def _country_read(country, rec, vz_node=None):
    rec = rec or {'events': {}, 'mentions': 0, 'items': []}
    name = COUNTRY_DISPLAY.get(country, country.title())
    level, lane, events = 0, 'none', []
    for cls, lvl, _ in EVENTS:
        ev = rec['events'].get(cls)
        if not ev:
            continue
        n_rep, n_rum = len(ev['reported']), len(ev['rumint'])
        if n_rep >= CORROBORATION:
            e_lane, e_lvl = 'corroborated', lvl
        elif n_rep == 1:
            e_lane, e_lvl = 'single_source', 2
        else:
            e_lane, e_lvl = 'rumint', 1
        events.append({'event': cls, 'what': EVENT_TEXT[cls], 'lane': e_lane, 'level': e_lvl,
                       'outlets': sorted(ev['reported'])[:6], 'rumint_outlets': sorted(ev['rumint'])[:6]})
        if e_lvl > level:
            level, lane = e_lvl, e_lane
    if level == 0 and rec['mentions']:
        level, lane = 1, 'background'

    # Venezuela: fold in the Margarita node the VZ tracker writes
    if country == 'venezuela' and isinstance(vz_node, dict) and vz_node.get('level', 0) > level:
        level = int(vz_node.get('level') or 0)
        lane = vz_node.get('lane', lane)

    top = max(events, key=lambda e: e['level'], default=None)
    if level == 0:
        sentence = (f'No Hizballah-linked reporting on {name} this cycle -- unread, not calm: '
                    'this network is built to be quiet.')
    elif lane == 'background':
        sentence = (f'{name}: Hizballah comes up only in background or commentary pieces this cycle '
                    '(history, anniversaries, analysis) -- no new event reported.')
    elif lane == 'rumint':
        sentence = (f'{name}: claims of {top["what"] if top else "Hizballah activity"} are circulating only as '
                    'rumour or hedged reporting -- held in the rumour lane until a second outlet confirms.')
    elif lane == 'single_source':
        sentence = (f'{name}: one outlet reports {top["what"] if top else "Hizballah activity"} '
                    '-- not yet corroborated.')
    else:
        sentence = (f'{name}: {len(top["outlets"]) if top else 2} separate outlets report '
                    f'{top["what"] if top else "Hizballah activity"}.')
        if top and top['event'] != 'plot':
            sentence += (' What it means: pressure on the money network that funds Hizballah in Lebanon -- '
                         'not, on its own, a sign of local attack risk.')
        else:
            sentence += ' This is the rare kinetic case: read it with the 1992/1994 precedents and watch for arrests.'
    if country == 'venezuela' and isinstance(vz_node, dict) and vz_node.get('sentence'):
        sentence += ' Margarita node (Venezuela tracker): ' + vz_node['sentence']
    return {
        'country': country, 'display': name, 'level': level, 'lane': lane,
        'sentence': sentence, 'events': events, 'mentions': rec['mentions'],
        'items': rec['items'], 'standing': STANDING.get(country, ''),
    }


def scan():
    t0 = time.time()
    arts, feeds_ok = fetch_articles()
    arts, stale = drop_stale(arts)
    cls = classify(arts)
    vz_node = _redis_get(VZ_NODE_KEY)
    countries = {}
    for c in ('paraguay', 'argentina', 'brazil', 'venezuela'):
        countries[c] = _country_read(c, cls.get(c), vz_node if c == 'venezuela' else None)
    for c in cls:
        if c not in countries:
            countries[c] = _country_read(c, cls[c])
    tba = [countries[c] for c in ('paraguay', 'argentina', 'brazil')]
    tba_level = max(r['level'] for r in tba)
    lit = [r['display'] for r in countries.values() if r['level'] >= 2]
    if not arts:
        headline = ('No Hizballah-Latin America reporting reached the scanner this cycle (' + str(feeds_ok) +
                    ' of ' + str(len(QUERIES)) + ' searches answered) -- unread, not calm.')
    elif lit:
        headline = ('Hizballah-linked enforcement or activity reported for ' + ', '.join(lit) +
                    '. The So What is money: who is moving it, and whether the network that funds Lebanon is being squeezed.')
    else:
        headline = ('No new Hizballah-linked event in Latin America this cycle -- background and commentary only. '
                    'Quiet here is normal; this network is built to be quiet.')
    payload = {
        'success': True, 'version': __version__,
        'scanned_at': datetime.now(timezone.utc).isoformat(),
        'headline': headline, 'tba_level': tba_level,
        'countries': countries,
        'coverage': {'articles': len(arts), 'stale_dropped': stale, 'searches': len(QUERIES),
                     'searches_answered': feeds_ok},
        'rules': ('Two lanes: corroborated (2+ separate outlets, event reported as fact) and rumour (one '
                  'outlet, hedged wording or social). A plot or attack tops the scale only when 2+ outlets '
                  'report it. Local effect is mostly crime and money; the headline So What is money flowing '
                  'to Lebanon.'),
        'scan_seconds': round(time.time() - t0, 1),
    }
    _redis_set(SUMMARY_KEY, payload)
    for c, r in countries.items():
        _redis_set(READ_KEY % c, dict(r, scanned_at=payload['scanned_at'], source='hizballah_latam ' + __version__))
    print(f'[Hizballah LatAm] scan: {len(arts)} articles ({stale} stale), searches {feeds_ok}/{len(QUERIES)}, '
          f'TBA L{tba_level}, lit={lit}')
    return payload


def get_payload(force=False):
    if not force:
        cached = _redis_get(SUMMARY_KEY)
        if cached:
            cached['cached'] = True
            return cached
    return scan()


def _bg_loop():
    time.sleep(150)
    while True:
        try:
            scan()
        except Exception as e:
            print(f'[Hizballah LatAm] background scan error: {str(e)[:150]}')
        time.sleep(SCAN_INTERVAL_SECONDS)


def register_hizballah_latam_endpoints(app, force_gate=None, start_background=True):
    from flask import jsonify, request

    def _force():
        if request.args.get('force', 'false').lower() != 'true':
            return False
        return force_gate(request.path) if force_gate else True

    @app.route('/api/wha/hizballah-latam', methods=['GET'])
    def api_hizballah_latam():
        try:
            return jsonify(get_payload(force=_force()))
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)[:200]}), 500

    @app.route('/api/wha/hizballah-latam/<country>', methods=['GET'])
    def api_hizballah_latam_country(country):
        p = get_payload(force=False)
        r = (p.get('countries') or {}).get((country or '').lower())
        if not r:
            return jsonify({'success': False, 'error': 'not tracked', 'tracked': sorted(p.get('countries') or {})}), 404
        return jsonify(dict(r, success=True, scanned_at=p.get('scanned_at'), rules=p.get('rules')))

    if start_background:
        threading.Thread(target=_bg_loop, daemon=True, name='HizballahLatamBG').start()
    print(f'[Hizballah LatAm] v{__version__} routes: /api/wha/hizballah-latam[/<country>]')
