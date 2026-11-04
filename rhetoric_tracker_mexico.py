"""
rhetoric_tracker_mexico.py -- Mexico Rhetoric & Pressure Tracker v1.0.0
Asifah Analytics -- WHA backend -- built Nov 4 2026

Runs on the shared engine (wha_rhetoric_engine.py). This file is the CONFIG:
who we watch, which words count, what a red line is, and what it all means
in plain language.

THE SO WHAT (why Mexico matters)
  Local:    can the state hold ground against the cartels? The Sinaloa
            civil war (Chapitos vs Mayos) has run in Culiacán since Sep 2024;
            CJNG fights for Michoacán, Jalisco and Guanajuato.
  Regional: the front door for migration and drugs into the US, and the
            US's largest trading partner.
  Global:   the US designated six Mexican cartels as foreign terrorist
            organisations (Feb 2025) -- a legal hook for US military action on
            Mexican soil. Whether that hook is ever used is THE unasked
            question, and Mexico's answer (cooperate / resist / suspend) sets
            the tone for the hemisphere.
  For Americans: car and grocery prices (trade), fentanyl deaths (drugs),
            remittances and the border.

ACTORS (7) -> VECTORS (5)
  governance      presidency, security_cabinet
  cartel_violence cartels
  us_pressure     us_security, us_trade
  border          migration_border
  china           china_mexico

RED LINES (BREACHED only when 2+ outlets report it as fact)
  US strike on Mexican soil · US ground operation in Mexico · Mexico suspends
  security cooperation / expels US agents · notice of withdrawal from USMCA ·
  killing of a senior official.
GREEN LINES (cooperation; never raise the level)
  cartel prisoners sent to the US · new security / trade arrangements.

Dated facts (re-verify on the 45-day cycle, next ~Dec 19 2026):
  * FTO designations: Feb 2025 (Sinaloa, CJNG + four others).
  * CIA officers in a Chihuahua drug-lab raid (Apr 2026); ex-state prosecutor
    charged with treason Oct 21 2026.
  * ~500 US troops sent to the Tamaulipas border after an alleged shooting
    (late Sep 2026); Mexico's own deployment = "Operation Mirror".
  * NYT (Oct 24 2026): US memo pressing for US personnel to accompany
    operations in Mexico; Sheinbaum: joint operations are not allowed by
    Mexican law.
  * USMCA joint review July 1 2026; not extended -> the pact stays in force
    to 2036 with yearly reviews. US tariffs on Mexican steel, aluminium and
    vehicles remain the main irritant.

COPYRIGHT (c) 2025-2026 Asifah Analytics. All rights reserved.
"""

from wha_rhetoric_engine import CountryRhetoricTracker

VERSION = '1.0.0'

