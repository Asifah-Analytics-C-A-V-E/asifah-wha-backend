"""
rhetoric_tracker_paraguay.py -- Paraguay Rhetoric & Pressure Tracker v1.1.0
Asifah Analytics -- WHA backend -- built Nov 4 2026 (shared engine: wha_rhetoric_engine.py)

THE SO WHAT (why Paraguay matters)
  Local:    a small, stable country whose politics run through the Colorado
            Party -- and through ex-president Horacio Cartes, sanctioned by the
            US in 2023 for corruption, citing ties to Hizballah members.
  Regional: Ciudad del Este anchors the Tri-Border Area with Brazil and
            Argentina: the hemisphere's best-known Hizballah finance hub, and
            a route for Brazil's PCC gang, cocaine and contraband.
  Global:   Taiwan's last diplomatic ally in South America (since 1957). If
            Asunción switches, Beijing completes the continent -- and the switch
            would be sold as a beef-and-soy export deal.
  Unasked question: is the money (to Lebanon, through Itaipú, from beef and soy
            to China) moving Paraguay's alignment faster than its politics admit?

Honesty rule (Hizballah): the local effect is crime and money; the So What is
money flowing to Lebanon. Attack risk needs 2+ outlets reporting a plot.

v1.1.0 (Nov 6 2026): Peña resigned on Nov 5 2026 as the Chamber of Deputies moved
to impeach him; the tracker only knew "impeachment move" (L3) and its background
still said "his single term ends in 2028". Added: president_resigns /
president_removed tripwires (L4, governance crisis), a red line for a president
forced out, a So What that asks the unasked question (does the Taiwan tie
survive a new government?), and a dated background line.

Dated facts (re-verify ~Dec 19 2026): Santiago Peña (Colorado) took office Aug 2023
for a single term to 2028 and RESIGNED Nov 5 2026 ahead of impeachment; Peña reaffirmed Taiwan ties in Taipei May 7 2026;
Hizballah listed as terrorist 2019; US sanctions on Cartes 2023; 2020 Pedro Juan
Caballero prison escape (75 inmates, mostly PCC); Itaipú debt paid off 2023,
Annex C renegotiation open.

COPYRIGHT (c) 2025-2026 Asifah Analytics. All rights reserved.
"""

from wha_rhetoric_engine import CountryRhetoricTracker

VERSION = '1.1.0'

