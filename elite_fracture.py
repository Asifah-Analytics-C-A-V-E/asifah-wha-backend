"""
Asifah Analytics -- Elite Fracture Detector
v1.0.0 -- July 23 2026  |  portable primitive, Cuba profile first

═══════════════════════════════════════════════════════════════════════
THE PROBLEM THIS SOLVES
═══════════════════════════════════════════════════════════════════════
Every regime tracker on the platform measures STREET fracture:

    regime_fracture = max(dissident_signal - suppression_signal, 0)

That models popular unrest -- protests, 11J-style eruptions, visible dissent
contained (or not) by visible repression. It is the right model for that
question and the wrong model for a different one.

ELITE fracture has an inverted signature. When the fight moves inside the
palace, the street goes QUIET: suppression rises pre-emptively, dissidents are
detained before they assemble, and the composite street read falls toward zero
at exactly the moment risk is highest. A tracker built only for street fracture
reads a succession crisis as calm -- right up until it is not.

The 1911 Madero case is the canonical shape: an aged autocrat, an elite that
stops believing in the succession, and a rupture that begins above the street
rather than in it. Cuba's own 2006 handover ran the same way -- Fidel vanished
from state media before anything was announced.

═══════════════════════════════════════════════════════════════════════
THE SEVEN COMPONENTS
═══════════════════════════════════════════════════════════════════════
1. ABSENCE ANOMALY        -- principal missing from expected appearances
2. EXTRAORDINARY CONVOCATION -- unscheduled plenum / special session
3. PERSONNEL CHURN        -- military & security reshuffles
4. SUCCESSION VOCABULARY  -- explicit transfer/relief/continuity language
5. REASSURANCE SURGE      -- INVERSE signal (see below)
6. PRE-EMPTIVE SUPPRESSION-- repression rising ahead of street activity
7. CAPITAL SECURITY POSTURE -- forces concentrating on the seat of power

TWO OF THESE ARE INVERSE READS, and they are the analytically interesting ones:

  * REASSURANCE SURGE. Regimes do not proclaim continuity when continuity is
    secure. A spike in "the Revolution continues" messaging is a statement
    about what the regime fears its own cadre is thinking. This is the
    doctrine's "reading other actors' beliefs" move -- an observation about
    what informed insiders believe, drawn from open evidence, predicting
    nothing.

  * PRE-EMPTIVE SUPPRESSION. Routine repression is control. Repression rising
    while street activity stays flat is the regime acting on information the
    street does not have yet. The street model reads this as stability; here it
    reads as brittleness. Same input, opposite meaning, because the question
    is different.

═══════════════════════════════════════════════════════════════════════
DOCTRINE
═══════════════════════════════════════════════════════════════════════
Convergence, not prediction. This module NEVER says a transition will occur,
is imminent, or is likely. It reports which elite-transition-stress signals are
observable right now and what such patterns have historically preceded. The
reader completes the inference.

Absence-honest: a component with no evidence scores zero and says so. Silence
is reported as silence, never inferred as calm.

═══════════════════════════════════════════════════════════════════════
PORTABILITY
═══════════════════════════════════════════════════════════════════════
Everything country-specific lives in a PROFILE dict. To add DPRK, Venezuela, or
Russia, add a profile -- the detectors, scoring, banding and prose are generic.
This is the primitive the Black Swan roadmap's DPRK Succession detector needs.

COPYRIGHT (c) 2025-2026 Asifah Analytics. All rights reserved.
"""

import unicodedata
from datetime import datetime, timezone

__version__ = '1.0.0'


# ============================================================
# TEXT NORMALISATION
# ============================================================
def _fold(s):
    """Accent-fold + lowercase. Spanish sources write 'Raul' and 'regimen';
    unaccented keywords must match them. Folding both sides fixes every term
    at once rather than hand-adding variants."""
    if not s:
        return ''
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s))
                   if not unicodedata.combining(c)).lower()


def _corpus(articles):
    parts = []
    for a in (articles or []):
        if isinstance(a, dict):
            parts.append('%s %s' % (a.get('title') or '', a.get('description') or ''))
        elif isinstance(a, str):
            parts.append(a)
    return _fold(' | '.join(parts))