ACTORS = {
    'presidency': {
        'name': 'Presidency (Sheinbaum)', 'flag': '🇲🇽', 'icon': '🏛️', 'vector': 'governance',
        'role': 'Claudia Sheinbaum (since Oct 2024), the daily "mañanera" press conference, Morena',
        'baseline': 16,
        'keywords': ['sheinbaum', 'claudia sheinbaum', 'mananera', 'conferencia matutina',
                     'palacio nacional', 'presidenta de mexico', 'mexican president', 'mexico president',
                     'morena', 'gobierno de mexico', 'mexican government', 'reforma electoral',
                     'reforma judicial', 'poder judicial', 'suprema corte', 'amlo', 'lopez obrador'],
        'tripwires': [
            ('constitutional_crisis', 3, ['crisis constitucional', 'constitutional crisis mexico']),
        ],
    },
    'security_cabinet': {
        'name': 'Security Cabinet', 'flag': '🇲🇽', 'icon': '🛡️', 'vector': 'governance',
        'role': 'García Harfuch (security), Defence, Navy, National Guard, the federal prosecutor (FGR)',
        'baseline': 12,
        'keywords': ['garcia harfuch', 'harfuch', 'sspc', 'secretaria de seguridad', 'sedena', 'defensa nacional',
                     'semar', 'marina armada', 'guardia nacional', 'national guard mexico', 'fgr',
                     'fiscalia general', 'ernestina godoy', 'gabinete de seguridad', 'security cabinet',
                     'plan michoacan', 'operativo', 'mexican army', 'mexican navy', 'ejercito mexicano'],
        'tripwires': [
            ('senior_official_killed', 4, ['asesinan a gobernador', 'gobernador asesinado', 'asesinan al senador',
                                           'senador asesinado', 'asesinan a diputado federal',
                                           'secretario de seguridad asesinado', 'governor assassinated',
                                           'governor killed', 'senator killed', 'cabinet minister killed']),
            ('mayor_killed', 3, ['asesinan al alcalde', 'asesinan a alcalde', 'alcalde asesinado',
                                 'asesinan a la alcaldesa', 'alcaldesa asesinada', 'mayor killed', 'mayor assassinated',
                                 'mayor shot dead']),
            ('security_chief_out', 3, ['renuncia garcia harfuch', 'garcia harfuch renuncia', 'harfuch resigns',
                                       'destituyen a garcia harfuch']),
        ],
    },
    'cartels': {
        'name': 'Cartels & Organised Crime', 'flag': '💀', 'icon': '🔫', 'vector': 'cartel_violence',
        'role': 'Sinaloa (Chapitos vs Mayos), CJNG, Gulf, Northeast, La Familia Michoacana; fentanyl labs',
        'baseline': 20,
        'keywords': ['cartel de sinaloa', 'sinaloa cartel', 'cjng', 'cartel jalisco', 'jalisco nueva generacion',
                     'chapitos', 'los chapitos', 'mayiza', 'mayo zambada', 'el mencho', 'cartel del golfo',
                     'cartel del noreste', 'familia michoacana', 'carteles unidos', 'narco', 'narcotrafico',
                     'crimen organizado', 'organized crime mexico', 'fentanilo', 'fentanyl', 'narcolaboratorio',
                     'drug lab', 'culiacan', 'huachicol', 'extorsion', 'cobro de piso', 'desaparecidos',
                     'fosa clandestina', 'cartel violence', 'cartel war'],
        'tripwires': [
            ('massacre', 3, ['masacre', 'massacre', 'matanza']),
            ('narco_blockades', 3, ['narcobloqueos', 'narcobloqueo', 'quema de vehiculos', 'cartel blockades',
                                    'torched vehicles']),
            ('attack_on_forces', 3, ['emboscada a militares', 'emboscada a la guardia nacional', 'ambush soldiers',
                                     'soldiers killed', 'militares asesinados', 'policias asesinados',
                                     'ataque con drones', 'drone attack']),
            ('kingpin_removed', 3, ['capturan a el mencho', 'el mencho detenido', 'el mencho abatido',
                                    'mencho captured', 'mencho killed', 'detienen a ivan archivaldo',
                                    'ivan archivaldo detenido', 'ivan archivaldo guzman arrested',
                                    'capturan a jesus alfredo guzman', 'cae el lider del cartel']),
        ],
    },
    'us_security': {
        'name': 'US-Mexico Security', 'flag': '🇺🇸', 'icon': '🦅', 'vector': 'us_pressure',
        'role': 'Terrorist designations, drones and the CIA, US troops at the border, transfers of prisoners',
        'baseline': 12,
        'keywords': ['terrorist organization', 'organizacion terrorista', 'narcoterrorismo', 'narcoterrorism',
                     'foreign terrorist', 'fto', 'cia', 'dea', 'drones estadounidenses', 'us drones',
                     'ronald johnson', 'embajador johnson', 'intervencion', 'intervention', 'soberania',
                     'sovereignty', 'operacion espejo', 'operation mirror', 'us troops', 'tropas estadounidenses',
                     'military action against cartels', 'strikes on cartels', 'ataques contra carteles',
                     'extradicion', 'extradited', 'security cooperation', 'cooperacion en seguridad',
                     'joint operations', 'operaciones conjuntas', 'hegseth', 'pentagon', 'pentagono'],
        'tripwires': [
            ('us_strike_mexico', 4, ['us strike in mexico', 'us strikes in mexico', 'us drone strike in mexico',
                                     'us airstrike in mexico', 'strike on mexican soil', 'strikes on mexican soil',
                                     'ataque de estados unidos en territorio mexicano',
                                     'bombardeo estadounidense en mexico', 'ataque con dron estadounidense',
                                     'us military strike on mexican']),
            ('us_ground_operation', 4, ['us troops in mexico', 'us soldiers in mexico', 'us special forces in mexico',
                                        'tropas estadounidenses en mexico', 'tropas de estados unidos en mexico',
                                        'operacion militar estadounidense en mexico', 'us raid in mexico']),
            ('cooperation_suspended', 3, ['suspende la cooperacion en seguridad', 'suspende cooperacion de seguridad',
                                          'suspends security cooperation', 'expulsa a agentes', 'expels us agents',
                                          'expels dea', 'expulsa a la dea']),
            ('foreign_agents_scandal', 2, ['agentes de la cia', 'cia agents', 'cia officers', 'agentes extranjeros',
                                           'traicion a la patria', 'treason']),
            ('new_terror_designation', 2, ['designa como organizacion terrorista', 'designated as a foreign terrorist',
                                           'designates as foreign terrorist']),
            # green (cooperation) -- never raises the level
            ('prisoner_transfer', 2, ['reos a estados unidos', 'narcos a estados unidos', 'capos a estados unidos',
                                      'narcotraficantes a estados unidos', 'traslado de reos', 'sends cartel',
                                      'cartel figures to the us', 'cartel members to the us',
                                      'cartel leaders to the united states', 'cartel bosses to the us',
                                      'extraditado a estados unidos', 'extradited to the united states']),
            ('security_arrangement', 1, ['acuerdo de seguridad', 'security agreement', 'grupo de implementacion',
                                         'security implementation group', 'entendimiento de seguridad']),
        ],
    },
    'us_trade': {
        'name': 'US-Mexico Trade', 'flag': '🇺🇸', 'icon': '🚚', 'vector': 'us_pressure',
        'role': 'USMCA (T-MEC) reviews, US tariffs on steel, aluminium and cars, Ebrard-Greer talks, remittances',
        'baseline': 12,
        'keywords': ['usmca', 't-mec', 'tmec', 'aranceles', 'tariffs', 'tariff', 'ebrard', 'greer',
                     'seccion 232', 'section 232', 'acero', 'steel', 'autos', 'automotriz', 'nearshoring',
                     'remesas', 'remittances', 'exportaciones', 'exports to the us', 'trade deficit',
                     'deficit comercial', 'peso mexicano', 'mexican peso', 'banxico', 'pemex'],
        'tripwires': [
            ('usmca_withdrawal', 4, ['withdraw from usmca', 'withdrawal from usmca', 'terminate usmca',
                                     'notice of withdrawal', 'retiro del t-mec', 'salir del t-mec',
                                     'abandona el t-mec', 'aviso de retiro']),
            ('new_us_tariffs', 3, ['new tariffs on mexico', 'new tariffs on mexican', 'imposes tariffs on mexico',
                                   'raises tariffs on mexico', 'nuevos aranceles a mexico', 'impone aranceles a mexico',
                                   'aumenta aranceles a mexico']),
            ('trade_relief', 1, ['tariff relief', 'exenta de aranceles', 'elimina aranceles', 'lifts tariffs on mexico',
                                 'acuerdo comercial con estados unidos', 'trade deal with mexico']),
        ],
    },
    'migration_border': {
        'name': 'Migration & the Border', 'flag': '🛂', 'icon': '🧱', 'vector': 'border',
        'role': 'Deportations, the northern border, migrant routes through Mexico, border incidents',
        'baseline': 10,
        'keywords': ['migrantes', 'migrants', 'migracion', 'migration', 'deportados', 'deportations',
                     'deportaciones', 'frontera norte', 'us-mexico border', 'southern border', 'border patrol',
                     'cbp', 'ice', 'caravana', 'caravan', 'tijuana', 'ciudad juarez', 'reynosa', 'matamoros',
                     'nuevo laredo', 'tapachula', 'muro fronterizo', 'border wall', 'cruce fronterizo'],
        'tripwires': [
            ('border_incident', 3, ['disparos desde mexico', 'shots fired from mexico', 'border shooting',
                                    'tiroteo en la frontera', 'cartel drone incursion', 'drones del cartel',
                                    'cartel drones']),
            ('border_closure', 3, ['cierre de la frontera', 'cierra la frontera', 'closes the border with mexico',
                                   'border closed to', 'shuts the border']),
            ('mass_deportation_surge', 2, ['deportacion masiva', 'mass deportation', 'vuelos de deportacion',
                                           'deportation flights']),
        ],
    },
    'china_mexico': {
        'name': 'China-Mexico', 'flag': '🇨🇳', 'icon': '🐉', 'vector': 'china',
        'role': 'Chinese imports and investment, goods routed through Mexico, Mexico\'s tariffs on Asian imports',
        'baseline': 6,
        'keywords': ['china mexico', 'chinese imports', 'importaciones chinas', 'productos chinos',
                     'inversion china', 'chinese investment', 'byd', 'triangulacion', 'transshipment',
                     'aranceles a china', 'tariffs on china', 'empresas chinas', 'chinese companies',
                     'importaciones asiaticas', 'asian imports'],
        'tripwires': [
            ('tariffs_on_china', 2, ['aranceles a china', 'aranceles a productos chinos', 'tariffs on chinese imports',
                                     'aranceles a importaciones asiaticas', 'tariffs on asian imports']),
            ('chinese_project_blocked', 2, ['byd cancela', 'byd pauses', 'frena inversion china',
                                            'blocks chinese investment', 'rechaza inversion china']),
        ],
    },
}

