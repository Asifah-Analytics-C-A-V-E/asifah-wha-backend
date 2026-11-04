"""
rhetoric_tracker_argentina.py -- Argentina Rhetoric & Pressure Tracker v1.0.0
Asifah Analytics -- WHA backend -- built Nov 4 2026

Runs on the shared engine (wha_rhetoric_engine.py). This file is the CONFIG.

THE SO WHAT (why Argentina matters)
  Local:    can Milei's shock programme survive to the October 2027
            presidential election? The test is the peso, reserves and the street.
  Regional: South America's swing state in the US-China contest -- a US
            Treasury swap (US$20bn, Oct 2025) AND a renewed Chinese swap
            (~US$18-19bn framework, five more years from Aug 2026). Argentina
            declined BRICS membership in 2024 but never left the 2022 Belt and
            Road agreement.
  Global:   (1) food and energy -- the top exporter of soybean meal and oil,
            and Vaca Muerta, one of the world's largest shale resources;
            (2) the South Atlantic / Antarctic gateway (Falklands, Ushuaia);
            (3) the hemisphere's main Iran/Hizballah precedent -- the 1992
            Israeli embassy and 1994 AMIA bombings -- under the region's most
            pro-Israel president. This is where Middle East conflict is most
            likely to reach the Americas.

ACTORS (7) -> VECTORS (6)
  governance        presidency, congress_street
  economy           economy
  us_alignment      us_argentina
  china_alignment   china_argentina
  south_atlantic    uk_falklands
  security          security_iran   (+ the shared Hizballah LatAm module)

Dated facts (re-verify ~Dec 19 2026): Milei since Dec 2023; La Libertad
Avanza won the Oct 2025 midterms but lacks a majority; ~US$25bn of debt
payments due in 2027 (Milei, Oct 12 2026); Trump's Falklands comments
Aug 31 - Sep 3 2026; Ushuaia integrated naval base announced with US backing
(Apr 2024); China's Espacio Lejano station in Neuquén (since 2015, 50-year lease).

COPYRIGHT (c) 2025-2026 Asifah Analytics. All rights reserved.
"""

from wha_rhetoric_engine import CountryRhetoricTracker

VERSION = '1.0.0'