ACTORS = {
    'pena_government': {
        'name': 'Peña Government', 'flag': '🇵🇾', 'icon': '🏛️', 'vector': 'governance',
        'role': 'President Santiago Peña (Colorado, 2023-2028), cabinet, Congress',
        'baseline': 10,
        'keywords': ['santiago pena', 'presidente pena', 'gobierno de pena', 'pena palmieri', 'mburuvicha roga', 'palacio de lopez',
                     'gobierno paraguayo', 'paraguayan government', 'congreso paraguayo', 'senado paraguayo',
                     'camara de diputados', 'juicio politico', 'gabinete'],
        'tripwires': [
            ('impeachment_move', 3, ['juicio politico a pena', 'juicio politico al presidente', 'impeachment pena',
                                    'juicio politico contra pena', 'juicio politico contra santiago pena',
                                    'impeach pena', 'impeachment against pena']),
            # v1.1.0 (Nov 6 2026): a head of state forced out is a governance crisis (L4)
            ('president_resigns', 4, ['renuncia de pena', 'pena renuncia', 'renuncio pena', 'renuncio el presidente',
                                      'renuncia del presidente', 'renuncia a la presidencia', 'pena resigns',
                                      'pena resigned', 'resignation of president pena', 'paraguay president resigns',
                                      'paraguayan president resigns']),
            ('president_removed', 4, ['destituyen a pena', 'pena destituido', 'destitucion de pena',
                                      'destitucion del presidente', 'senado destituye', 'pena removed from office',
                                      'pena ousted', 'removed from office in paraguay']),
            ('cabinet_crisis', 2, ['crisis de gabinete', 'renuncia masiva de ministros']),
        ],
    },
    'cartes_colorado': {
        'name': 'Cartes & the Colorado Party', 'flag': '🇵🇾', 'icon': '🎩', 'vector': 'governance',
        'role': 'Ex-president Horacio Cartes (US-sanctioned 2023), Honor Colorado faction, corruption cases',
        'baseline': 6,
        'keywords': ['horacio cartes', 'cartes', 'honor colorado', 'partido colorado', 'anr', 'tabacalera del este',
                     'tabesa', 'ofac paraguay', 'sanciones a cartes', 'corrupcion', 'lavado de dinero'],
        'tripwires': [
            ('new_us_sanctions', 3, ['nuevas sanciones de estados unidos', 'ofac sanciona', 'us sanctions paraguayan',
                                     'treasury sanctions paraguay', 'designado significativamente corrupto']),
            ('cartes_charged', 3, ['imputan a cartes', 'cartes imputado', 'cartes charged', 'cartes indicted']),
        ],
    },
    'tba_hizballah': {
        'name': 'Tri-Border & Hizballah Finance', 'flag': '🕸️', 'icon': '🛡️', 'vector': 'security',
        'role': 'Ciudad del Este, money laundering, contraband, Hizballah-linked financiers',
        'baseline': 6,
        'keywords': ['ciudad del este', 'triple frontera', 'tri-border', 'hezbollah', 'hezbola', 'hizballah',
                     'hizbollah', 'lavado de dinero', 'money laundering', 'contrabando', 'smuggling',
                     'financiamiento del terrorismo', 'terror financing', 'seprelad', 'libanes', 'lebanese'],
        'tripwires': [
            ('terror_plot', 4, ['frustran un atentado', 'desbaratan un atentado', 'planeaba un atentado',
                                'foiled attack', 'terror plot']),
            ('hizballah_arrest', 3, ['detenido vinculado a hezbollah', 'detienen a financista de hezbollah',
                                     'hezbollah financier arrested', 'arrested hezbollah', 'extraditado por financiar a hezbollah']),
            ('laundering_bust', 3, ['desarticulan red de lavado', 'money laundering ring dismantled',
                                    'megaoperativo contra el lavado', 'operativo contra lavado en ciudad del este']),
        ],
    },
    'pcc_crime': {
        'name': 'PCC & Organised Crime', 'flag': '💀', 'icon': '🔫', 'vector': 'security',
        'role': 'Brazil\'s PCC in border cities and prisons, cocaine routes, marijuana, Pedro Juan Caballero',
        'baseline': 8,
        'keywords': ['pcc', 'primeiro comando da capital', 'primer comando de la capital', 'comando vermelho',
                     'pedro juan caballero', 'narcotrafico', 'cocaina', 'marihuana', 'carcel', 'penitenciaria',
                     'tacumbu', 'sicariato', 'sicarios', 'senad', 'crimen organizado'],
        'tripwires': [
            ('prison_break', 3, ['fuga masiva', 'se fugaron', 'mass prison break', 'prison escape']),
            ('prison_riot', 3, ['motin en tacumbu', 'motin carcelario', 'prison riot', 'toma de la carcel']),
            ('official_killed', 4, ['asesinan a fiscal', 'fiscal asesinado', 'asesinan a intendente',
                                    'periodista asesinado', 'prosecutor killed', 'journalist killed']),
        ],
    },
    'taiwan_china': {
        'name': 'Taiwan vs China', 'flag': '🇹🇼', 'icon': '⚖️', 'vector': 'alignment',
        'role': 'Taiwan\'s last South American ally (since 1957); the beef-and-soy lobby that wants China',
        'baseline': 5,
        'keywords': ['taiwan', 'taiwán', 'taipei', 'taipéi', 'lai ching-te', 'china continental', 'beijing', 'pekin',
                     'republica popular china', 'relaciones con china', 'reconocimiento diplomatico',
                     'carne a china', 'soja a china', 'mercado chino'],
        'tripwires': [
            ('switch_to_beijing', 4, ['rompe relaciones con taiwan', 'establece relaciones con china',
                                      'switches recognition to beijing', 'cuts ties with taiwan']),
            ('switch_motion', 3, ['proyecto para reconocer a china', 'mocion para relaciones con china',
                                  'senado debate relaciones con china']),
            ('taiwan_reaffirmed', 1, ['reafirma alianza con taiwan', 'reaffirms ties with taiwan', 'visita a taipei',
                                      'cooperacion con taiwan']),
        ],
    },
    'itaipu_brazil': {
        'name': 'Itaipú & Brazil', 'flag': '🇧🇷', 'icon': '⚡', 'vector': 'energy',
        'role': 'Itaipú tariff and Annex C talks, Yacyretá, Paraná river levels, Brazil relations',
        'baseline': 6,
        'keywords': ['itaipu', 'itaipú', 'anexo c', 'annex c', 'yacyreta', 'yacyretá', 'tarifa de itaipu',
                     'rio parana', 'río paraná', 'bajante', 'hidrovia', 'lula', 'brasil'],
        'requires_any': ['itaipu', 'yacyreta', 'anexo c', 'annex c', 'parana', 'hidrovia', 'brasil', 'brazil'],
        'tripwires': [
            ('itaipu_dispute', 3, ['crisis en itaipu', 'suspende negociacion del anexo c', 'itaipu dispute',
                                   'conflicto por la tarifa de itaipu']),
            ('itaipu_deal', 1, ['acuerdo sobre el anexo c', 'acuerdo tarifa itaipu', 'itaipu agreement']),
            ('river_crisis', 2, ['bajante historica', 'record low parana', 'barcazas varadas']),
        ],
    },
    'us_paraguay': {
        'name': 'US-Paraguay', 'flag': '🇺🇸', 'icon': '🦅', 'vector': 'us',
        'role': 'Security co-operation, sanctions, SOUTHCOM, counter-narcotics, the embassy',
        'baseline': 4,
        'keywords': ['estados unidos paraguay', 'us paraguay', 'embajada de estados unidos', 'southcom',
                     'comando sur', 'dea', 'acuerdo de cooperacion', 'sofa', 'rubio paraguay'],
        'tripwires': [
            ('security_agreement', 1, ['acuerdo de cooperacion en defensa', 'status of forces', 'acuerdo sofa',
                                       'security agreement with paraguay']),
            ('us_troop_presence', 2, ['tropas estadounidenses en paraguay', 'us troops in paraguay']),
        ],
    },
}