VECTORS = {
    'governance': {'name': 'Governance & Security State', 'plain': 'government and the security forces',
                   'actors': ['presidency', 'security_cabinet']},
    'cartel_violence': {'name': 'Cartel Violence', 'plain': 'cartel violence', 'actors': ['cartels']},
    'us_pressure': {'name': 'US Pressure (security + trade)', 'plain': 'pressure from Washington',
                    'actors': ['us_security', 'us_trade']},
    'border': {'name': 'Border & Migration', 'plain': 'the border and migration', 'actors': ['migration_border']},
    'china': {'name': 'China Channel', 'plain': 'China-Mexico trade', 'actors': ['china_mexico']},
}

RED_LINES = [
    {'id': 'us_strike', 'label': 'A US strike on Mexican soil', 'tripwires': ['us_strike_mexico'],
     'why': 'The cartel terrorist designations give Washington a legal hook; using it on Mexican soil would '
            'be the first US military action in Mexico in over a century and would force Sheinbaum to choose '
            'between cooperation and rupture.'},
    {'id': 'us_ground_op', 'label': 'US troops operating inside Mexico', 'tripwires': ['us_ground_operation'],
     'why': 'Mexican law bars foreign agents from arrests or searches; the US has pressed for its personnel '
            'to accompany operations (reported Oct 2026).'},
    {'id': 'coop_suspended', 'label': 'Mexico suspends security cooperation or expels US agents',
     'tripwires': ['cooperation_suspended'],
     'why': 'Intelligence sharing and prisoner transfers are what has kept unilateral US action off the table.'},
    {'id': 'usmca_exit', 'label': 'Formal notice to leave USMCA', 'tripwires': ['usmca_withdrawal'],
     'why': 'About four-fifths of Mexico\'s exports go to the US; the pact is the floor under that trade.'},
    {'id': 'senior_killed', 'label': 'A senior official assassinated', 'tripwires': ['senior_official_killed'],
     'why': 'A governor, senator or cabinet-level killing would mark cartels taking on the state directly.'},
]
GREEN_LINES = [
    {'id': 'transfers', 'label': 'Cartel prisoners sent to the US', 'tripwires': ['prisoner_transfer'],
     'why': 'Mexico sent 29 cartel figures to the US in Feb 2025 and 26 in Aug 2025: cooperation that buys room '
            'against unilateral US action.'},
    {'id': 'arrangement', 'label': 'A new security or trade arrangement',
     'tripwires': ['security_arrangement', 'trade_relief'],
     'why': 'Deals and working groups are how both sides lower the temperature.'},
]