ACTORS = {
    'presidency': {
        'name': 'Presidency (Milei)', 'flag': '🇦🇷', 'icon': '🏛️', 'vector': 'governance',
        'role': 'Javier Milei (since Dec 2023), Karina Milei, the cabinet, La Libertad Avanza',
        'baseline': 16,
        'keywords': ['milei', 'javier milei', 'karina milei', 'casa rosada', 'adorni', 'jefe de gabinete',
                     'la libertad avanza', 'libertad avanza', 'gobierno nacional', 'argentine president',
                     'argentine government', 'presidente milei', 'gabinete nacional', 'decreto de necesidad',
                     'dnu'],
        'tripwires': [
            ('cabinet_crisis', 3, ['crisis de gabinete', 'renuncia masiva', 'cabinet crisis argentina',
                                   'ministers resign']),
            ('impeachment_move', 3, ['juicio politico a milei', 'impeachment milei', 'juicio politico al presidente']),
            ('state_of_siege', 4, ['estado de sitio', 'state of siege']),
        ],
    },
    'congress_street': {
        'name': 'Congress, Unions & the Street', 'flag': '🇦🇷', 'icon': '✊', 'vector': 'governance',
        'role': 'Veto fights in Congress, the CGT unions, pensioners, universities, Peronist governors (Kicillof)',
        'baseline': 12,
        'keywords': ['congreso', 'diputados', 'senado', 'veto', 'cgt', 'paro general', 'general strike',
                     'sindicatos', 'unions', 'jubilados', 'pensioners', 'universidades', 'marcha universitaria',
                     'piqueteros', 'protesta', 'protest', 'kicillof', 'peronismo', 'peronist', 'kirchner',
                     'cristina kirchner', 'gobernadores', 'reforma laboral', 'labor reform'],
        'tripwires': [
            ('general_strike', 3, ['paro general', 'general strike']),
            ('veto_overridden', 2, ['rechazo al veto', 'insiste con la ley', 'override the veto', 'overrides veto',
                                    'veto overridden', 'revierte el veto']),
            ('deadly_protest', 3, ['manifestante muerto', 'murio en la protesta', 'protester killed',
                                   'represion deja heridos', 'muerto en la marcha']),
        ],
    },
    'economy': {
        'name': 'Economy, Central Bank & IMF', 'flag': '💵', 'icon': '📉', 'vector': 'economy',
        'role': 'Caputo (economy), the central bank (BCRA), the peso band, reserves, the IMF, bonds',
        'baseline': 18,
        'keywords': ['caputo', 'luis caputo', 'bcra', 'banco central', 'central bank', 'reservas', 'reserves',
                     'peso', 'dolar', 'dollar', 'banda cambiaria', 'cepo', 'inflacion', 'inflation', 'indec',
                     'fmi', 'imf', 'riesgo pais', 'country risk', 'bonos', 'bonds', 'deuda', 'debt', 'merval',
                     'licitacion', 'vaca muerta', 'ypf', 'litio', 'lithium', 'soja', 'soybean'],
        'tripwires': [
            ('capital_controls_return', 4, ['vuelve el cepo', 'regreso del cepo', 'reimpone el cepo',
                                            'reimposes capital controls', 'capital controls return',
                                            'nuevo cepo']),
            ('default', 4, ['default de la deuda', 'argentina defaults', 'cesacion de pagos', 'misses bond payment',
                            'missed a bond payment', 'no pago los bonos']),
            ('peso_run', 3, ['corrida cambiaria', 'run on the peso', 'devaluacion brusca', 'peso plunges',
                             'peso se desploma', 'el dolar se dispara', 'dollar soars', 'salto del dolar']),
            ('caputo_exit', 3, ['renuncia caputo', 'caputo renuncia', 'caputo resigns', 'caputo leaves',
                                'renuncio caputo', 'salida de caputo']),
            ('imf_breakdown', 3, ['fmi suspende', 'imf suspends', 'imf halts', 'suspende el programa con el fmi']),
            # green
            ('imf_review_passed', 1, ['fmi aprueba la revision', 'imf approves review', 'imf completes review',
                                      'desembolso del fmi', 'imf disbursement', 'aprobo la revision']),
        ],
    },
    'us_argentina': {
        'name': 'US-Argentina', 'flag': '🇺🇸', 'icon': '🦅', 'vector': 'us_alignment',
        'role': 'The US Treasury swap, trade deal, Ushuaia base, F-16s, US pressure to limit China',
        'baseline': 8,
        'keywords': ['bessent', 'tesoro de estados unidos', 'us treasury', 'trump milei', 'milei trump',
                     'estados unidos argentina', 'us argentina', 'embajada de estados unidos', 'lamelas',
                     'southcom', 'comando sur', 'f-16', 'ushuaia', 'acuerdo comercial con estados unidos',
                     'swap con estados unidos', 'us swap', 'washington'],
        'tripwires': [
            ('us_ushuaia_base', 3, ['base naval integrada', 'base en ushuaia', 'naval base in ushuaia',
                                    'ushuaia naval base', 'comando sur ushuaia', 'southcom ushuaia']),
            ('us_trade_deal', 2, ['acuerdo comercial con estados unidos', 'us argentina trade agreement',
                                  'trade deal with argentina', 'acuerdo de comercio e inversiones']),
            ('us_swap_drawn', 2, ['activa el swap', 'uso del swap del tesoro', 'drew on the swap',
                                  'treasury buys pesos', 'tesoro compra pesos']),
            ('us_presses_on_china', 2, ['presion de estados unidos por china', 'us presses argentina on china',
                                        'bessent china', 'limit china', 'sacar a china', 'china out of argentina']),
        ],
    },
    'china_argentina': {
        'name': 'China-Argentina', 'flag': '🇨🇳', 'icon': '🐉', 'vector': 'china_alignment',
        'role': 'The yuan swap, the Neuquén space station, lithium, soy, fishing fleets at Mile 201',
        'baseline': 7,
        'keywords': ['china argentina', 'swap con china', 'yuan', 'yuanes', 'espacio lejano', 'estacion espacial',
                     'space station', 'neuquen', 'xi jinping', 'beijing', 'pekin', 'inversion china',
                     'chinese investment', 'milla 201', 'pesca ilegal', 'buques chinos', 'chinese fishing',
                     'ganfeng', 'zijin', 'tsingshan', 'huawei', 'ruta de la seda', 'belt and road', 'brics',
                     'embajada china', 'chinese embassy'],
        'requires_any': ['china', 'chino', 'china', 'chinese', 'yuan', 'yuanes', 'xi jinping', 'beijing', 'pekin',
                         'espacio lejano', 'ganfeng', 'zijin', 'tsingshan', 'huawei', 'brics', 'milla 201'],
        'tripwires': [
            ('space_station_row', 2, ['estacion espacial china', 'espacio lejano', 'chinese space station',
                                      'deep space station']),
            ('chinese_port_or_base', 3, ['puerto chino', 'base china', 'chinese port in argentina',
                                         'chinese base in argentina', 'base naval china']),
            ('fishing_clash', 3, ['prefectura dispara', 'captura buque chino', 'detienen buque pesquero',
                                  'chinese fishing vessel seized', 'buque chino detenido']),
            ('china_swap_move', 2, ['renueva el swap con china', 'swap with china renewed', 'activa el swap con china',
                                    'amplia el swap con china', 'cancela el swap con china']),
        ],
    },
    'uk_falklands': {
        'name': 'UK, Falklands & Antarctica', 'flag': '🇬🇧', 'icon': '🧭', 'vector': 'south_atlantic',
        'role': 'The Malvinas/Falklands claim, Sea Lion oil, the US position, Ushuaia and the Antarctic gateway',
        'baseline': 6,
        'keywords': ['malvinas', 'falklands', 'falkland islands', 'islas malvinas', 'mount pleasant', 'stanley',
                     'sea lion', 'navitas', 'rockhopper', 'georgias del sur', 'south georgia', 'antartida',
                     'antarctica', 'antarctic', 'atlantico sur', 'south atlantic', 'reino unido', 'united kingdom',
                     'britain', 'londres', 'ushuaia', 'tierra del fuego', 'pasaje de drake', 'drake passage'],
        'tripwires': [
            ('south_atlantic_incident', 4, ['incidente militar en malvinas', 'military incident falklands',
                                            'royal navy deploys', 'buque de guerra britanico',
                                            'british warship falklands']),
            # v1.0.0: the annual sovereignty speeches (UN C-24 in June, April 2) are routine and
            # excluded; only concrete measures count -- sanctions, flight / shipping restrictions.
            ('sovereignty_push', 3, ['sanciones a petroleras', 'sanctions on oil companies',
                                     'sancion a empresas que operan en malvinas', 'sanctions on companies operating in the falklands',
                                     'suspende los vuelos a malvinas', 'suspends flights to the falklands',
                                     'prohibe buques con bandera de malvinas', 'bans falklands-flagged']),
            ('us_falklands_shift', 3, ['trump malvinas', 'trump falklands', 'us position on the falklands',
                                       'estados unidos y malvinas', 'washington malvinas']),
            ('sea_lion_milestone', 2, ['sea lion', 'navitas', 'rockhopper']),
        ],
    },
    'security_iran': {
        'name': 'Security: Iran, Hizballah & the Tri-Border', 'flag': '🛡️', 'icon': '🕸️', 'vector': 'security',
        'role': 'AMIA (1994) and Israeli embassy (1992) cases, Hizballah finance in the Tri-Border Area, threats to Jewish and Israeli targets',
        'baseline': 6,
        'keywords': ['amia', 'embajada de israel', 'israeli embassy', 'hezbollah', 'hezbola', 'hizballah',
                     'hizbollah', 'iran', 'triple frontera', 'tri-border', 'puerto iguazu', 'ciudad del este',
                     'daia', 'comunidad judia', 'jewish community', 'antisemitismo', 'antisemitism',
                     'terrorismo', 'terrorism', 'ministerio de seguridad', 'israel'],
        'tripwires': [
            ('terror_attack', 4, ['atentado terrorista en', 'terror attack in buenos aires', 'atentado en buenos aires',
                                  'bomb attack in argentina', 'explosion en la sede']),
            ('terror_plot', 4, ['desbaratan un atentado', 'frustran un atentado', 'planeaba un atentado',
                                'foiled attack', 'foiled a plot', 'terror plot', 'plot to attack']),
            ('hizballah_arrest', 3, ['detenido vinculado a hezbollah', 'detienen a un miembro de hezbollah',
                                     'arrested hezbollah', 'hezbollah suspect arrested', 'detenido por financiar a hezbollah']),
            ('terror_designation', 2, ['declara organizacion terrorista', 'designa organizacion terrorista',
                                       'designates as terrorist organization', 'guardia revolucionaria terrorista']),
            ('amia_case_move', 2, ['juicio en ausencia', 'trial in absentia', 'condena amia', 'amia verdict',
                                   'causa amia']),
        ],
    },
}

