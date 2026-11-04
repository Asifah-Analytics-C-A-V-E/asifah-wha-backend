"""
polar_gateways.py -- Asifah Analytics -- WHA backend -- v1.0.0 (Nov 4 2026)

THE TWO POLAR GATEWAYS, AS SPOKES ON THE CHOKEPOINT WHEEL
  ARCTIC     = the Suez backup. Russia's Northern Sea Route is the Arctic lane
               that actually carries cargo; the Northwest Passage (Canada says
               internal waters, the US says international strait) is mostly
               theory. Every Red Sea / Suez disruption makes Moscow's NSR pitch
               louder and Beijing's "Polar Silk Road" more plausible.
  ANTARCTIC  = the Panama backup. Antarctica has no shipping lane through it,
               but the Strait of Magellan and the Drake Passage do. When drought
               cut Panama Canal transits in 2023-24, ships went around South
               America. Panama trouble makes Argentina and Chile matter for trade
               -- and the ports and airstrips at Ushuaia and Punta Arenas are the
               access points to the continent and its minerals.

WHAT IT READS (free sources only)
  * The military tracker's chokepoint fingerprints (shared Upstash, ME backend):
    military:chokepoint:{suez, bab_el_mandeb, arctic, bering_strait,
    panama_canal, magellan}. These are the PARTNER chokepoints.
  * Its own Google News RSS sweep (EN/ES/FR) for gateway events, graded by the
    shared evidence_gate: an event counts in full only with 2+ outlets.

LADDER (per gateway, 0-4; L5 is never reached here)
  L0 quiet / unread    L1 routine coverage
  L2 busier than usual, OR a single-outlet event, OR the partner chokepoint
     disrupted (the coupling condition is live)
  L3 a corroborated gateway event (diversions, restrictions, adversary vessel,
     a treaty dispute), OR partner disrupted AND gateway reporting active
  L4 a corroborated military incident / unauthorised transit in the gateway

OUTPUT
  Redis   gateway:arctic, gateway:antarctic, gateway:summary   (30h TTL)
  Flask   GET /api/wha/polar-gateways[?force=true]
          GET /api/wha/polar-gateways/<arctic|antarctic>
  The WHA regional BLUF reads gateway:* and emits a 'polar_gateway' signal at
  L2+ with an explicit `countries` list, so the GPI tags the right countries.

Dated facts (re-verify ~Dec 19 2026) live in GATEWAYS[...]['facts'].

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

__version__ = '1.0.0'

try:
    import feedparser
    FEEDPARSER = True
except ImportError:
    FEEDPARSER = False

try:
    from evidence_gate import TripwireLedger, drop_stale, outlet_of
except ImportError:                                   # pragma: no cover
    def drop_stale(a, max_age_days=10): return list(a), 0
    def outlet_of(a): return str(a.get('source') or 'unknown').lower()
    class TripwireLedger:
        def __init__(self): self._h = {}
        def add(self, tw, a, text=None): self._h.setdefault(tw, set()).add(outlet_of(a))
        def ids(self): return list(self._h)
        def result(self, tw):
            o = sorted(self._h.get(tw, ()))
            return {'grade': 'corroborated' if len(o) >= 2 else ('single_source' if o else 'none'),
                    'outlets': o, 'rumint_outlets': [], 'items': []}

UPSTASH_REDIS_URL = os.environ.get('UPSTASH_REDIS_URL')
UPSTASH_REDIS_TOKEN = os.environ.get('UPSTASH_REDIS_TOKEN')
TTL_SECONDS = 30 * 3600
SCAN_INTERVAL_SECONDS = 12 * 3600
KEY = 'gateway:%s'
SUMMARY_KEY = 'gateway:summary'
UA = 'Mozilla/5.0 (compatible; AsifahAnalytics-WHA/polar-gateways-%s; +https://asifahanalytics.com)' % __version__
LEVEL_NAMES = ['quiet', 'routine', 'watch', 'active', 'incident']
PARTNER_RANK = {'open': 0, 'monitored': 1, 'contested': 2, 'disrupted': 3}


def _fold(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s or '') if not unicodedata.combining(c)).lower()


_RX = {}


def _has(text, phrase):
    rx = _RX.get(phrase)
    if rx is None:
        rx = _RX[phrase] = re.compile(r'(?<![a-z0-9])' + re.escape(_fold(phrase)) + r'(?![a-z0-9])')
    return bool(rx.search(text))


# ════════════════════════════════════════════════════════════════════
# THE GATEWAYS
# ════════════════════════════════════════════════════════════════════
GATEWAYS = {
    'arctic': {
        'name': 'Gateway to the Arctic',
        'icon': '🧊',
        'countries': ['canada', 'us', 'russia', 'greenland', 'denmark', 'norway'],
        'pages': ['rhetoric-canada.html', 'rhetoric-us.html', 'rhetoric-greenland.html'],
        'partner': {'label': 'Suez / Red Sea', 'chokepoints': ['suez', 'bab_el_mandeb']},
        'own_chokepoints': ['arctic', 'bering_strait'],
        'relevance': ('arctic', 'arctique', 'artico', 'northwest passage', 'northern sea route',
                      'passage du nord-ouest', 'ruta del mar del norte', 'greenland', 'groenland',
                      'groenlandia', 'svalbard', 'nunavut', 'bering', 'barents', 'beaufort', 'icebreaker',
                      'brise-glace', 'rosatom', 'polar silk road'),
        'queries': [
            ('Northern Sea Route shipping', 'en-US', 'US'), ('Northwest Passage', 'en-CA', 'CA'),
            ('Arctic military Russia China', 'en-US', 'US'), ('Greenland United States Arctic', 'en-US', 'US'),
            ('Arctic icebreaker', 'en-US', 'US'), ('passage du Nord-Ouest Arctique', 'fr-CA', 'CA'),
        ],
        # (event, what, level, patterns, exclusions)
        'events': [
            ('unauthorized_transit', 'a foreign warship transiting the Northwest Passage without Canada\'s consent', 4,
             ['transits the northwest passage without', 'without canadian permission', 'freedom of navigation operation in the northwest passage',
              'sans l autorisation du canada'], ('rules out', 'would not')),
            ('arctic_clash', 'a military incident in the Arctic', 4,
             ['collision in the arctic', 'shots fired arctic', 'arctic standoff', 'incident militaire dans l arctique'],
             ('exercise', 'drill', 'simulation')),
            ('adversary_vessel', 'Russian or Chinese military or research vessels near North American Arctic waters', 3,
             ['chinese research vessel', 'chinese icebreaker', 'russian warships near alaska', 'joint russia-china patrol',
              'chinese and russian ships near alaska', 'chinese coast guard arctic'], ('exercise planned',)),
            ('nsr_surge', 'a jump in Northern Sea Route traffic or a new NSR route announcement', 3,
             ['record transits northern sea route', 'record transits on the northern sea route', 'northern sea route record', 'northern sea route traffic', 'container ship northern sea route',
              'rosatom northern sea route', 'year-round navigation northern sea route', 'polar silk road'], ()),
            ('greenland_move', 'a formal US move on Greenland', 3,
             ['executive order on greenland', 'us troops greenland', 'greenland agreement signed', 'annex greenland'],
             ('rules out', 'jokes')),
            ('bomber_intercept', 'NORAD intercepting Russian aircraft near the Arctic', 2,
             ['norad intercepts russian', 'russian bombers intercepted', 'intercepted russian aircraft off alaska'], ()),
        ],
        'facts': [
            'Canada calls the Northwest Passage internal waters; the US calls it an international strait (the 1988 deal "agrees to disagree").',
            'Russia\'s Northern Sea Route is the Arctic lane that carries real cargo; Rosatom runs it and markets it as the Suez alternative.',
            'China calls itself a "near-Arctic state"; Chinese research vessels and icebreakers have operated near Alaska.',
            'Greenland sits one strait east of Canada\'s archipelago; a US-Denmark-Greenland defence agreement was signed Sept 18 2026.',
        ],
        'so_what': ('The Arctic is the Suez backup. When the Red Sea closes, Russia\'s Northern Sea Route pitch gets '
                    'louder -- and the gateway Canada and the US both claim gets more valuable to everyone, including '
                    'Beijing.'),
        'watch': ['Red Sea / Suez status (the partner chokepoint)', 'Northern Sea Route traffic and Rosatom announcements',
                  'Foreign warships in the Northwest Passage', 'Chinese vessels near Alaska',
                  'US moves on Greenland', 'Icebreaker and NORAD milestones'],
    },
    'antarctic': {
        'name': 'Gateway to the Antarctic',
        'icon': '🐧',
        'countries': ['argentina', 'chile', 'united_kingdom', 'panama'],
        'pages': ['rhetoric-argentina.html', 'rhetoric-chile.html'],
        'partner': {'label': 'Panama Canal', 'chokepoints': ['panama_canal']},
        'own_chokepoints': ['magellan'],
        'relevance': ('antarctic', 'antarctica', 'antartida', 'antartico', 'antarctique', 'drake passage',
                      'pasaje de drake', 'strait of magellan', 'estrecho de magallanes', 'cape horn', 'cabo de hornos',
                      'ushuaia', 'punta arenas', 'tierra del fuego', 'south georgia', 'georgias del sur',
                      'falklands', 'malvinas', 'panama canal', 'canal de panama', 'krill'),
        'queries': [
            ('Panama Canal transits restrictions', 'en-US', 'US'), ('Canal de Panamá calado sequía', 'es-419', 'PA'),
            ('Strait of Magellan shipping', 'en-US', 'US'), ('Ushuaia base naval Antártida', 'es-419', 'AR'),
            ('Antarctic Treaty China', 'en-US', 'US'), ('Punta Arenas Antártica', 'es-419', 'CL'),
        ],
        'events': [
            ('south_atlantic_incident', 'a military incident in the South Atlantic or Antarctic waters', 4,
             ['incidente militar en malvinas', 'military incident falklands', 'warship confrontation south atlantic',
              'buque de guerra antartida'], ('exercise', 'ejercicio', 'aniversario', 'anniversary', '1982')),
            ('panama_restriction', 'new Panama Canal restrictions (draft limits, transit cuts)', 3,
             ['panama canal restricts', 'panama canal cuts transits', 'draft restrictions panama canal',
              'restricciones en el canal de panama', 'reduce los transitos', 'limita el calado'], ('lifts', 'levanta', 'elimina')),
            ('southern_diversion', 'ships diverting around South America (Magellan / Cape Horn)', 3,
             ['divert to the strait of magellan', 'around cape horn', 'via the strait of magellan instead',
              'desvian por el estrecho de magallanes', 'rodear el cabo de hornos'], ()),
            ('antarctic_treaty_dispute', 'a dispute over Antarctic Treaty rules (mining, military, new claims)', 3,
             ['antarctic treaty violation', 'mining in antarctica', 'military base in antarctica',
              'violacion del tratado antartico', 'mineria en la antartida'], ('ban', 'prohibicion vigente')),
            ('gateway_port_move', 'a new foreign stake in the gateway ports (Ushuaia, Punta Arenas)', 2,
             ['base naval integrada', 'naval base in ushuaia', 'chinese port ushuaia', 'puerto chino en ushuaia',
              'polo logistico antartico', 'punta arenas hub antartico'], ()),
            ('chinese_antarctic', 'Chinese expansion in Antarctica', 2,
             ['new chinese antarctic station', 'china antarctic base', 'nueva base china en la antartida',
              'qinling station'], ()),
        ],
        'facts': [
            'Ushuaia (Argentina) and Punta Arenas (Chile) are the two southern gateways to Antarctica, across the Drake Passage.',
            'Argentina, Chile and the UK claim overlapping slices of the Antarctic Peninsula; the 1959 Antarctic Treaty freezes claims and bans mining and military bases.',
            'A US-backed integrated naval base at Ushuaia was announced in April 2024; China has shown interest in the region\'s ports.',
            'In 2023-24 drought cut Panama Canal transits and ships went around South America instead.',
        ],
        'so_what': ('The south is the Panama backup. When the canal restricts transits, the Strait of Magellan and the '
                    'Drake Passage carry the overflow -- and whoever builds the ports at Ushuaia and Punta Arenas holds '
                    'the keys to Antarctica and its minerals once the treaty\'s mining ban is reopened.'),
        'watch': ['Panama Canal draft and transit limits (the partner chokepoint)', 'Diversions via Magellan / Cape Horn',
                  'Who builds or funds Ushuaia and Punta Arenas', 'Antarctic Treaty meetings and mining talk',
                  'The Falklands and the US position', 'Chinese stations and krill fleets'],
    },
}


# ════════════════════════════════════════════════════════════════════
# REDIS
# ════════════════════════════════════════════════════════════════════
def _get(key):
    if not (UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN):
        return None
    try:
        r = requests.get(f'{UPSTASH_REDIS_URL}/get/{key}',
                         headers={'Authorization': f'Bearer {UPSTASH_REDIS_TOKEN}'}, timeout=6)
        raw = r.json().get('result')
        return json.loads(raw) if raw else None
    except Exception:
        return None


def _set(key, value, ttl=TTL_SECONDS):
    if not (UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN):
        return False
    try:
        r = requests.post(f'{UPSTASH_REDIS_URL}/setex/{key}/{int(ttl)}',
                          headers={'Authorization': f'Bearer {UPSTASH_REDIS_TOKEN}'},
                          data=json.dumps(value, default=str), timeout=8)
        return r.status_code == 200
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════════
# FETCH
# ════════════════════════════════════════════════════════════════════
def _google(q, hl, gl):
    if not FEEDPARSER:
        return []
    ceid = '%s:%s' % (gl, hl.split('-')[0] if hl.startswith(('en', 'fr')) else hl)
    url = ('https://news.google.com/rss/search?q=%s+when:7d&hl=%s&gl=%s&ceid=%s' % (quote_plus(q), hl, gl, ceid))
    out = []
    try:
        resp = requests.get(url, headers={'User-Agent': UA}, timeout=12)
        for e in feedparser.parse(resp.content).entries[:25]:
            src = (e.get('source') or {}).get('title') if isinstance(e.get('source'), dict) else None
            title = e.get('title') or ''
            if not src and ' - ' in title:
                title, src = title.rsplit(' - ', 1)
            elif src and title.endswith(' - ' + src):
                title = title[:-(len(src) + 3)]
            out.append({'title': title[:300], 'url': e.get('link', ''), 'source': src or 'Google News',
                        'published': e.get('published', ''), 'feed_type': 'google_news'})
    except Exception as ex:
        print('[Polar Gateways] fetch error (%s): %s' % (q, str(ex)[:100]))
    return out


def _partner_status(chokepoints, reader):
    """Worst status across the partner chokepoints, from the military tracker's
    fingerprints. Missing = unread (the tracker writes only when it has signals)."""
    best, rows = None, []
    for cp in chokepoints:
        fp = reader('military:chokepoint:%s' % cp) or {}
        lvl = fp.get('alert_level')
        rows.append({'chokepoint': cp, 'status': lvl or 'unread', 'label': fp.get('alert_label') or 'Not reporting',
                     'signal_count': fp.get('signal_count', 0), 'scanned_at': fp.get('scanned_at')})
        if lvl and (best is None or PARTNER_RANK.get(lvl, 0) > PARTNER_RANK.get(best, 0)):
            best = lvl
    return best or 'unread', rows


# ════════════════════════════════════════════════════════════════════
# SCAN ONE GATEWAY
# ════════════════════════════════════════════════════════════════════
def scan_gateway(gid, items=None, reader=None):
    g = GATEWAYS[gid]
    reader = reader or _get
    if items is None:
        items = []
        for q, hl, gl in g['queries']:
            items.extend(_google(q, hl, gl))
            time.sleep(0.4)
    seen, dedup = set(), []
    for a in items:
        k = a.get('url') or a.get('title')
        if k and k not in seen:
            seen.add(k)
            dedup.append(a)
    fresh, stale = drop_stale(dedup, 10)
    relevant = []
    for a in fresh:
        t = _fold(' '.join(str(a.get(k) or '') for k in ('title', 'description')))
        if any(_has(t, r) for r in g['relevance']):
            a['_t'] = t
            relevant.append(a)

    led = TripwireLedger()
    for a in relevant:
        for ev, _what, _lvl, pats, excl in g['events']:
            if any(_has(a['_t'], x) for x in excl):
                continue
            if any(_has(a['_t'], p) for p in pats):
                led.add(ev, a, a['_t'])
    events = []
    level = 1 if relevant else 0
    lane = 'routine' if relevant else 'none'
    for ev, what, lvl, _p, _e in g['events']:
        r = led.result(ev)
        if r['grade'] == 'none':
            continue
        e_lvl = lvl if r['grade'] == 'corroborated' else (min(2, lvl) if r['grade'] == 'single_source' else 1)
        events.append({'event': ev, 'what': what, 'lane': r['grade'], 'level': e_lvl,
                       'outlets': r.get('outlets', []), 'items': r.get('items', [])[:3]})
        if e_lvl > level:
            level, lane = e_lvl, r['grade']

    partner, partner_rows = _partner_status(g['partner']['chokepoints'], reader)
    own, own_rows = _partner_status(g['own_chokepoints'], reader)
    coupling = False
    if PARTNER_RANK.get(partner, 0) >= 3:                       # partner disrupted
        coupling = True
        if level < 2:
            level, lane = 2, 'coupling'
        if relevant and level < 3:                               # and the gateway is being written about
            level, lane = 3, 'coupling'
    if len(relevant) >= 25 and level < 2:
        level, lane = 2, 'volume'

    top = max(events, key=lambda e: e['level'], default=None)
    if top and top['lane'] == 'corroborated':
        sentence = 'Confirmed by more than one outlet: %s.' % top['what']
    elif top and top['lane'] == 'single_source':
        sentence = 'One outlet reports %s -- not yet corroborated.' % top['what']
    elif coupling:
        sentence = ('The partner chokepoint (%s) reads disrupted -- the condition under which this gateway starts to '
                    'matter for trade is live.' % g['partner']['label'])
    elif relevant:
        sentence = 'Routine coverage (%d items); nothing high-impact confirmed.' % len(relevant)
    else:
        sentence = 'No gateway reporting reached the scanners this cycle -- unread, not calm.'
    if coupling and top:
        sentence += ' The partner chokepoint (%s) also reads disrupted.' % g['partner']['label']

    return {
        'gateway': gid, 'name': g['name'], 'icon': g['icon'], 'level': int(level), 'level_name': LEVEL_NAMES[level],
        'lane': lane, 'sentence': sentence, 'so_what': g['so_what'], 'facts': g['facts'], 'watch': g['watch'],
        'countries': g['countries'], 'pages': g['pages'],
        'partner': {'label': g['partner']['label'], 'status': partner, 'chokepoints': partner_rows},
        'gateway_waters': {'status': own, 'chokepoints': own_rows},
        'coupling_active': coupling, 'events': events,
        'items': [{'title': a.get('title'), 'url': a.get('url'), 'source': outlet_of(a)} for a in relevant[:6]],
        'articles': len(relevant), 'stale_dropped': stale,
        'facts_as_of': '2026-11-04', 'version': __version__,
    }


def scan_all(force=False):
    if not force:
        cached = _get(SUMMARY_KEY)
        if cached:
            cached['cached'] = True
            return cached
    now = datetime.now(timezone.utc).isoformat()
    out = {}
    for gid in GATEWAYS:
        r = scan_gateway(gid)
        r['scanned_at'] = now
        _set(KEY % gid, r)
        out[gid] = r
    payload = {'success': True, 'gateways': out, 'scanned_at': now, 'cached': False, 'version': __version__}
    _set(SUMMARY_KEY, payload)
    print('[Polar Gateways] scan: ' + ', '.join('%s L%d' % (k, v['level']) for k, v in out.items()))
    return payload


# ════════════════════════════════════════════════════════════════════
# FLASK
# ════════════════════════════════════════════════════════════════════
_last_force = [0.0]


def register_polar_gateway_endpoints(app, force_gate=None, start_background=True):
    from flask import jsonify, request

    def _all():
        force = request.args.get('force', 'false').lower() in ('true', '1', 'yes')
        if force:
            ok = force_gate('polar-gateways') if force_gate else True
            if not ok or time.time() - _last_force[0] < 900:
                force = False
            else:
                _last_force[0] = time.time()
        try:
            return jsonify(scan_all(force=force))
        except Exception as ex:
            return jsonify({'success': False, 'error': str(ex)[:200]}), 500

    def _one(gid):
        if gid not in GATEWAYS:
            return jsonify({'success': False, 'error': 'unknown gateway'}), 404
        r = _get(KEY % gid)
        if not r:
            r = (scan_all(force=False).get('gateways') or {}).get(gid) or {}
        return jsonify(dict(r, success=bool(r)))

    app.add_url_rule('/api/wha/polar-gateways', 'polar_gateways_all', _all, methods=['GET'])
    app.add_url_rule('/api/wha/polar-gateways/<gid>', 'polar_gateways_one', _one, methods=['GET'])

    if start_background:
        def _loop():
            time.sleep(440)
            while True:
                try:
                    scan_all(force=True)
                except Exception as ex:
                    print('[Polar Gateways] background error: %s' % str(ex)[:200])
                time.sleep(SCAN_INTERVAL_SECONDS)
        threading.Thread(target=_loop, daemon=True, name='PolarGatewaysBG').start()
    print('[Polar Gateways] endpoints registered: /api/wha/polar-gateways[/<arctic|antarctic>]')