VECTORS = {
    'governance': {'name': 'Governance & the Colorado Party', 'plain': 'politics',
                   'actors': ['pena_government', 'cartes_colorado']},
    'security': {'name': 'Security: Tri-Border & Crime', 'plain': 'the Tri-Border Area and organised crime',
                 'actors': ['tba_hizballah', 'pcc_crime']},
    'alignment': {'name': 'Taiwan vs China', 'plain': 'Taiwan and China', 'actors': ['taiwan_china']},
    'energy': {'name': 'Itaipú & the River', 'plain': 'Itaipú and the Paraná', 'actors': ['itaipu_brazil']},
    'us': {'name': 'US Alignment', 'plain': 'US-Paraguay relations', 'actors': ['us_paraguay']},
}

RED_LINES = [
    {'id': 'forced_out', 'label': 'The president is forced out (resignation under pressure or removal)',
     'tripwires': ['president_resigns', 'president_removed'],
     'why': 'A stable, single-party system losing its head of state mid-term is the governance break the tracker exists '
            'to catch; succession, the Cartes faction and the Taiwan tie all reopen at once.'},
    {'id': 'switch', 'label': 'Paraguay switches recognition from Taiwan to Beijing', 'tripwires': ['switch_to_beijing'],
     'why': 'Taiwan would lose its last South American ally and Beijing would complete the continent.'},
    {'id': 'plot', 'label': 'A terror plot or attack (2+ outlets)', 'tripwires': ['terror_plot'],
     'why': 'The Tri-Border networks are mostly about money; a plot would change what they are.'},
    {'id': 'official', 'label': 'A prosecutor, official or journalist assassinated', 'tripwires': ['official_killed'],
     'why': 'The 2022 murder of anti-mafia prosecutor Marcelo Pecci showed how far the networks reach.'},
    {'id': 'prison', 'label': 'A mass prison break', 'tripwires': ['prison_break'],
     'why': '75 inmates, most from the PCC, escaped Pedro Juan Caballero in 2020.'},
]
GREEN_LINES = [
    {'id': 'taiwan', 'label': 'Taiwan alliance reaffirmed', 'tripwires': ['taiwan_reaffirmed'],
     'why': 'Each reaffirmation buys Taipei time.'},
    {'id': 'us_sec', 'label': 'US-Paraguay security agreement step', 'tripwires': ['security_agreement'],
     'why': 'Co-operation on the Tri-Border is the main lever against the money networks.'},
    {'id': 'itaipu', 'label': 'Itaipú agreement', 'tripwires': ['itaipu_deal'],
     'why': 'Settles the biggest money question in Paraguayan politics.'},
]