MEANINGS = {
    'us_strike': {
        'plain': ('The US designated six Mexican cartels, including Sinaloa and CJNG, as foreign terrorist '
                  'organisations in February 2025, and has struck alleged drug boats at sea.'),
        'global': ('A strike on Mexican soil would test the US-Mexico relationship -- the US\'s largest trade '
                   'partnership -- and set a precedent for US force in the hemisphere.'),
        'not_implied': 'Threats, plans and leaks are not strikes; only a strike reported as fact by 2+ outlets is.',
    },
    'sovereignty': {
        'plain': ('Sheinbaum\'s line is "cooperation without subordination": intelligence sharing yes, '
                  'foreign troops or agents operating in Mexico no. Mexican law bars foreign agents from making arrests.'),
        'regional': ('In April 2026 CIA officers were found to have joined a Chihuahua drug-lab raid without '
                     'federal approval; a former state prosecutor was charged with treason in October.'),
        'not_implied': 'Sovereignty rhetoric is the normal register of the mañanera, not a rupture.',
    },
    'cartels': {
        'plain': ('Cartel violence kills tens of thousands a year. The Sinaloa cartel has been at war with itself '
                  '(Chapitos vs Mayos) in Culiacán since September 2024; CJNG is the most expansive group.'),
        'global': ('Fentanyl precursors from Asia are pressed into pills in Mexican labs and smuggled north; '
                   'that is why cartel news in Mexico becomes US policy within days.'),
        'not_implied': 'High cartel-news volume is the baseline in Mexico; it is not a new war.',
    },
    'trade': {
        'plain': ('Mexico is the US\'s largest trading partner; about four-fifths of Mexican exports go north. '
                  'US tariffs on Mexican steel, aluminium and vehicles remain.'),
        'global': ('Cars, auto parts, electronics, avocados and tomatoes cross the border every day; tariffs '
                   'show up in US prices within months.'),
        'economy': 'The peso and the Mexican stock market react first; US car and grocery prices follow.',
        'not_implied': 'Trade talk and threats are not new tariffs or a USMCA exit.',
    },
    'border': {
        'plain': ('Crossings at the US-Mexico border are far below 2023 levels; the pressure now runs through '
                  'deportations to Mexico and security incidents at the line.'),
        'not_implied': 'Border news is not a migration surge unless the numbers move.',
    },
    'china_mexico': {
        'plain': ('Washington\'s worry is Chinese goods and parts routed through Mexico to dodge US tariffs. '
                  'Mexico raised tariffs on many Asian imports from 2026 partly to answer that worry.'),
        'not_implied': 'Chinese trade with Mexico is not a political alignment with Beijing.',
    },
    'politics': {
        'plain': ('Claudia Sheinbaum (Morena) has governed since October 2024 with large majorities in Congress '
                  'and high approval; she answers questions live every weekday morning (the mañanera).'),
        'not_implied': 'Political news volume is not instability.',
    },
}