VECTORS = {
    'governance': {'name': 'Governance & the Street', 'plain': 'politics and protest',
                   'actors': ['presidency', 'congress_street']},
    'economy': {'name': 'Economy & the Peso', 'plain': 'the economy and the peso', 'actors': ['economy']},
    'us_alignment': {'name': 'US Alignment', 'plain': 'US-Argentina relations', 'actors': ['us_argentina']},
    'china_alignment': {'name': 'China Alignment', 'plain': 'China-Argentina relations', 'actors': ['china_argentina']},
    'south_atlantic': {'name': 'South Atlantic & Antarctic', 'plain': 'the Falklands and the South Atlantic',
                       'actors': ['uk_falklands']},
    'security': {'name': 'Security: Iran & Hizballah', 'plain': 'terrorism and the Tri-Border Area',
                 'actors': ['security_iran']},
}

RED_LINES = [
    {'id': 'controls_back', 'label': 'Capital controls (the "cepo") reimposed', 'tripwires': ['capital_controls_return'],
     'why': 'Lifting the cepo in 2025 was the programme\'s signature. Bringing it back would mean the peso '
            'could not be defended -- the classic Argentine crisis signal.'},
    {'id': 'default', 'label': 'A missed bond payment / default', 'tripwires': ['default'],
     'why': 'Argentina has defaulted nine times. About US$25bn of debt payments fall due in 2027, an election year.'},
    {'id': 'attack', 'label': 'A terror attack or confirmed plot in Argentina', 'tripwires': ['terror_attack', 'terror_plot'],
     'why': 'Argentina suffered the hemisphere\'s two deadliest Iran-linked bombings (1992, 1994). A plot needs '
            'two separate outlets before it counts.'},
    {'id': 'south_atlantic', 'label': 'A military incident in the South Atlantic', 'tripwires': ['south_atlantic_incident'],
     'why': 'No one serious expects an invasion; an incident would show the dispute has moved from words to ships.'},
    {'id': 'siege', 'label': 'A state of siege declared', 'tripwires': ['state_of_siege'],
     'why': 'The last state of siege (December 2001) came with the collapse of the De la Rúa government.'},
]
GREEN_LINES = [
    {'id': 'imf_ok', 'label': 'IMF review passed / disbursement', 'tripwires': ['imf_review_passed'],
     'why': 'Each passed review keeps the IMF money flowing and the programme credible.'},
]