def _hits(corpus, terms):
    """Distinct matched terms. A count of DISTINCT vocabulary, not raw volume --
    one story repeated twenty times should not look like twenty signals."""
    return [t for t in terms if _fold(t) in corpus]


def _evidence(articles, terms, limit=3):
    """Pull headlines that actually carry the matched vocabulary, so every
    component can show its work rather than asserting a score."""
    out = []
    for a in (articles or []):
        if not isinstance(a, dict):
            continue
        blob = _fold('%s %s' % (a.get('title') or '', a.get('description') or ''))
        for t in terms:
            if _fold(t) in blob:
                title = (a.get('title') or '').strip()
                if title and title not in out:
                    out.append(title[:180])
                break
        if len(out) >= limit:
            break
    return out


# ============================================================
# CUBA PROFILE
# ============================================================
CUBA_PROFILE = {
    'country': 'cuba',
    'display': 'Cuba',
    'principals': ['raul castro', 'raul', 'diaz-canel', 'diaz canel',
                   'miguel diaz-canel', 'general de ejercito'],

    # 1. ABSENCE -- reporting ABOUT absence is the observable; we cannot
    #    measure an appearance that did not happen, but the press notices.
    'absence': [
        'ausente', 'no asistio', 'no aparecio', 'no participo',
        'ausencia de raul', 'ausencia de diaz-canel', 'sin aparecer',
        'no se ha visto', 'no ha sido visto', 'lleva semanas sin',
        'rumores sobre su salud', 'estado de salud de raul',
        'salud de raul castro', 'hospitalizado', 'delicado de salud',
        'did not attend', 'absent from', 'has not been seen',
        'health rumors', 'rumours about his health',
    ],

    # 2. EXTRAORDINARY CONVOCATION -- unscheduled institutional gatherings are
    #    how one-party systems ratify decisions already taken.
    'convocation': [
        'pleno extraordinario', 'sesion extraordinaria', 'reunion extraordinaria',
        'convocatoria urgente', 'buro politico se reune', 'pleno del comite central',
        'asamblea nacional extraordinaria', 'congreso extraordinario del partido',
        'consejo de estado se reune de urgencia',
        'extraordinary plenum', 'emergency session', 'special session of the assembly',
        'politburo convened', 'central committee plenum',
    ],

    # 3. PERSONNEL CHURN -- who holds the guns, and did that change quietly?
    'personnel': [
        'releva a', 'relevado de su cargo', 'destituido', 'destitucion',
        'sustituido en el cargo', 'nuevo ministro del interior',
        'nuevo ministro de las far', 'cambios en el minint',
        'cambios en las far', 'reorganizacion militar', 'purga',
        'general retirado', 'pasa a retiro', 'cesado en funciones',
        'reshuffle', 'dismissed from post', 'removed from his post',
        'new interior minister', 'purge of officials',
    ],

    # 4. SUCCESSION VOCABULARY -- explicit transfer language.
    'succession': [
        'sucesion', 'relevo generacional', 'traspaso de poder',
        'transicion politica', 'quien sucedera', 'sucesor de raul',
        'proceso de sucesion', 'entrega del poder', 'renuncia',
        'dimision', 'sucesion presidencial',
        'succession', 'transfer of power', 'who will succeed',
        'step down', 'resignation of',
    ],

    # 5. REASSURANCE -- INVERSE. Continuity proclaimed is continuity doubted.
    'reassurance': [
        'la revolucion continua', 'continuidad de la revolucion',
        'unidad del partido', 'unidad monolitica', 'firmeza revolucionaria',
        'nada detendra la revolucion', 'el partido esta unido',
        'continuidad historica', 'somos continuidad',
        'la revolucion es invencible', 'orden interior garantizado',
        'the revolution continues', 'party unity', 'unbreakable unity',
    ],

    # 7. CAPITAL SECURITY POSTURE -- forces around the seat of power.
    'capital_security': [
        'tropas en la habana', 'militares en las calles de la habana',
        'despliegue en plaza de la revolucion', 'boinas negras',
        'tropas especiales', 'operativo policial en la habana',
        'refuerzo de seguridad en la habana', 'control militar de la capital',
        'troops in havana', 'security deployment havana',
    ],

    # Actor keys used for the pre-emptive-suppression differential
    'suppression_actor': 'cuban_military_security',
    'dissident_actor':   'cuban_dissidents',

    'precedents': [
        {'label': 'Fidel hands power to Raul (July 2006)',
         'lesson': 'Absence from state media preceded any announcement; the '
                   'transfer was ratified institutionally only after the fact.'},
        {'label': 'Raul formally assumes presidency (Feb 2008)',
         'lesson': 'Provisional arrangement made permanent through a scheduled '
                   'National Assembly session -- an orderly elite transition '
                   'with no street component.'},
        {'label': 'Diaz-Canel assumes presidency (2018) / PCC First Secretary (2021)',
         'lesson': 'Managed succession outside the Castro line; continuity '
                   'messaging surged around both handovers.'},
        {'label': 'Madero / Diaz rupture (Mexico, 1910-11)',
         'lesson': 'An aged autocrat, an elite that stopped believing in the '
                   'succession, and a rupture that began above the street. The '
                   'canonical shape for elite-initiated removal.'},
        {'label': 'Ceausescu (Romania, Dec 1989)',
         'lesson': 'Security apparatus fractured from the top; the decisive '
                   'turn was the army changing sides, not the crowd growing.'},
    ],
}