TRIPWIRE_PLAIN = {
    'constitutional_crisis': ('a constitutional crisis', 'governance'),
    'senior_official_killed': ('the killing of a senior official', 'kinetic'),
    'mayor_killed': ('the killing of a mayor', 'kinetic'),
    'security_chief_out': ('the security minister leaving office', 'governance'),
    'massacre': ('a massacre', 'kinetic'),
    'narco_blockades': ('cartel road blockades and burning vehicles', 'kinetic'),
    'attack_on_forces': ('an attack on soldiers or police', 'kinetic'),
    'kingpin_removed': ('the capture or killing of a top cartel leader', 'kinetic'),
    'us_strike_mexico': ('a US strike on Mexican soil', 'kinetic'),
    'us_ground_operation': ('US troops operating inside Mexico', 'kinetic'),
    'cooperation_suspended': ('Mexico suspending security cooperation or expelling US agents', 'diplomatic'),
    'foreign_agents_scandal': ('a row over US agents operating in Mexico', 'diplomatic'),
    'new_terror_designation': ('a new US terrorist designation of a Mexican group', 'diplomatic'),
    'prisoner_transfer': ('cartel prisoners handed to the US', 'diplomatic'),
    'security_arrangement': ('a new security arrangement', 'diplomatic'),
    'usmca_withdrawal': ('notice of withdrawal from USMCA', 'economic'),
    'new_us_tariffs': ('new US tariffs on Mexico', 'economic'),
    'trade_relief': ('tariff relief or a trade deal', 'economic'),
    'border_incident': ('a shooting or drone incursion at the border', 'kinetic'),
    'border_closure': ('a closure of the US-Mexico border', 'economic'),
    'mass_deportation_surge': ('a surge in deportations to Mexico', 'humanitarian'),
    'tariffs_on_china': ('Mexican tariffs on Chinese imports', 'economic'),
    'chinese_project_blocked': ('a Chinese investment in Mexico blocked or paused', 'economic'),
}

