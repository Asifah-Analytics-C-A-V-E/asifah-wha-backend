"""
rhetoric_tracker_canada.py -- Canada Rhetoric & Pressure Tracker v1.0.0
Asifah Analytics -- WHA backend -- built Nov 4 2026 (shared engine: wha_rhetoric_engine.py)

THE SO WHAT (why Canada matters)
  Local:    a trade war with its closest ally is now a unity question. Alberta
            voted ~75% to stay (Oct 19 2026) and Quebec elected a sovereigntist
            PQ minority (Oct 5 2026); economic pain is what feeds both files.
  Regional: Canada is the largest foreign supplier of US crude and electricity,
            and half of the North American auto industry. Tariffs land on US
            gas prices and car plants as well as Canadian ones.
  Global:   the Arctic gateway -- the Northwest Passage (Canada: internal
            waters; US: international strait), NORAD, critical minerals -- is
            contested by the ally and the adversaries at once. A US that treats
            Canada as a pressure target is a test of what US alliances are worth.
  Unasked question: can an ally be coerced into concessions -- and if Canada
            holds, what does that teach Europe, Japan and Korea?

Dated facts (re-verify ~Dec 19 2026): PM Mark Carney (Liberal, since Mar 2025);
US tariffs incl. USMCA-compliant goods from Aug 22 2026; 50% auto/truck/parts/
steel tariff announced for Jan 1 2027; Canadian counter-tariffs on C$27.6bn
from Sep 8 2026; USMCA not renewed at the Jul 1 2026 review; Alberta referendum
Oct 19 2026 (~75% remain); PQ minority Oct 5 2026 (59 of 127 seats).

COPYRIGHT (c) 2025-2026 Asifah Analytics. All rights reserved.
"""

from wha_rhetoric_engine import CountryRhetoricTracker

VERSION = '1.0.0'