MEANINGS = {
    'economy': {
        'plain': ('Milei\'s shock programme cut monthly inflation from about 25% (Dec 2023) to around 2%. The '
                  'peso trades in a managed band; reserves are thin and about US$25bn of debt falls due in 2027.'),
        'regional': ('Argentina is the IMF\'s largest debtor and has two backstops: a US$20bn US Treasury swap and '
                     'a Chinese yuan swap. Which one it draws on is a political choice.'),
        'economy': 'A peso run shows up first in the "blue" dollar and bond prices, then in prices in shops.',
        'not_implied': 'Economic news volume in Argentina is the baseline, not a crisis.',
    },
    'politics': {
        'plain': ('Javier Milei, a libertarian, has been president since December 2023. His party won the October '
                  '2025 midterms but lacks a majority; the next presidential election is October 2027.'),
        'not_implied': 'Protest and veto fights are normal Argentine politics, not instability.',
    },
    'us_argentina': {
        'plain': ('Milei is Washington\'s closest ally in South America. The US Treasury\'s US$20bn swap (Oct 2025) '
                  'steadied the peso before the midterms; a US-backed naval base is planned at Ushuaia.'),
        'global': ('Washington wants Argentina to limit China\'s footprint -- the space station, ports, lithium and the swap.'),
        'not_implied': 'Warm words from Washington are not a change in who buys Argentina\'s exports.',
    },
    'china_argentina': {
        'plain': ('China operates a deep-space station in Neuquén (since 2015, run by an agency under its military), '
                  'holds a yuan swap with the central bank, invests in lithium and buys most of Argentina\'s unprocessed soybeans.'),
        'global': ('Argentina joined the Belt and Road in 2022 and was invited into BRICS in 2024 -- Milei said no to '
                   'BRICS but kept the swap. Chinese fishing fleets work the edge of Argentine waters ("Mile 201").'),
        'not_implied': 'Trade with China is not a political realignment.',
    },
    'falklands': {
        'plain': ('Argentina claims the Falklands (Malvinas), which Britain has held since 1833 and retook in the '
                  '1982 war. About 3,500 islanders; a British garrison at Mount Pleasant; the Sea Lion oil field planned for ~2028.'),
        'global': ('The islands and South Georgia anchor Britain\'s Antarctic claim, and Ushuaia is the closest port to '
                   'Antarctica -- the dispute is about the South Atlantic gateway and the minerals of the 2040s, not '
                   'just 3,500 islanders. In Aug-Sep 2026 President Trump declined to say whether the US would back the UK.'),
        'not_implied': 'Sovereignty speeches happen every year (April 2, June 10); they are not escalation.',
    },
    'security': {
        'plain': ('Argentina suffered the 1992 Israeli embassy bombing (29 killed) and the 1994 AMIA bombing (85 '
                  'killed); its courts hold Iran responsible and Hizballah as the executor. It has Latin America\'s '
                  'largest Jewish community and the region\'s most pro-Israel president.'),
        'global': ('That makes Argentina the place where Middle East conflict is most likely to reach the Americas. '
                   'The Tri-Border Area (Puerto Iguazú) is the hemisphere\'s best-known Hizballah finance hub.'),
        'not_implied': ('AMIA anniversaries and court news are background, not threat. The local effect of the '
                        'Tri-Border networks is crime and money; attack risk needs 2+ outlets reporting a plot.'),
    },
}