PROFILES = {'cuba': CUBA_PROFILE}


# ============================================================
# COMPONENT DETECTORS
# ============================================================
def _component(name, label, corpus, articles, terms, weight, inverse=False, note=''):
    matched = _hits(corpus, terms)
    n = len(matched)
    # Distinct-vocabulary bands: 1-2 terms = present, 3-4 = notable, 5+ = dense
    raw = 0 if n == 0 else (1 if n <= 2 else (2 if n <= 4 else 3))
    return {
        'id':        name,
        'label':     label,
        'lit':       raw > 0,
        'intensity': raw,
        'weighted':  round(raw * weight, 2),
        'weight':    weight,
        'inverse':   inverse,
        'matched_terms': matched[:8],
        'distinct_terms': n,
        'evidence':  _evidence(articles, matched) if matched else [],
        'note':      note,
    }


def _preemptive_suppression(actor_results, profile):
    """Suppression rising while the street stays flat.

    The street model treats suppression as the thing that CONTAINS dissent, so
    high suppression lowers its fracture score. Here the differential is the
    signal: when repression runs ahead of visible dissent, the regime is acting
    on something the street has not produced yet. Same observation, opposite
    reading, because the question is different.
    """
    ar = actor_results or {}
    def lvl(key):
        v = ar.get(key)
        if isinstance(v, dict):
            for f in ('escalation_level', 'level', 'threat_level'):
                if f in v:
                    try:
                        return int(v[f] or 0)
                    except (TypeError, ValueError):
                        return 0
        try:
            return int(v or 0)
        except (TypeError, ValueError):
            return 0

    supp = lvl(profile['suppression_actor'])
    diss = lvl(profile['dissident_actor'])
    gap = supp - diss
    intensity = 0 if gap <= 0 else (1 if gap == 1 else (2 if gap == 2 else 3))
    return {
        'id':        'preemptive_suppression',
        'label':     'Pre-emptive suppression (repression ahead of the street)',
        'lit':       intensity > 0,
        'intensity': intensity,
        'weighted':  round(intensity * 1.2, 2),
        'weight':    1.2,
        'inverse':   True,
        'suppression_level': supp,
        'dissident_level':   diss,
        'gap':       gap,
        'evidence':  [],
        'note':      ('Suppression L%d against dissident L%d. A positive gap reads as '
                      'the security apparatus moving ahead of visible street activity.'
                      % (supp, diss)),
    }