ACTORS = {
    'carney_government': {
        'name': 'Carney Government', 'flag': '🇨🇦', 'icon': '🏛️', 'vector': 'governance',
        'role': 'PM Mark Carney (Liberal, since Mar 2025), cabinet, Parliament, the opposition Conservatives',
        'baseline': 14,
        'keywords': ['carney', 'mark carney', 'prime minister carney', 'premier ministre carney', 'ottawa',
                     'parliament hill', 'house of commons', 'chambre des communes', 'poilievre', 'conservatives',
                     'liberal government', 'gouvernement liberal', 'federal budget', 'budget federal',
                     'confidence vote', 'vote de confiance', 'snap election', 'election anticipee'],
        'tripwires': [
            ('government_falls', 4, ['government falls', 'loses confidence vote', 'gouvernement renverse',
                                     'non-confidence vote passes', 'motion de censure adoptee']),
            ('snap_election_called', 3, ['calls snap election', 'dissolves parliament', 'declenche des elections',
                                         'dissolution du parlement']),
        ],
    },
    'us_trade': {
        'name': 'US-Canada Trade War', 'flag': '🇺🇸', 'icon': '🚚', 'vector': 'us_pressure',
        'role': 'US tariffs and Canadian counter-tariffs, USMCA (CUSMA), autos, steel, energy, dairy, lumber',
        'baseline': 14,
        'keywords': ['tariff', 'tariffs', 'tarifs', 'droits de douane', 'counter-tariffs', 'contre-tarifs',
                     'cusma', 'usmca', 'aceum', 'trade war', 'guerre commerciale', 'section 232',
                     'auto tariffs', 'steel tariffs', 'aluminum', 'aluminium', 'softwood lumber', 'bois d oeuvre',
                     'dairy', 'supply management', 'gestion de l offre', 'dominic leblanc', 'trade talks'],
        'tripwires': [
            ('usmca_termination', 4, ['withdraw from usmca', 'terminate usmca', 'withdraw from cusma',
                                      'notice of withdrawal', 'retrait de l aceum']),
            ('new_us_tariffs', 3, ['new tariffs on canada', 'new tariffs on canadian', 'raises tariffs on canada',
                                   'imposes tariffs on canada', 'nouveaux tarifs sur le canada']),
            ('auto_tariff_in_force', 3, ['auto tariff takes effect', 'tariffs on canadian cars take effect',
                                         '50% tariff takes effect', 'les tarifs de 50 % entrent en vigueur']),
            ('canada_retaliates', 3, ['canada retaliates', 'new counter-tariffs', 'canada imposes counter-tariffs',
                                      'nouvelles contre-mesures', 'export tax on energy', 'taxe a l exportation']),
            ('trade_deal', 1, ['trade deal with canada', 'tariff relief for canada', 'tariffs lifted on canada',
                               'accord commercial avec les etats-unis', 'entente commerciale']),
        ],
    },
    'us_security': {
        'name': 'Sovereignty & Security', 'flag': '🇺🇸', 'icon': '🛡️', 'vector': 'us_pressure',
        'role': '"51st state" talk, NORAD, the border, defence spending, intelligence sharing',
        'baseline': 6,
        'keywords': ['51st state', '51e etat', 'annexation', 'annexion', 'norad', 'canadian armed forces',
                     'forces armees canadiennes', 'defence spending', 'nato target', 'golden dome', 'border security',
                     'northern border', 'five eyes', 'sovereignty', 'souverainete canadienne'],
        'tripwires': [
            ('annexation_move', 4, ['executive order on canada', 'formal annexation', 'military force against canada',
                                    'invade canada', 'troops to the canadian border']),
            ('norad_rupture', 3, ['withdraws from norad', 'suspends norad', 'quits norad', 'retrait du norad']),
            ('defence_agreement', 1, ['norad modernization agreement', 'defence agreement with the united states',
                                      'golden dome agreement', 'accord de defense']),
        ],
    },
    'alberta': {
        'name': 'Alberta & the West', 'flag': '🛢️', 'icon': '🤠', 'vector': 'unity',
        'role': 'Premier Danielle Smith, separatist groups, pipelines and provincial powers',
        'baseline': 6,
        'keywords': ['alberta', 'danielle smith', 'alberta separatism', 'alberta independence', 'separatistes albertains',
                     'alberta referendum', 'referendum albertain', 'wexit', 'alberta prosperity project',
                     'pipeline', 'oleoduc', 'oil sands', 'sables bitumineux', 'saskatchewan'],
        'requires_any': ['alberta', 'albertain', 'danielle smith', 'saskatchewan', 'wexit', 'oil sands', 'sables bitumineux'],
        'tripwires': [
            ('binding_referendum_alberta', 4, ['binding referendum on independence', 'second alberta referendum',
                                               'nouveau referendum en alberta', 'alberta independence referendum set']),
            ('alberta_powers_grab', 2, ['alberta sovereignty act invoked', 'alberta pension plan', 'alberta police force',
                                        'loi sur la souverainete de l alberta']),
        ],
    },
    'quebec': {
        'name': 'Quebec & Sovereignty', 'flag': '⚜️', 'icon': '🗳️', 'vector': 'unity',
        'role': 'The Parti Québécois minority (since Oct 2026), Paul St-Pierre Plamondon, referendum talk',
        'baseline': 7,
        'keywords': ['quebec', 'québec', 'parti quebecois', 'parti québécois', 'pq', 'st-pierre plamondon', 'psp',
                     'souverainete', 'souveraineté', 'referendum', 'référendum', 'assemblee nationale',
                     'quebec solidaire', 'bloc quebecois', 'yves-francois blanchet'],
        'requires_any': ['quebec', 'quebecois', 'parti quebecois', 'st-pierre plamondon', 'assemblee nationale', 'bloc quebecois'],
        'tripwires': [
            ('quebec_referendum_called', 4, ['referendum date set', 'date du referendum', 'question referendaire',
                                             'referendum question tabled', 'annonce un referendum']),
            ('quebec_sovereignty_bill', 3, ['projet de loi sur la souverainete', 'sovereignty bill tabled',
                                            'loi sur l avenir du quebec']),
        ],
    },
    'arctic': {
        'name': 'Arctic Sovereignty', 'flag': '🧊', 'icon': '🧭', 'vector': 'arctic',
        'role': 'Northwest Passage, Russian and Chinese activity, icebreakers, Greenland next door',
        'baseline': 5,
        'keywords': ['arctic', 'arctique', 'northwest passage', 'passage du nord-ouest', 'nunavut', 'iqaluit',
                     'resolute', 'icebreaker', 'brise-glace', 'polar', 'greenland', 'groenland', 'nuuk',
                     'arctic sovereignty', 'souverainete arctique', 'ice pact', 'northern sea route'],
        'requires_any': ['canada', 'canadian', 'canadien', 'canadienne', 'nunavut', 'northwest passage',
                         'passage du nord-ouest', 'iqaluit', 'ottawa'],
        'tripwires': [
            ('unauthorized_transit', 4, ['transits the northwest passage without', 'sails through the northwest passage without permission',
                                         'freedom of navigation northwest passage', 'traverse le passage du nord-ouest sans']),
            ('adversary_arctic_activity', 3, ['russian bombers intercepted', 'chinese research vessel arctic',
                                              'russian aircraft norad intercept', 'chinese icebreaker canadian waters',
                                              'joint russia-china patrol']),
        ],
    },
    'china_canada': {
        'name': 'China-Canada', 'flag': '🇨🇳', 'icon': '🐉', 'vector': 'china',
        'role': 'Canola and EV tariffs, interference inquiries, critical minerals, a possible thaw',
        'baseline': 5,
        'keywords': ['china canada', 'chine canada', 'canola', 'colza', 'chinese ev', 'vehicules electriques chinois',
                     'foreign interference', 'ingerence etrangere', 'beijing', 'pekin', 'xi jinping',
                     'critical minerals', 'mineraux critiques'],
        'requires_any': ['china', 'chine', 'chinese', 'chinois', 'beijing', 'pekin', 'xi jinping'],
        'tripwires': [
            ('china_trade_thaw', 2, ['canada lifts tariffs on chinese', 'china lifts canola tariffs',
                                     'reprise du commerce avec la chine', 'canada china trade deal']),
            ('china_retaliation', 3, ['china imposes tariffs on canadian', 'china bans canadian',
                                      'la chine impose des droits sur']),
        ],
    },
}