TRIPWIRE_PLAIN = {
    'cabinet_crisis': ('a cabinet crisis', 'governance'),
    'impeachment_move': ('an impeachment move against Milei', 'governance'),
    'state_of_siege': ('a state of siege', 'governance'),
    'general_strike': ('a general strike', 'governance'),
    'veto_overridden': ('Congress overriding a presidential veto', 'governance'),
    'deadly_protest': ('a death or serious injuries at a protest', 'kinetic'),
    'capital_controls_return': ('capital controls (the cepo) coming back', 'economic'),
    'default': ('a missed bond payment', 'economic'),
    'peso_run': ('a run on the peso', 'economic'),
    'caputo_exit': ('the economy minister leaving', 'economic'),
    'imf_breakdown': ('the IMF programme breaking down', 'economic'),
    'imf_review_passed': ('an IMF review passed', 'economic'),
    'us_ushuaia_base': ('a step on the US-backed Ushuaia naval base', 'diplomatic'),
    'us_trade_deal': ('a US-Argentina trade agreement step', 'economic'),
    'us_swap_drawn': ('a draw on the US Treasury swap', 'economic'),
    'us_presses_on_china': ('Washington pressing Argentina to limit China', 'diplomatic'),
    'space_station_row': ('a row over China\'s Neuquén space station', 'diplomatic'),
    'chinese_port_or_base': ('a Chinese port or base project', 'diplomatic'),
    'fishing_clash': ('a clash with a Chinese fishing vessel', 'kinetic'),
    'china_swap_move': ('a change to the China swap', 'economic'),
    'south_atlantic_incident': ('a military incident in the South Atlantic', 'kinetic'),
    'sovereignty_push': ('a new Argentine move on Falklands sovereignty', 'diplomatic'),
    'us_falklands_shift': ('a shift in the US position on the Falklands', 'diplomatic'),
    'sea_lion_milestone': ('a Sea Lion oil-field milestone', 'economic'),
    'terror_attack': ('a terror attack in Argentina', 'kinetic'),
    'terror_plot': ('a foiled terror plot in Argentina', 'kinetic'),
    'hizballah_arrest': ('an arrest linked to Hizballah', 'kinetic'),
    'terror_designation': ('a new terrorist designation', 'diplomatic'),
    'amia_case_move': ('a step in the AMIA case', 'diplomatic'),
}

TRIPWIRE_MEANING = {k: v for k, v in (
    ('cabinet_crisis', 'politics'), ('impeachment_move', 'politics'), ('state_of_siege', 'politics'),
    ('general_strike', 'politics'), ('veto_overridden', 'politics'), ('deadly_protest', 'politics'),
    ('capital_controls_return', 'economy'), ('default', 'economy'), ('peso_run', 'economy'),
    ('caputo_exit', 'economy'), ('imf_breakdown', 'economy'), ('imf_review_passed', 'economy'),
    ('us_ushuaia_base', 'us_argentina'), ('us_trade_deal', 'us_argentina'), ('us_swap_drawn', 'economy'),
    ('us_presses_on_china', 'us_argentina'), ('space_station_row', 'china_argentina'),
    ('chinese_port_or_base', 'china_argentina'), ('fishing_clash', 'china_argentina'),
    ('china_swap_move', 'china_argentina'), ('south_atlantic_incident', 'falklands'),
    ('sovereignty_push', 'falklands'), ('us_falklands_shift', 'falklands'), ('sea_lion_milestone', 'falklands'),
    ('terror_attack', 'security'), ('terror_plot', 'security'), ('hizballah_arrest', 'security'),
    ('terror_designation', 'security'), ('amia_case_move', 'security'))}