MEANINGS = {
    'tba': {
        'plain': ('Ciudad del Este is the commercial hub of the Tri-Border Area with Brazil and Argentina -- long '
                  'reported as a centre for smuggling, money laundering and Hizballah-linked finance. Paraguay listed '
                  'Hizballah as a terrorist organisation in 2019.'),
        'global': 'The So What is money flowing to Lebanon, not local attack risk.',
        'not_implied': 'Tri-Border crime and money stories are not attack warnings.',
    },
    'crime': {
        'plain': ('Brazil\'s PCC gang has spread into Paraguay\'s border cities and prisons; Paraguay is South '
                  'America\'s largest marijuana producer and a cocaine route to Europe.'),
        'not_implied': 'Routine drug seizures are the baseline, not escalation.',
    },
    'taiwan': {
        'plain': ('Paraguay has recognised Taipei since 1957 -- the last South American country to do so. Peña '
                  'reaffirmed the tie in Taipei in May 2026.'),
        'global': ('China, which does not trade officially with Taiwan\'s allies, is the market Paraguayan beef and '
                   'soy cannot reach directly; a switch would be sold as an export deal.'),
        'not_implied': 'Lobbying for the China market is not a switch.',
    },
    'itaipu': {
        'plain': ('Itaipú (with Brazil) is one of the world\'s largest hydro dams; its debt was paid off in 2023, '
                  'opening a renegotiation of the treaty\'s financial terms (Annex C) worth billions a year.'),
        'not_implied': 'Tariff talks are routine; a suspension would not be.',
    },
    'politics': {
        'plain': ('Santiago Peña (Colorado Party) took office in August 2023 for a single term to 2028; on Nov 5 2026 he '
                  'resigned as the Chamber of Deputies moved to impeach him (background dated Nov 6 2026 -- check the '
                  'live read for what followed). Ex-president Horacio Cartes, sanctioned by the US in 2023, leads the '
                  'party\'s dominant faction.'),
        'not_implied': 'Political news volume is not instability.',
    },
    'us': {
        'plain': 'Washington works with Asunción on counter-narcotics and the Tri-Border while sanctioning Cartes.',
        'not_implied': 'Embassy statements are not policy changes.',
    },
}