VECTORS = {
    'governance': {'name': 'Federal Government', 'plain': 'federal politics', 'actors': ['carney_government']},
    'us_pressure': {'name': 'US Pressure (trade + sovereignty)', 'plain': 'pressure from Washington',
                    'actors': ['us_trade', 'us_security']},
    'unity': {'name': 'National Unity', 'plain': 'Alberta and Quebec', 'actors': ['alberta', 'quebec']},
    'arctic': {'name': 'Arctic Gateway', 'plain': 'the Arctic', 'actors': ['arctic']},
    'china': {'name': 'China Channel', 'plain': 'China-Canada relations', 'actors': ['china_canada']},
}

RED_LINES = [
    {'id': 'usmca_exit', 'label': 'Formal notice to leave USMCA (CUSMA)', 'tripwires': ['usmca_termination'],
     'why': 'About three-quarters of Canada\'s exports go to the US; the pact is the floor under that trade.'},
    {'id': 'annexation', 'label': 'A formal US move against Canadian sovereignty', 'tripwires': ['annexation_move'],
     'why': '"51st state" talk is rhetoric; an executive order, troop movement or formal annexation step would not be.'},
    {'id': 'quebec_ref', 'label': 'A Quebec sovereignty referendum called', 'tripwires': ['quebec_referendum_called'],
     'why': 'The PQ has promised one. The last (1995) failed by 50.6% to 49.4%.'},
    {'id': 'alberta_ref', 'label': 'A binding Alberta independence referendum', 'tripwires': ['binding_referendum_alberta'],
     'why': 'The October 2026 vote was non-binding and ~75% said stay; a binding vote would be a new stage.'},
    {'id': 'nwp', 'label': 'A foreign warship through the Northwest Passage without consent',
     'tripwires': ['unauthorized_transit'],
     'why': 'Canada calls the passage internal waters; the US calls it an international strait. A deliberate transit tests the claim.'},
    {'id': 'gov_falls', 'label': 'The federal government falls', 'tripwires': ['government_falls'],
     'why': 'Carney governs without a guaranteed majority; a fall mid-trade-war would freeze Ottawa\'s response.'},
]
GREEN_LINES = [
    {'id': 'trade_deal', 'label': 'A trade deal or tariff relief', 'tripwires': ['trade_deal'],
     'why': 'The fastest way down for both economies.'},
    {'id': 'defence', 'label': 'A new NORAD or defence agreement', 'tripwires': ['defence_agreement'],
     'why': 'Defence co-operation is the part of the relationship that has kept working.'},
]