SO_WHAT_RULES = [
    {'tripwires': ['terror_attack', 'terror_plot'], 'weight': 7.0,
     'confirmed': ('A terror attack or foiled plot in Argentina is confirmed by 2+ outlets. Read it against the '
                   'Middle East: Argentina is the hemisphere\'s most exposed Israeli and Jewish target, and the '
                   'Iran-Israel conflict sets the tempo. Watch for Iran or Hizballah attribution.'),
     'single': ('One outlet reports a terror plot in Argentina; not corroborated. Plot stories are often '
                'overstated in early reporting -- wait for a second outlet.')},
    {'tripwires': ['capital_controls_return', 'default'], 'weight': 7.0,
     'confirmed': ('A core Argentine crisis signal is confirmed: capital controls back or a missed payment. That '
                   'ends the Milei programme as designed and reopens the question of who rescues Argentina -- '
                   'Washington or Beijing.'),
     'single': 'One outlet reports capital controls or a missed payment; not yet corroborated.'},
    {'tripwires': ['peso_run', 'caputo_exit', 'imf_breakdown'], 'weight': 5.6,
     'confirmed': ('Economic stress is confirmed by 2+ outlets. Milei expects any run on the peso to come during '
                   'the 2027 campaign; watch whether the US Treasury swap is drawn.')},
    {'tripwires': ['south_atlantic_incident', 'us_falklands_shift', 'sovereignty_push'], 'weight': 5.0,
     'confirmed': ('The Falklands file moved, confirmed by 2+ outlets. The real variable is the US guarantee to '
                   'Britain -- and what that says about US commitments to allies generally.')},
    {'tripwires': ['chinese_port_or_base', 'space_station_row', 'fishing_clash'], 'weight': 4.8,
     'confirmed': ('A China-Argentina friction point is confirmed. Washington reads every Chinese footprint near '
                   'the Antarctic gateway as strategic; Buenos Aires reads it as a customer and a creditor.')},
    {'tripwires': ['us_ushuaia_base', 'us_trade_deal', 'us_presses_on_china'], 'weight': 4.2,
     'confirmed': ('A US-Argentina step is confirmed. Watch Beijing\'s answer on the swap and soy purchases: '
                   'Milei pays for US alignment in Chinese goodwill.')},
    {'tripwires': ['general_strike', 'deadly_protest'], 'weight': 4.4,
     'confirmed': ('Street pressure is confirmed: a general strike or a deadly protest. Strikes are routine '
                   'under Milei; deaths are not.')},
    {'tripwires': ['hizballah_arrest'], 'weight': 4.4,
     'confirmed': ('A Hizballah-linked arrest is confirmed. The local effect is crime and money; the So What '
                   'is money flowing to Lebanon.')},
]
VECTOR_SO_WHAT = {
    'economy': (3.4, 'Economic reporting is busier than usual. In Argentina the peso is the first thing to watch: '
                     'stress shows in the dollar rate before it shows in politics.'),
    'south_atlantic': (3.2, 'Falklands and South Atlantic reporting is up. ' + MEANINGS['falklands']['global']),
    'security': (3.2, 'Security reporting (Iran, Hizballah, AMIA) is up. ' + MEANINGS['security']['not_implied']),
    'china_alignment': (3.0, 'China-Argentina reporting is busier than usual -- watch the swap, the space station and lithium.'),
}
STANDING_SO_WHAT = [
    'The unasked question: when Argentina next needs a rescue -- most likely in the 2027 election year -- does '
    'it call Washington or Beijing? Every economic, US and China signal here is read against that.',
    'The Middle East connection: Argentina is where Iran\'s conflict with Israel has already struck the Americas '
    'twice. A spike in Iran-Israel tension raises the stakes of every security signal on this page.',
]