TRIPWIRE_PLAIN = {
    'impeachment_move': ('an impeachment move against Peña', 'governance'),
    'president_resigns': ('the president resigning under pressure', 'governance'),
    'president_removed': ('the president removed from office', 'governance'),
    'cabinet_crisis': ('a cabinet crisis', 'governance'),
    'new_us_sanctions': ('new US sanctions on Paraguayan figures', 'diplomatic'),
    'cartes_charged': ('criminal charges against Horacio Cartes', 'governance'),
    'terror_plot': ('a foiled terror plot', 'kinetic'),
    'hizballah_arrest': ('an arrest linked to Hizballah finance', 'kinetic'),
    'laundering_bust': ('a money-laundering ring dismantled', 'economic'),
    'prison_break': ('a mass prison break', 'kinetic'),
    'prison_riot': ('a prison riot', 'kinetic'),
    'official_killed': ('the killing of a prosecutor, official or journalist', 'kinetic'),
    'switch_to_beijing': ('Paraguay switching recognition to Beijing', 'diplomatic'),
    'switch_motion': ('a motion in Congress to recognise Beijing', 'diplomatic'),
    'taiwan_reaffirmed': ('the Taiwan alliance reaffirmed', 'diplomatic'),
    'itaipu_dispute': ('an Itaipú dispute with Brazil', 'economic'),
    'itaipu_deal': ('an Itaipú agreement', 'economic'),
    'river_crisis': ('a low Paraná river stranding barges', 'economic'),
    'security_agreement': ('a US-Paraguay security agreement step', 'diplomatic'),
    'us_troop_presence': ('US troops in Paraguay', 'diplomatic'),
}
TRIPWIRE_MEANING = {
    'impeachment_move': 'politics', 'president_resigns': 'politics', 'president_removed': 'politics',
    'cabinet_crisis': 'politics', 'new_us_sanctions': 'politics',
    'cartes_charged': 'politics', 'terror_plot': 'tba', 'hizballah_arrest': 'tba', 'laundering_bust': 'tba',
    'prison_break': 'crime', 'prison_riot': 'crime', 'official_killed': 'crime', 'switch_to_beijing': 'taiwan',
    'switch_motion': 'taiwan', 'taiwan_reaffirmed': 'taiwan', 'itaipu_dispute': 'itaipu', 'itaipu_deal': 'itaipu',
    'river_crisis': 'itaipu', 'security_agreement': 'us', 'us_troop_presence': 'us',
}

SO_WHAT_RULES = [
    {'tripwires': ['president_resigns', 'president_removed'], 'weight': 6.5,
     'confirmed': ('Paraguay\'s president has been forced out mid-term, confirmed by 2+ outlets. The unasked question is '
                   'not who governs next week but what the transition reopens: the Cartes faction\'s grip on the '
                   'Colorado Party, the Itaipú money, and the Taiwan tie -- a new government is the moment Beijing\'s '
                   'beef-and-soy offer is easiest to accept.'),
     'single': ('One outlet reports the president resigning or being removed; wait for a second before reading it as a '
                'governance crisis.')},
    {'tripwires': ['switch_to_beijing'], 'weight': 7.5,
     'confirmed': ('Paraguay has switched recognition to Beijing, confirmed by 2+ outlets. Taiwan has no ally left in '
                   'South America; watch Washington\'s response and the beef and soy contracts that follow.'),
     'single': 'One outlet reports a switch to Beijing; not corroborated. These reports recur -- wait for a second outlet.'},
    {'tripwires': ['terror_plot'], 'weight': 7.0,
     'confirmed': ('A terror plot in Paraguay is confirmed by 2+ outlets -- the Tri-Border networks moving from money '
                   'to operations. Read it against the Middle East: Iran-Israel tension sets the tempo.')},
    {'tripwires': ['official_killed', 'prison_break'], 'weight': 5.6,
     'confirmed': 'Organised crime struck at the state this cycle, confirmed by 2+ outlets. ' + MEANINGS['crime']['plain']},
    {'tripwires': ['hizballah_arrest', 'laundering_bust'], 'weight': 4.8,
     'confirmed': ('A Tri-Border money case moved this cycle. The local effect is crime and money; the So What is '
                   'money flowing to Lebanon.')},
    {'tripwires': ['new_us_sanctions', 'cartes_charged'], 'weight': 4.6,
     'confirmed': ('The Cartes file moved this cycle. Washington\'s pressure on the Colorado Party\'s most powerful '
                   'figure is pressure on Peña\'s coalition.')},
    {'tripwires': ['switch_motion'], 'weight': 4.4,
     'confirmed': 'A motion to recognise Beijing is in Congress. ' + MEANINGS['taiwan']['global']},
    {'tripwires': ['itaipu_dispute', 'river_crisis'], 'weight': 3.8,
     'confirmed': 'Paraguay\'s energy and export money is under pressure this cycle. ' + MEANINGS['itaipu']['plain']},
]
VECTOR_SO_WHAT = {
    'security': (3.4, 'Tri-Border and organised-crime reporting is up. ' + MEANINGS['tba']['not_implied']),
    'alignment': (3.4, 'Taiwan-China reporting is up. ' + MEANINGS['taiwan']['global']),
}
STANDING_SO_WHAT = [
    'The unasked question: is money -- to Lebanon through the Tri-Border, from beef and soy toward China, '
    'through Itaipú -- moving Paraguay faster than its politics admit?',
]


