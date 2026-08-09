"""Spanish→English economics terms, for expanding a query before retrieval.

The corpus is bilingual and split by language along topic lines: the Spanish
documents are institutional (Banco de España, AIReF, BCE) and Austrian-school,
while the theory and the econometrics are English textbooks. Users type
Spanish. Both retrievers suffer for it in different ways — BM25 cannot cross a
language at all, and the embedder bridges ES↔EN unevenly, well enough for
"praxeología" and not well enough for "brecha del producto".

So the query carries its own translation. This is a glossary and not a
translator on purpose: it is deterministic, adds no latency, no model call and
no dependency, and every entry is auditable. It also stays narrow — only terms
of art, because expanding common words would flood the lexical query with noise
and dilute the embedding.

Entries earn their place by being terminology a textbook indexes under, not by
being Spanish words that happen to have an English equivalent.
"""
from __future__ import annotations

import unicodedata

#: Accent-free, lower-case Spanish term → English terms to append.
#: Longest keys are matched first, so "tipo de interés real" wins over
#: "tipo de interés".
TERMS: dict[str, str] = {
    # macro identities and gaps
    "brecha del producto": "output gap",
    "producto potencial": "potential output",
    "ley de okun": "Okun law",
    "curva de phillips": "Phillips curve",
    "tasa de crecimiento": "growth rate",
    "crecimiento economico": "economic growth",
    "desempleo": "unemployment",
    "paro": "unemployment",
    "expectativas de inflacion": "inflation expectations",
    "inflacion": "inflation",
    "tipo de interes real": "real interest rate",
    "tipo de interes": "interest rate",
    "tipos de interes": "interest rates",
    "politica monetaria": "monetary policy",
    "politica fiscal": "fiscal policy",
    # debt sustainability
    "sostenibilidad de la deuda": "debt sustainability",
    "deuda publica": "public debt government debt",
    "deuda soberana": "sovereign debt",
    "saldo primario": "primary balance",
    "superavit primario": "primary surplus",
    "bola de nieve": "snowball effect debt dynamics",
    "efecto bola de nieve": "snowball effect",
    "riesgo soberano": "sovereign risk",
    "prima de riesgo": "risk premium sovereign spread",
    "consolidacion fiscal": "fiscal consolidation austerity",
    "multiplicador fiscal": "fiscal multiplier",
    "gasto publico": "government spending",
    "ingresos publicos": "government revenue",
    "estabilizar la ratio": "stabilise the debt ratio",
    # micro
    "elasticidad": "elasticity",
    "oferta y demanda": "supply and demand",
    "excedente del consumidor": "consumer surplus",
    "excedente del productor": "producer surplus",
    "coste de oportunidad": "opportunity cost",
    "incidencia fiscal": "tax incidence",
    "impuesto": "tax",
    "cuna fiscal": "tax wedge",
    "peso muerto": "deadweight loss",
    "rendimientos decrecientes": "diminishing returns",
    # econometrics
    "efectos fijos": "fixed effects",
    "datos de panel": "panel data",
    "errores estandar": "standard errors",
    "errores agrupados": "clustered standard errors",
    "variable omitida": "omitted variable",
    "variable instrumental": "instrumental variable",
    "proyecciones locales": "local projections",
    "funcion de respuesta al impulso": "impulse response function",
    "minimos cuadrados": "least squares",
    "heterocedasticidad": "heteroskedasticity",
    "estocastico": "stochastic",
    "serie temporal": "time series",
    # housing and households
    "precio de la vivienda": "house prices housing",
    "vivienda": "housing",
    "hipoteca": "mortgage",
    "alquiler": "rent",
    "asequibilidad": "affordability",
    "hogares": "households",
    "riqueza": "wealth",
    "pobreza infantil": "child poverty",
    "pobreza": "poverty",
    "desigualdad": "inequality",
    # money and the Austrian corpus
    "calculo economico": "economic calculation",
    "ciclo economico": "business cycle",
    "expansion del credito": "credit expansion",
    "oferta monetaria": "money supply",
    "banco central": "central bank",
    # development
    "desarrollo economico": "economic development",
    "instituciones": "institutions",
    "productividad": "productivity",
    "inmigracion": "immigration",
    "salarios": "wages",
    "mercado laboral": "labour market labor market",
}

#: Longest first: a query containing "tipo de interés real" should not be
#: expanded twice, once for the phrase and once for the substring.
_ORDERED = sorted(TERMS, key=len, reverse=True)


def _fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def english_terms(query: str) -> list[str]:
    """English terminology implied by a Spanish query, in match order.

    Phrases stay whole. Deduplicating word by word used to turn "growth rate"
    plus "interest rate" into "growth rate interest", quietly destroying the
    second term of art — the one the question was actually about.
    """
    hay = _fold(query)
    out: list[str] = []
    for es in _ORDERED:
        if es in hay:
            hay = hay.replace(es, " ")          # consume, so no double match
            phrase = TERMS[es]
            if phrase not in out:
                out.append(phrase)
    return out


def expand(query: str) -> str:
    """The query with its English terminology appended.

    Appended rather than substituted: the Spanish half still has to reach the
    Spanish documents, which for debt sustainability are the ones that answer.
    """
    extra = english_terms(query)
    return f"{query} {' '.join(extra)}" if extra else query


def is_expanded(query: str) -> bool:
    return bool(english_terms(query))