DRIFT_PROFILE = {
    'inroad_actor': 'china_argentina', 'counter_actor': 'us_argentina',
    'inroad_tripwires': ('chinese_port_or_base', 'china_swap_move', 'space_station_row'),
    'counter_tripwires': ('us_ushuaia_base', 'us_trade_deal', 'us_presses_on_china', 'us_swap_drawn'),
    'so_what': {
        'US-anchored': ('Milei\'s Argentina reads US-anchored this cycle: China is present as customer and creditor, '
                        'not as a political pull.'),
        'Contested': ('China and the US are both active in Argentina this cycle. Milei talks like a US ally and '
                      'finances himself like a hedger -- the question is which patron sets conditions first.'),
        'Drifting': ('China\'s moves in Argentina are outpacing Washington\'s this cycle, through the swap, the '
                     'space station and commodities -- even under the region\'s most pro-US president.'),
        'Realigning': ('Sustained Chinese moves with little US push-back are consistent with Argentina sliding back '
                       'toward Beijing\'s orbit.'),
    },
    'leading_indicators': [
        'The swap lines -- which one Argentina draws on when the peso is under pressure',
        'Ushuaia -- the US-backed naval base vs any Chinese port interest',
        'Neuquén -- inspections or new limits on China\'s space station',
        'Lithium -- who wins new concessions in the north',
        'The 2027 campaign -- a Peronist return would reopen the China file',
    ],
}


def _hizballah_read(redis_get):
    return redis_get('hizballah_latam:read:argentina') or {}


def _hizballah_signal(t, ctx):
    r = ctx['extras'].get('hizballah') or {}
    lvl = int(r.get('level') or 0)
    if lvl < 2:
        return []
    lane = r.get('lane', '')
    return [t.sig('hizballah_latam', min(lvl, 3) if lane != 'corroborated' else lvl,
                  'Argentina: Hizballah Latin America module reads L%d (%s)' % (lvl, lane.replace('_', ' ')),
                  (r.get('sentence') or '') + ' ' + MEANINGS['security']['not_implied'], 'kinetic', 'security',
                  actor='security_iran', kind='crosstheater',
                  sources=[{'title': i.get('title'), 'url': i.get('url'), 'source': i.get('source')}
                           for i in (r.get('items') or [])[:3]])]