MEANINGS = {
    'trade': {
        'plain': ('About three-quarters of Canada\'s exports go to the US. US tariffs have covered a broad range of '
                  'Canadian goods since August 22, 2026, and a 50% tariff on cars, trucks, parts and steel is '
                  'announced for January 1, 2027.'),
        'global': ('Canada is the largest foreign supplier of US crude and electricity and half of the North American '
                   'auto industry, so tariffs show up in US gas, car and building prices too.'),
        'economy': 'Ontario\'s auto belt and Alberta\'s oil feel it first; the loonie moves before politics does.',
        'not_implied': 'Tariff talk and threats are not new tariffs.',
    },
    'sovereignty': {
        'plain': ('Washington\'s "51st state" language has moved Canadian opinion and politics since 2025. NORAD -- the '
                  'joint air-defence command -- still works.'),
        'global': 'How an ally answers coercion is watched in Europe, Japan and Korea.',
        'not_implied': 'Annexation rhetoric is not an annexation move.',
    },
    'unity': {
        'plain': ('Alberta voted about 75% to stay in a non-binding referendum on October 19, 2026. Quebec elected a '
                  'Parti Québécois minority on October 5, 2026, which has promised a sovereignty referendum.'),
        'regional': 'Economic pain from the trade war is the fuel for both files.',
        'not_implied': 'Separatist talk and polls are not a referendum.',
    },
    'arctic': {
        'plain': ('Canada says the Northwest Passage is internal Canadian waters; the US and others say it is an '
                  'international strait. Russia and China are increasingly active in the Arctic.'),
        'global': 'The Arctic route matters more each year the ice retreats -- and Greenland is next door.',
        'not_implied': 'Routine NORAD intercepts of Russian aircraft happen several times a year.',
    },
    'china': {
        'plain': ('Canada and China have traded tariffs (Chinese EVs; Canadian canola). A US trade war gives Ottawa a '
                  'reason to look for other customers -- and Washington a reason to watch.'),
        'not_implied': 'Trade talk with Beijing is not a political realignment.',
    },
    'politics': {
        'plain': 'Mark Carney (Liberal) has been prime minister since March 2025.',
        'not_implied': 'Political news volume is not instability.',
    },
}

TRIPWIRE_PLAIN = {
    'government_falls': ('the federal government falling', 'governance'),
    'snap_election_called': ('a snap federal election', 'governance'),
    'usmca_termination': ('notice of withdrawal from USMCA', 'economic'),
    'new_us_tariffs': ('new US tariffs on Canada', 'economic'),
    'auto_tariff_in_force': ('the US auto and steel tariff taking effect', 'economic'),
    'canada_retaliates': ('new Canadian counter-measures', 'economic'),
    'trade_deal': ('a trade deal or tariff relief', 'economic'),
    'annexation_move': ('a formal US move against Canadian sovereignty', 'diplomatic'),
    'norad_rupture': ('a break in NORAD co-operation', 'diplomatic'),
    'defence_agreement': ('a new defence agreement', 'diplomatic'),
    'binding_referendum_alberta': ('a binding Alberta independence referendum', 'governance'),
    'alberta_powers_grab': ('Alberta taking powers from Ottawa', 'governance'),
    'quebec_referendum_called': ('a Quebec sovereignty referendum being called', 'governance'),
    'quebec_sovereignty_bill': ('a Quebec sovereignty bill', 'governance'),
    'unauthorized_transit': ('a foreign warship transiting the Northwest Passage without consent', 'kinetic'),
    'adversary_arctic_activity': ('Russian or Chinese activity near Canada\'s Arctic', 'kinetic'),
    'china_trade_thaw': ('a China-Canada trade thaw', 'economic'),
    'china_retaliation': ('Chinese trade retaliation against Canada', 'economic'),
}
TRIPWIRE_MEANING = {
    'government_falls': 'politics', 'snap_election_called': 'politics', 'usmca_termination': 'trade',
    'new_us_tariffs': 'trade', 'auto_tariff_in_force': 'trade', 'canada_retaliates': 'trade', 'trade_deal': 'trade',
    'annexation_move': 'sovereignty', 'norad_rupture': 'sovereignty', 'defence_agreement': 'sovereignty',
    'binding_referendum_alberta': 'unity', 'alberta_powers_grab': 'unity', 'quebec_referendum_called': 'unity',
    'quebec_sovereignty_bill': 'unity', 'unauthorized_transit': 'arctic', 'adversary_arctic_activity': 'arctic',
    'china_trade_thaw': 'china', 'china_retaliation': 'china',
}