def _hizballah_read(redis_get):
    return redis_get('hizballah_latam:read:paraguay') or {}


def _hizballah_signal(t, ctx):
    r = ctx['extras'].get('hizballah') or {}
    lvl = int(r.get('level') or 0)
    if lvl < 2:
        return []
    lane = r.get('lane', '')
    return [t.sig('hizballah_latam', lvl if lane == 'corroborated' else min(lvl, 2),
                  'Paraguay: Hizballah Latin America module reads L%d (%s)' % (lvl, lane.replace('_', ' ')),
                  (r.get('sentence') or '') + ' ' + MEANINGS['tba']['not_implied'], 'kinetic', 'tba',
                  actor='tba_hizballah', kind='crosstheater',
                  sources=[{'title': i.get('title'), 'url': i.get('url'), 'source': i.get('source')}
                           for i in (r.get('items') or [])[:3]])]


CONFIG = {
    'slug': 'paraguay', 'name': 'Paraguay', 'flag': '🇵🇾', 'version': VERSION, 'facts_as_of': '2026-11-04',
    'actors': ACTORS, 'vectors': VECTORS,
    'rss_feeds': {
        'abc_color': {'url': 'https://www.abc.com.py/arc/outboundfeeds/rss/?outputType=xml', 'name': 'ABC Color',
                      'language': 'es', 'max': 60},
        'la_nacion_py': {'url': 'https://www.lanacion.com.py/arc/outboundfeeds/rss/?outputType=xml',
                         'name': 'La Nación (Paraguay)', 'language': 'es', 'max': 60},
    },
    'google_queries': [
        ('Santiago Peña', 'es-419', 'PY'), ('Horacio Cartes', 'es-419', 'PY'), ('Ciudad del Este lavado', 'es-419', 'PY'),
        ('Paraguay Taiwán China', 'es-419', 'PY'), ('Itaipú Anexo C', 'es-419', 'PY'), ('PCC Paraguay', 'es-419', 'PY'),
        ('Paraguay Hezbollah', 'en-US', 'US'), ('Paraguay Taiwan', 'en-US', 'US'),
    ],
    'gdelt_en': ['Paraguay Taiwan', 'Paraguay Pena', 'Ciudad del Este'],
    'gdelt_es': ['Paraguay Peña', 'Triple Frontera Paraguay'],
    'newsapi_queries': ['Paraguay', 'Ciudad del Este'],
    'brave_queries': ['Paraguay news Pena', 'Paraguay Taiwan'],
    'scrub': [],
    'context_terms': ('paraguay', 'paraguayo', 'paraguaya', 'paraguayos', 'paraguayan', 'asuncion', 'asunción',
                      'ciudad del este', 'santiago pena', 'presidente pena', 'cartes', 'pedro juan caballero', 'encarnacion',
                      'itaipu', 'yacyreta', 'chaco paraguayo', 'senad', 'tacumbu', 'mburuvicha roga', 'alto parana'),
    'own_outlets': ('abc color', 'abc.com.py', 'la nacion (paraguay)', 'lanacion.com.py', 'ultima hora', 'ultimahora',
                    'hoy.com.py', 'npy', 'unicanal', 'lanacion.com.py'),
    'own_tld': '.com.py/',
    'foreign_markers': ('argentina', 'milei', 'mexico', 'colombia', 'venezuela', 'peru', 'chile', 'bolivia',
                        'uruguay', 'espana', 'trump', 'estados unidos elecciones'),
    'exclusions': {
        'terror_plot': ('aniversario', 'anniversary', '1994', '1992', 'pelicula', 'serie'),
        'switch_to_beijing': ('descarta', 'rechaza', 'no romperá', 'no rompera', 'rules out', 'rejects', 'honduras',
                              'nicaragua', 'panama', 'republica dominicana', 'el salvador'),
        'prison_break': ('recapturan', 'recaptured', '2020', 'aniversario'),
        'official_killed': ('pecci', 'aniversario', 'anniversary', '2022'),
    },
    'red_lines': RED_LINES, 'green_lines': GREEN_LINES,
    'meanings': MEANINGS, 'tripwire_plain': TRIPWIRE_PLAIN, 'tripwire_meaning': TRIPWIRE_MEANING,
    'actor_meaning': {'pena_government': 'politics', 'cartes_colorado': 'politics', 'tba_hizballah': 'tba',
                      'pcc_crime': 'crime', 'taiwan_china': 'taiwan', 'itaipu_brazil': 'itaipu', 'us_paraguay': 'us'},
    'vector_pressure': {'governance': 'governance', 'security': 'kinetic', 'alignment': 'diplomatic',
                        'energy': 'economic', 'us': 'diplomatic'},
    'so_what_rules': SO_WHAT_RULES, 'vector_so_what': VECTOR_SO_WHAT, 'standing_so_what': STANDING_SO_WHAT,
    'quiet_so_what': ('Paraguay reads quiet this cycle. What would change that: a switch to Beijing, a terror plot '
                      'confirmed by 2+ outlets, a mass prison break, or the killing of a prosecutor or journalist.'),
    'background': MEANINGS['politics']['plain'],
    'spokes': [
        ('china', 'taiwan_china', 'holdout',
         'Paraguay is Taiwan\'s last South American ally; its beef and soy lobby wants the Chinese market.'),
        ('iran', 'tba_hizballah', 'finance_node',
         'Ciudad del Este is the hemisphere\'s best-known Hizballah finance hub (Tri-Border Area).'),
        ('us', 'us_paraguay', 'hemispheric_partner',
         'Security partner on counter-narcotics and the Tri-Border; the US sanctioned ex-president Cartes in 2023.'),
    ],
    'hub_names': {'us': 'US', 'china': 'China', 'iran': 'Iran'},
    'fingerprints': {'paraguay_taiwan_switch': ['switch_to_beijing', 'switch_motion'],
                     'paraguay_tba_signal': ['terror_plot', 'hizballah_arrest', 'laundering_bust']},
    'extra_reads': {'hizballah': _hizballah_read},
    'extra_signals': [_hizballah_signal],
}

tracker = CountryRhetoricTracker(CONFIG)


def register_paraguay_rhetoric_endpoints(app, force_gate=None, start_background=True):
    tracker.register(app, force_gate=force_gate, start_background=start_background, warmup_seconds=380)