# ============================================================
# MAIN
# ============================================================
def compute_elite_fracture(articles, actor_results=None, country='cuba'):
    """
    Score elite-transition stress from the scanned corpus.

    Returns a dict carrying the band, the component breakdown, the evidence
    behind each lit component, precedent-anchored prose, and the mandatory
    convergence disclaimer.
    """
    profile = PROFILES.get(country) or CUBA_PROFILE
    corpus = _corpus(articles)

    comps = [
        _component('absence_anomaly', 'Principal absence from expected appearances',
                   corpus, articles, profile['absence'], 1.3,
                   note='Absence is the earliest observable in every Cuban transition '
                        'to date; in 2006 it preceded any announcement.'),
        _component('extraordinary_convocation', 'Extraordinary institutional convocation',
                   corpus, articles, profile['convocation'], 1.2,
                   note='One-party systems convene to ratify decisions already taken.'),
        _component('personnel_churn', 'Military / security personnel churn',
                   corpus, articles, profile['personnel'], 1.1,
                   note='Movement among those who hold the guns is the load-bearing '
                        'variable in elite transitions.'),
        _component('succession_vocabulary', 'Explicit succession vocabulary',
                   corpus, articles, profile['succession'], 1.0,
                   note='Open discussion of transfer is late-stage; it usually '
                        'follows the other components rather than leading them.'),
        _component('reassurance_surge', 'Continuity / unity messaging surge (inverse)',
                   corpus, articles, profile['reassurance'], 0.9, inverse=True,
                   note='INVERSE READ. Regimes do not proclaim continuity when '
                        'continuity is secure; a surge is a statement about what '
                        'the leadership fears its own cadre believes.'),
        _component('capital_security', 'Security posture around the seat of power',
                   corpus, articles, profile['capital_security'], 1.1,
                   note='Force concentration on the capital rather than the '
                        'provinces distinguishes palace risk from street risk.'),
    ]
    comps.append(_preemptive_suppression(actor_results, profile))

    lit = [c for c in comps if c['lit']]
    composite = round(sum(c['weighted'] for c in comps), 2)
    lit_count = len(lit)

    # ── BANDING ──
    # Deliberately requires BREADTH, not depth: any single component has an
    # innocent explanation (a leader skips one event; a ministry reshuffles).
    # Several independent components lighting together is the read.
    if lit_count >= 5 or composite >= 8.0:
        band, band_label, color = 'acute', 'ACUTE -- MULTI-COMPONENT ELITE STRESS', '#dc2626'
    elif lit_count >= 3 or composite >= 4.5:
        band, band_label, color = 'elevated', 'ELEVATED -- ELITE STRESS SIGNALS CONVERGING', '#f97316'
    elif lit_count >= 1:
        band, band_label, color = 'watch', 'WATCH -- ISOLATED ELITE SIGNAL', '#f59e0b'
    else:
        band, band_label, color = 'dormant', 'DORMANT -- NO ELITE-STRESS SIGNALS', '#6b7280'

    prose = _build_prose(profile, band, lit, comps, composite)

    return {
        'module':     'elite_fracture',
        'version':    __version__,
        'country':    profile['country'],
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'band':       band,
        'band_label': band_label,
        'color':      color,
        'composite':  composite,
        'lit_count':  lit_count,
        'components': comps,
        'prose':      prose,
        'precedents': profile['precedents'],
        'disclaimer': ('This is a CONVERGENCE indicator, NOT a probability of action. '
                       'It reports which elite-transition-stress signals are observable '
                       'now and what such patterns have historically preceded. It does '
                       'not forecast a transition, a timeline, or an outcome.'),
        'methodology': ('Distinct-vocabulary counts across seven components, two of them '
                        'inverse reads (continuity messaging; suppression running ahead '
                        'of street activity). Banding requires breadth across independent '
                        'components rather than depth in any one, because a single '
                        'component almost always has an innocent explanation.'),
    }