TRIPWIRE_MEANING = {
    'us_strike_mexico': 'us_strike', 'us_ground_operation': 'us_strike', 'new_terror_designation': 'us_strike',
    'cooperation_suspended': 'sovereignty', 'foreign_agents_scandal': 'sovereignty',
    'prisoner_transfer': 'sovereignty', 'security_arrangement': 'sovereignty',
    'massacre': 'cartels', 'narco_blockades': 'cartels', 'attack_on_forces': 'cartels',
    'kingpin_removed': 'cartels', 'senior_official_killed': 'cartels', 'mayor_killed': 'cartels',
    'usmca_withdrawal': 'trade', 'new_us_tariffs': 'trade', 'trade_relief': 'trade',
    'border_incident': 'border', 'border_closure': 'trade', 'mass_deportation_surge': 'border',
    'tariffs_on_china': 'china_mexico', 'chinese_project_blocked': 'china_mexico',
    'constitutional_crisis': 'politics', 'security_chief_out': 'politics',
}

SO_WHAT_RULES = [
    {'tripwires': ['us_strike_mexico', 'us_ground_operation'], 'weight': 7.0,
     'confirmed': ('US military action inside Mexico is confirmed by 2+ outlets. This is the line the cartel '
                   'terrorist designations made possible. Watch Sheinbaum\'s next mañanera: cooperation framed as '
                   'joint, a diplomatic protest, or a suspension of security cooperation. Watch the peso and USMCA '
                   'talk for the economic spill-over.'),
     'single': ('One outlet reports US military action inside Mexico; not corroborated. Leaks and plans have '
                'surfaced repeatedly since 2025 without a strike -- wait for a second outlet.')},
    {'tripwires': ['cooperation_suspended'], 'weight': 6.5,
     'confirmed': ('Mexico has suspended security cooperation or expelled US agents, confirmed by 2+ outlets. '
                   'That removes the main thing that has kept unilateral US action off the table.'),
     'single': 'One outlet reports Mexico curbing security cooperation; not yet corroborated.'},
    {'tripwires': ['usmca_withdrawal'], 'weight': 6.5,
     'confirmed': ('Formal notice to leave USMCA is confirmed. Prices of cars, parts and produce in the US and '
                   'jobs in Mexico\'s factory belt are directly exposed; watch the peso.'),
     'single': 'One outlet reports a USMCA withdrawal notice; not yet corroborated. Threats are common, notices are not.'},
    {'tripwires': ['senior_official_killed'], 'weight': 6.0,
     'confirmed': ('A senior official has been killed, confirmed by 2+ outlets. Cartels taking on the state at '
                   'this level invites both a Mexican crackdown and louder US calls for intervention.')},
    {'tripwires': ['new_us_tariffs'], 'weight': 5.0,
     'confirmed': ('New US tariffs on Mexico are confirmed. Expect the peso to move first and US prices for '
                   'cars, parts and produce to follow over months.')},
    {'tripwires': ['massacre', 'narco_blockades', 'attack_on_forces'], 'weight': 4.6,
     'confirmed': ('Major cartel violence is confirmed by 2+ outlets. Each spike feeds the US argument that '
                   'Mexico cannot control its territory -- the argument that precedes unilateral action.')},
    {'tripwires': ['kingpin_removed'], 'weight': 4.8,
     'confirmed': ('A top cartel leader has been captured or killed. Expect retaliation (blockades, burning '
                   'vehicles) and a succession fight -- removals usually raise violence before they lower it.')},
    {'tripwires': ['border_incident', 'border_closure'], 'weight': 4.6,
     'confirmed': ('A border security incident or closure is confirmed. Border events move fastest into US '
                   'domestic politics and trade flows.')},
    {'tripwires': ['prisoner_transfer'], 'weight': 3.8,
     'confirmed': ('Mexico has sent cartel prisoners to the US. Read it as cooperation that buys room: '
                   'transfers have come when US pressure peaks.')},
]
VECTOR_SO_WHAT = {
    'us_pressure': (3.6, 'Washington pressure on Mexico (security and trade) is in the news more than usual. '
                         'In Mexico the two travel together: security demands and tariff threats are often bundled.'),
    'cartel_violence': (3.0, 'Cartel news is busier than usual -- in Mexico that is a high baseline, so treat it as '
                             'a signal only if a confirmed event sits behind it.'),
    'border': (3.0, 'Border and migration reporting is up. Border events move fastest into US politics.'),
}
STANDING_SO_WHAT = [
    'The unasked question: will the US use force against cartels inside Mexico, and what does Mexico do if it '
    'does? Every security, trade and border signal on this page is read against that question.',
]