SO_WHAT_RULES = [
    {'tripwires': ['usmca_termination', 'annexation_move'], 'weight': 7.0,
     'confirmed': ('A formal US move against the trade pact or Canadian sovereignty is confirmed by 2+ outlets. '
                   'This is the step from rhetoric to policy -- watch Ottawa\'s answer and the loonie.'),
     'single': 'One outlet reports a formal US move against USMCA or Canadian sovereignty; not yet corroborated.'},
    {'tripwires': ['quebec_referendum_called', 'binding_referendum_alberta'], 'weight': 6.5,
     'confirmed': ('A unity referendum has been called, confirmed by 2+ outlets. The trade war has become a '
                   'constitutional question -- watch markets, the federal response, and Washington\'s comments.')},
    {'tripwires': ['unauthorized_transit'], 'weight': 6.0,
     'confirmed': ('A foreign warship has transited the Northwest Passage without consent. Who sent it matters: '
                   'from the US it tests an ally\'s claim; from Russia or China it tests NORAD.')},
    {'tripwires': ['new_us_tariffs', 'auto_tariff_in_force', 'canada_retaliates'], 'weight': 5.0,
     'confirmed': ('The trade war escalated this cycle, confirmed by 2+ outlets. ' + MEANINGS['trade']['global'])},
    {'tripwires': ['government_falls', 'snap_election_called'], 'weight': 5.4,
     'confirmed': 'Ottawa is heading to an election mid-trade-war; expect a pause in negotiations.'},
    {'tripwires': ['china_trade_thaw', 'china_retaliation'], 'weight': 3.8,
     'confirmed': ('China-Canada trade moved this cycle. Washington reads any Ottawa-Beijing thaw as a defection; '
                   'Ottawa reads it as diversification.')},
]
VECTOR_SO_WHAT = {
    'us_pressure': (3.6, 'US-Canada pressure is in the news more than usual. ' + MEANINGS['trade']['global']),
    'unity': (3.4, 'Alberta and Quebec are in the news more than usual. ' + MEANINGS['unity']['regional']),
    'arctic': (3.0, 'Arctic reporting is up. ' + MEANINGS['arctic']['global']),
}
STANDING_SO_WHAT = [
    'The unasked question: can an ally be coerced into concessions? If Canada holds, other allies learn one '
    'lesson; if it folds, they learn another. The answer is being written in Ottawa, Edmonton and Quebec City.',
]