CONFIG = {
    'slug': 'argentina', 'name': 'Argentina', 'flag': '🇦🇷', 'version': VERSION, 'facts_as_of': '2026-11-04',
    'actors': ACTORS, 'vectors': VECTORS,
    'rss_feeds': {
        'la_nacion': {'url': 'https://www.lanacion.com.ar/arc/outboundfeeds/rss/?outputType=xml',
                      'name': 'La Nación', 'language': 'es', 'max': 60},
        'infobae': {'url': 'https://www.infobae.com/arc/outboundfeeds/rss/?outputType=xml',
                    'name': 'Infobae', 'language': 'es', 'max': 60},
        'ba_times': {'url': 'https://www.batimes.com.ar/feed', 'name': 'Buenos Aires Times', 'language': 'en'},
        'mercopress': {'url': 'https://en.mercopress.com/rss', 'name': 'MercoPress', 'language': 'en'},
    },
    'google_queries': [
        ('Milei', 'es-419', 'AR'), ('Caputo dólar reservas', 'es-419', 'AR'), ('FMI Argentina', 'es-419', 'AR'),
        ('Malvinas', 'es-419', 'AR'), ('China Argentina swap OR Neuquén OR litio', 'es-419', 'AR'),
        ('AMIA OR Hezbollah Argentina', 'es-419', 'AR'), ('CGT paro', 'es-419', 'AR'),
        ('Argentina Milei', 'en-US', 'US'), ('Falklands', 'en-GB', 'GB'),
    ],
    'gdelt_en': ['Argentina Milei', 'Argentina peso IMF', 'Falklands Argentina'],
    'gdelt_es': ['Milei gobierno', 'Malvinas soberanía', 'Argentina China swap'],
    'newsapi_queries': ['Milei', 'Argentina peso', 'Falklands'],
    'brave_queries': ['Argentina Milei news', 'Argentina peso reserves'],
    'scrub': [],
    'context_terms': ('argentina', 'argentino', 'argentina', 'argentinos', 'argentinas', 'argentine', 'milei',
                      'buenos aires', 'casa rosada', 'caputo', 'bcra', 'malvinas', 'falklands', 'ushuaia',
                      'tierra del fuego', 'patagonia argentina', 'neuquen', 'vaca muerta', 'ypf', 'tucuman',
                      'jujuy', 'puerto iguazu', 'kicillof', 'amia', 'la libertad avanza', 'merval', 'indec',
                      'adorni', 'mar del plata', 'bahia blanca', 'chubut', 'mount pleasant', 'conurbano',
                      'peronismo', 'kirchnerismo', 'gendarmeria'),
    'own_outlets': ('la nacion', 'lanacion.com.ar', 'clarin', 'pagina 12', 'pagina12', 'ambito', 'perfil',
                    'buenos aires times', 'batimes', 'el cronista', 'tn.com.ar', 'todo noticias'),
    'own_tld': '.com.ar/',
    'foreign_markers': ('mexico', 'sheinbaum', 'colombia', 'venezuela', 'peru', 'chile', 'kast', 'brasil', 'brazil',
                        'lula', 'uruguay', 'paraguay', 'bolivia', 'ecuador', 'cuba', 'espana', 'spain'),
    'exclusions': {
        'terror_attack': ('aniversario', 'anniversary', '1994', '1992', 'juicio', 'trial', 'causa amia', 'homenaje',
                          'acto', 'recuerdo', 'conmemoracion'),
        'terror_plot': ('aniversario', 'anniversary', '1994', '1992', 'pelicula', 'serie', 'novela'),
        'general_strike': ('convoca', 'convocara', 'anuncia', 'amenaza', 'evalua', 'calls for', 'threatens',
                           'analiza', 'descarta'),
        'state_of_siege': ('1989', '2001', 'aniversario', 'anniversary'),
        'default': ('evitar el default', 'avoid default', 'sin default', 'riesgo de default', 'default risk'),
        'sovereignty_push': ('2 de abril', 'april 2', '10 de junio', 'june 10', 'aniversario', 'anniversary'),
        'sea_lion_milestone': ('lobo marino', 'sea lions'),
        'peso_run': ('descarta', 'rules out', 'sin corrida', 'no habra corrida'),
    },
    'red_lines': RED_LINES, 'green_lines': GREEN_LINES,
    'meanings': MEANINGS, 'tripwire_plain': TRIPWIRE_PLAIN, 'tripwire_meaning': TRIPWIRE_MEANING,
    'actor_meaning': {'presidency': 'politics', 'congress_street': 'politics', 'economy': 'economy',
                      'us_argentina': 'us_argentina', 'china_argentina': 'china_argentina',
                      'uk_falklands': 'falklands', 'security_iran': 'security'},
    'vector_pressure': {'governance': 'governance', 'economy': 'economic', 'us_alignment': 'diplomatic',
                        'china_alignment': 'diplomatic', 'south_atlantic': 'diplomatic', 'security': 'kinetic'},
    'so_what_rules': SO_WHAT_RULES, 'vector_so_what': VECTOR_SO_WHAT, 'standing_so_what': STANDING_SO_WHAT,
    'quiet_so_what': ('Argentina reads quiet this cycle. What would change that: capital controls reimposed or a '
                      'missed payment, a run on the peso, a terror plot confirmed by 2+ outlets, or a military '
                      'incident in the South Atlantic.'),
    'background': MEANINGS['politics']['plain'],
    'drift_profile': DRIFT_PROFILE, 'drift_meaning': 'china_argentina',
    'spokes': [
        ('us', 'us_argentina', 'hemispheric_partner',
         'Milei is Washington\'s closest South American ally: a US$20bn Treasury swap (Oct 2025), a planned '
         'US-backed naval base at Ushuaia, and US pressure to limit China.'),
        ('china', 'china_argentina', 'commodity_customer',
         'China holds a yuan swap with Argentina\'s central bank, runs a deep-space station in Neuquén and buys most '
         'of its unprocessed soybeans.'),
        ('iran', 'security_iran', 'target',
         'Argentina\'s courts hold Iran responsible for the 1994 AMIA bombing; Hizballah finance runs through the '
         'Tri-Border Area; Milei is the region\'s most pro-Israel president.'),
    ],
    'hub_names': {'us': 'US', 'china': 'China', 'iran': 'Iran'},
    'fingerprints': {'argentina_financial_stress': ['capital_controls_return', 'default', 'peso_run'],
                     'argentina_terror_signal': ['terror_attack', 'terror_plot', 'hizballah_arrest'],
                     'argentina_south_atlantic': ['south_atlantic_incident', 'us_falklands_shift']},
    'extra_reads': {'hizballah': _hizballah_read},
    'extra_signals': [_hizballah_signal],
}

tracker = CountryRhetoricTracker(CONFIG)


def scan_argentina_rhetoric(force=False):
    return tracker.scan(force=force)


def register_argentina_rhetoric_endpoints(app, force_gate=None, start_background=True):
    tracker.register(app, force_gate=force_gate, start_background=start_background, warmup_seconds=260)