def _mexico_pulse(redis_get):
    """Context only: the Mexico Financial Pulse (peso / IPC / WTI) if cached."""
    d = redis_get('stability:mexico:financial_pulse') or {}
    fp = d.get('financial_pulse') or d
    tiles = (fp or {}).get('tiles') or {}
    peso = tiles.get('MXNUSD') or {}
    return {'peso_tier': peso.get('tier'), 'peso_change_24h': peso.get('change_pct_24h'),
            'read': d.get('read')} if tiles else {}


def _pulse_signal(t, ctx):
    p = ctx['extras'].get('pulse') or {}
    if p.get('peso_tier') in ('stress', 'warning') and (ctx['vector_levels'].get('us_pressure') in ('elevated', 'high', 'surge')):
        return [t.sig('market_coupling', 2, 'Mexico: the peso is under pressure while US-pressure news is busy',
                      'The peso tile on the Mexico Financial Pulse reads ' + str(p['peso_tier']) +
                      ' in the same cycle as above-usual US-pressure reporting. Markets price US-Mexico risk '
                      'before officials announce it.', 'economic', 'trade', kind='commodity_coupling')]
    return []


CONFIG = {
    'slug': 'mexico', 'name': 'Mexico', 'flag': '🇲🇽', 'version': VERSION, 'facts_as_of': '2026-11-04',
    'actors': ACTORS, 'vectors': VECTORS,
    'rss_feeds': {
        'el_financiero': {'url': 'https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml',
                          'name': 'El Financiero', 'language': 'es'},
        'mnd': {'url': 'https://mexiconewsdaily.com/feed/', 'name': 'Mexico News Daily', 'language': 'en'},
        'insight_crime': {'url': 'https://insightcrime.org/feed/', 'name': 'InSight Crime', 'language': 'en'},
        'border_report': {'url': 'https://www.borderreport.com/feed/', 'name': 'Border Report', 'language': 'en'},
        'infobae': {'url': 'https://www.infobae.com/arc/outboundfeeds/rss/?outputType=xml',
                    'name': 'Infobae', 'language': 'es', 'max': 60},
    },
    'google_queries': [
        ('Sheinbaum mañanera', 'es-419', 'MX'), ('Sheinbaum Estados Unidos cárteles', 'es-419', 'MX'),
        ('García Harfuch', 'es-419', 'MX'), ('Sinaloa Culiacán violencia', 'es-419', 'MX'),
        ('CJNG', 'es-419', 'MX'), ('T-MEC aranceles', 'es-419', 'MX'),
        ('US Mexico cartels military', 'en-US', 'US'), ('USMCA Mexico tariffs', 'en-US', 'US'),
        ('Mexico border shooting OR drones cartel', 'en-US', 'US'),
    ],
    'gdelt_en': ['Mexico cartel', 'Sheinbaum', 'US Mexico security', 'USMCA Mexico'],
    'gdelt_es': ['Sheinbaum seguridad', 'cártel Sinaloa', 'aranceles México'],
    'newsapi_queries': ['Sheinbaum', 'Mexico cartels', 'USMCA Mexico'],
    'brave_queries': ['Mexico cartel news', 'Sheinbaum United States'],
    'bluesky_target': 'mexico',
    'scrub': ['new mexico', 'nuevo mexico', 'gulf of mexico', 'golfo de mexico'],
    'context_terms': ('mexico', 'mexicano', 'mexicana', 'mexicanos', 'mexicanas', 'sheinbaum', 'cdmx',
                      'ciudad de mexico', 'mexico city', 'sinaloa', 'culiacan', 'jalisco', 'guadalajara',
                      'michoacan', 'tamaulipas', 'chihuahua', 'ciudad juarez', 'tijuana', 'baja california',
                      'sonora', 'estado de guerrero', 'acapulco', 'veracruz', 'nuevo leon', 'monterrey', 'zacatecas',
                      'guanajuato', 'morena', 'pemex', 'banxico', 't-mec', 'cjng', 'harfuch', 'ebrard', 'sedena',
                      'semar', 'palacio nacional', 'mananera', 'chapitos', 'mayiza', 'el mencho', 'reynosa',
                      'matamoros', 'nuevo laredo', 'tapachula', 'oaxaca', 'chiapas', 'quintana roo', 'cancun',
                      'queretaro', 'puebla', 'uruapan'),
    'own_outlets': ('el financiero', 'elfinanciero.com.mx', 'mexico news daily', 'mexiconewsdaily', 'milenio',
                    'el universal', 'eluniversal.com.mx', 'la jornada', 'proceso', 'reforma', 'animal politico',
                    'excelsior', 'aristegui', 'el economista'),
    'own_tld': '.mx/',
    'foreign_markers': ('argentina', 'milei', 'colombia', 'petro', 'venezuela', 'peru', 'chile', 'guatemala',
                        'honduras', 'el salvador', 'bukele', 'cuba', 'espana', 'brasil', 'brazil', 'ecuador'),
    'exclusions': {
        'us_strike_mexico': ('lancha', 'boat', 'embarcacion', 'pacifico oriental', 'eastern pacific', 'caribe',
                             'caribbean', 'rechaza', 'descarta', 'rules out', 'rejects', 'no habra', 'polymarket'),
        'us_ground_operation': ('rechaza', 'descarta', 'rules out', 'rejects', 'no habra', 'no permitira',
                                'will not allow', 'frontera', 'border'),
        'massacre': ('aniversario', 'anniversary', 'tlatelolco', 'acteal', '1968'),
        'foreign_agents_scandal': ('venezuela', 'cuba'),
        'border_closure': ('reabre', 'reopens', 'reapertura'),
    },
    'red_lines': RED_LINES, 'green_lines': GREEN_LINES,
    'meanings': MEANINGS, 'tripwire_plain': TRIPWIRE_PLAIN, 'tripwire_meaning': TRIPWIRE_MEANING,
    'actor_meaning': {'presidency': 'politics', 'security_cabinet': 'sovereignty', 'cartels': 'cartels',
                      'us_security': 'sovereignty', 'us_trade': 'trade', 'migration_border': 'border',
                      'china_mexico': 'china_mexico'},
    'vector_pressure': {'governance': 'governance', 'cartel_violence': 'kinetic', 'us_pressure': 'diplomatic',
                        'border': 'humanitarian', 'china': 'economic'},
    'so_what_rules': SO_WHAT_RULES, 'vector_so_what': VECTOR_SO_WHAT, 'standing_so_what': STANDING_SO_WHAT,
    'quiet_so_what': ('Mexico reads quiet this cycle against its own high baseline. What would change that: '
                      'a US strike or ground operation in Mexico confirmed by 2+ outlets, Mexico suspending '
                      'security cooperation, a USMCA withdrawal notice, or a senior official assassinated.'),
    'background': MEANINGS['politics']['plain'],
    'spokes': [
        ('us', 'us_security', 'inbound_target',
         'Cartel terrorist designations (Feb 2025) give Washington a legal hook for force; Mexico answers with '
         'cooperation it controls -- intelligence sharing and prisoner transfers -- and refuses US troops.'),
        ('china', 'china_mexico', 'trade_conduit',
         'Washington\'s concern is Chinese goods routed through Mexico; Mexico raised tariffs on Asian imports in 2026.'),
    ],
    'fingerprints': {'mexico_us_kinetic': ['us_strike_mexico', 'us_ground_operation'],
                     'mexico_trade_rupture': ['usmca_withdrawal', 'new_us_tariffs', 'border_closure']},
    'extra_reads': {'pulse': _mexico_pulse},
    'extra_signals': [_pulse_signal],
}

tracker = CountryRhetoricTracker(CONFIG)


def scan_mexico_rhetoric(force=False):
    return tracker.scan(force=force)


def register_mexico_rhetoric_endpoints(app, force_gate=None, start_background=True):
    tracker.register(app, force_gate=force_gate, start_background=start_background, warmup_seconds=200)