CONFIG = {
    'slug': 'canada', 'name': 'Canada', 'flag': '🇨🇦', 'version': VERSION, 'facts_as_of': '2026-11-04',
    'actors': ACTORS, 'vectors': VECTORS,
    'rss_feeds': {},          # Canadian outlet feeds could not be verified from here; Google News carries them by name.
    'google_queries': [
        ('Carney tariffs', 'en-CA', 'CA'), ('CUSMA Canada trade talks', 'en-CA', 'CA'),
        ('Alberta separatism', 'en-CA', 'CA'), ('Quebec referendum PQ', 'en-CA', 'CA'),
        ('Arctic sovereignty Canada', 'en-CA', 'CA'), ('Canada China canola', 'en-CA', 'CA'),
        ('Carney tarifs', 'fr-CA', 'CA'), ('référendum Québec PQ', 'fr-CA', 'CA'),
        ('Canada tariffs Trump', 'en-US', 'US'),
    ],
    'gdelt_en': ['Canada tariffs', 'Carney', 'Alberta separatism', 'Northwest Passage'],
    'gdelt_es': [],
    'newsapi_queries': ['Carney Canada', 'Canada tariffs', 'Quebec referendum'],
    'brave_queries': ['Canada trade war news', 'Alberta Quebec separatism'],
    'scrub': ['canada goose', 'air canada flight'],
    'context_terms': ('canada', 'canadian', 'canadians', 'canadien', 'canadienne', 'canadiens', 'ottawa', 'carney',
                      'poilievre', 'alberta', 'quebec', 'ontario', 'toronto', 'montreal', 'vancouver', 'calgary',
                      'edmonton', 'saskatchewan', 'manitoba', 'nunavut', 'cusma', 'loonie', 'huard', 'tsx',
                      'parti quebecois', 'danielle smith', 'doug ford', 'leblanc', 'norad'),
    'own_outlets': ('cbc', 'radio-canada', 'globe and mail', 'theglobeandmail', 'national post', 'toronto star',
                    'ctv', 'global news', 'la presse', 'le devoir', 'calgary herald', 'edmonton journal', 'macleans'),
    'own_tld': '.ca/',
    'foreign_markers': ('mexico', 'sheinbaum', 'australia', 'united kingdom', 'india', 'japan', 'germany', 'france'),
    'exclusions': {
        'new_us_tariffs': ('exempt', 'exemption', 'pause', 'delay', 'suspend'),
        'annexation_move': ('joke', 'jokes', 'rhetoric', 'rules out', 'denies'),
        'quebec_referendum_called': ('1995', '1980', 'no referendum', 'pas de referendum', 'apres 2029'),
        'binding_referendum_alberta': ('rules out', 'no second', 'pas de second'),
        'adversary_arctic_activity': ('exercise', 'exercice'),
    },
    'red_lines': RED_LINES, 'green_lines': GREEN_LINES,
    'meanings': MEANINGS, 'tripwire_plain': TRIPWIRE_PLAIN, 'tripwire_meaning': TRIPWIRE_MEANING,
    'actor_meaning': {'carney_government': 'politics', 'us_trade': 'trade', 'us_security': 'sovereignty',
                      'alberta': 'unity', 'quebec': 'unity', 'arctic': 'arctic', 'china_canada': 'china'},
    'vector_pressure': {'governance': 'governance', 'us_pressure': 'economic', 'unity': 'governance',
                        'arctic': 'diplomatic', 'china': 'economic'},
    'so_what_rules': SO_WHAT_RULES, 'vector_so_what': VECTOR_SO_WHAT, 'standing_so_what': STANDING_SO_WHAT,
    'quiet_so_what': ('Canada reads quiet this cycle. What would change that: a USMCA withdrawal notice, the '
                      'January 1 auto tariff taking effect, a Quebec or binding Alberta referendum being called, or '
                      'a foreign warship through the Northwest Passage.'),
    'background': MEANINGS['politics']['plain'],
    'spokes': [
        ('us', 'us_trade', 'pressure_target',
         'US tariffs on Canada since August 2026 and "51st state" rhetoric turned the closest ally into a pressure target.'),
        ('china', 'china_canada', 'trade_rival', 'Canada and China have traded tariffs on EVs and canola.'),
    ],
    'hub_names': {'us': 'US', 'china': 'China'},
    'fingerprints': {'canada_trade_rupture': ['usmca_termination', 'new_us_tariffs', 'auto_tariff_in_force'],
                     'canada_unity_crisis': ['quebec_referendum_called', 'binding_referendum_alberta'],
                     'canada_arctic_incident': ['unauthorized_transit', 'adversary_arctic_activity']},
}

tracker = CountryRhetoricTracker(CONFIG)


def register_canada_rhetoric_endpoints(app, force_gate=None, start_background=True):
    tracker.register(app, force_gate=force_gate, start_background=start_background, warmup_seconds=320)