def _build_prose(profile, band, lit, comps, composite):
    """Estimative voice. Names what is observable and what it has historically
    preceded; never asserts what will happen."""
    disp = profile['display']

    if band == 'dormant':
        return ('%s elite-fracture read: no elite-transition-stress signals observable '
                'this cycle. This is an absence of signal, not evidence of stability -- '
                'palace dynamics are poorly observable by design, and the street-level '
                'read is the better instrument while this one is quiet.' % disp)

    names = ', '.join(c['label'].split('(')[0].strip().lower() for c in lit)
    parts = ['%s elite-fracture read: %d of 7 components active (composite %.1f) -- %s.'
             % (disp, len(lit), composite, names)]

    inv = [c for c in lit if c.get('inverse')]
    if inv:
        parts.append('Note the inverse components: %s. These read opposite to the '
                     'street model -- continuity messaging and pre-emptive repression '
                     'both indicate leadership anxiety rather than leadership control, '
                     'and both suppress the street-fracture score at the same time.'
                     % ', '.join(c['label'].split('(')[0].strip().lower() for c in inv))

    if band == 'acute':
        parts.append('Breadth at this level across independent components is consistent '
                     'with the pattern that has historically preceded elite-initiated '
                     'transitions -- in Cuba 2006, absence from state media preceded any '
                     'announcement; in the Madero and Ceausescu cases, the decisive '
                     'movement occurred above the street while the street appeared calm.')
    elif band == 'elevated':
        parts.append('Convergence across several independent components is the threshold '
                     'at which elite dynamics historically become legible from outside. '
                     'Watch whether personnel churn and capital security posture join '
                     'the existing set -- those two carry the most weight because they '
                     'concern who holds the guns.')
    else:
        parts.append('A single lit component is not a pattern; isolated signals in this '
                     'space usually have routine explanations. It is logged so that a '
                     'later convergence can be dated back to its first appearance.')

    parts.append('CAUTION: the street-fracture read may fall while this rises. That '
                 'divergence is itself the finding, not a contradiction.')
    return ' '.join(parts)


# ============================================================
# SELF-TEST
# ============================================================
if __name__ == '__main__':
    print('Elite Fracture Detector v%s -- self-test\n' % __version__)

    dormant = [{'title': 'Cuba announces new tourism campaign for winter season',
                'description': 'Ministry promotes Varadero bookings.'}]
    r = compute_elite_fracture(dormant, {'cuban_military_security': 1,
                                         'cuban_dissidents': 1})
    print('TEST 1 -- quiet corpus')
    print('  band:', r['band_label'])
    print('  prose:', r['prose'][:150], '...')
    assert r['band'] == 'dormant'
    print('  OK -- absence reported as absence, not inferred as calm\n')

    acute = [
        {'title': 'Raúl Castro ausente de la sesión plenaria del Comité Central',
         'description': 'El general de ejército no asistió; crecen rumores sobre su salud.'},
        {'title': 'Convocan pleno extraordinario del Partido Comunista de Cuba',
         'description': 'Reunión extraordinaria sin fecha previa en el calendario.'},
        {'title': 'Cambios en el MININT: destituido el viceministro del Interior',
         'description': 'Relevado de su cargo tras una reorganización militar.'},
        {'title': 'Granma: la Revolución continúa, el partido está unido',
         'description': 'Editorial insiste en la continuidad histórica y la unidad monolítica.'},
        {'title': 'Refuerzo de seguridad en La Habana; tropas especiales desplegadas',
         'description': 'Operativo policial en la capital.'},
    ]
    r2 = compute_elite_fracture(acute, {'cuban_military_security': 4,
                                        'cuban_dissidents': 1})
    print('TEST 2 -- convergent corpus (your Madero scenario)')
    print('  band:      ', r2['band_label'])
    print('  composite: ', r2['composite'], '| lit:', r2['lit_count'], 'of 7')
    for c in r2['components']:
        if c['lit']:
            flag = ' [INVERSE]' if c.get('inverse') else ''
            print('    * %-52s x%d%s' % (c['label'][:52], c['intensity'], flag))
    print('\n  PROSE:\n  ', r2['prose'][:520], '...')
    assert r2['band'] == 'acute', r2['band']
    assert any(c['id'] == 'preemptive_suppression' and c['lit'] for c in r2['components'])
    print('\n  OK -- breadth across independent components fires ACUTE')
    print('  OK -- pre-emptive suppression lit (L4 supp vs L1 diss)')

    # The divergence that motivates the module
    print('\nTEST 3 -- divergence check')
    street = max(1 - 4, 0)
    print('  street-fracture (dissident 1 - suppression 4) =', street, '-> reads CALM')
    print('  elite-fracture band                            =', r2['band'], '-> reads ACUTE')
    print('  OK -- the two instruments disagree, which is precisely the point')
