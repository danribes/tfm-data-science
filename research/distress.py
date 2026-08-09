"""Early warning of sovereign distress: what the countries that ended badly
looked like beforehand.

This is the probabilistic complement to the 7 % bond-yield red line. The yield
says what the market demands today; this says how closely a country's macro
position resembles those that went on to default, judged on 418 real onsets
across 65 years.

Three decisions do most of the work, and each of them makes the number smaller
and the exercise honest:

  onset, not state — 49 % of country-years in the database are "in default",
      because a default lasts years. Predicting that is almost the same as
      reading last year's value. The label here is the *first* year of a spell:
      3,9 % of eligible rows, and a genuine early-warning problem.

  forecast, not description — features are read at t and the label at t+1.
      A model given this year's collapse to explain this year's default has
      learned nothing anyone can use.

  grouped by country — no country appears in both train and test. Sovereign
      panels are strongly autocorrelated within a country, so a random split
      would let the model memorise Argentina's 1980s and score itself on
      Argentina's 1990s.

Labels: BoC–BoE Sovereign Default Database (Bank of Canada / Bank of England),
2025 edition. Features: World Bank WDI.

    python -m research.distress
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "data" / "external"
OUT = ROOT / "docs" / "eval"

LABELS = EXTERNAL / "bocboe_default_labels.csv.gz"
FEATURES = EXTERNAL / "wb_macro_panel.csv.gz"

#: Names the World Bank spells differently, or entities it no longer lists.
#: Written out rather than fuzzy-matched: a fuzzy match that silently pairs
#: "Congo" with the wrong Congo would corrupt the panel invisibly, and there
#: are only twenty-one of them.
ALIASES: dict[str, str | None] = {
    "Dem. Rep. of Congo (Kinshasa)": "COD",
    "Rep. of Congo (Brazzaville)": "COG",
    "Egypt": "EGY",
    "Laos": "LAO",
    "Micronesia": "FSM",
    "Nauru": "NRU",
    "Somalia": "SOM",
    "Syria": "SYR",
    "Turkey": "TUR",
    "Venezuela": "VEN",
    "Vietnam": "VNM",
    "eSwatini (Swaziland)": "SWZ",
    "Korea, Democratic People's Republic of (North)": "PRK",
    "USSR/Russian Federation": "RUS",
    "Anguilla": "AIA",
    "Cook Islands": "COK",
    "Sint Maarten": "SXM",
    "Netherlands Antilles": "ANT",
    "Puerto Rico": "PRI",
    # Dissolved states with no successor code in the WDI panel. Dropped rather
    # than mapped onto a successor, which would attribute one country's history
    # to another.
    "Czechoslovakia": None,
    "Yugoslavia": None,
}

FEATURE_COLS = [
    "ext_debt_gni", "debt_service_x", "reserves_mo", "reserves_debt",
    "cab_gdp", "gdp_growth", "inflation", "gdp_pc", "exports_gdp",
]

FEATURE_LABELS = {
    "ext_debt_gni": "Deuda externa (% RNB)",
    "debt_service_x": "Servicio de la deuda (% exportaciones)",
    "reserves_mo": "Reservas (meses de importaciones)",
    "reserves_debt": "Reservas (% deuda externa)",
    "cab_gdp": "Saldo por cuenta corriente (% PIB)",
    "gdp_growth": "Crecimiento del PIB (%)",
    "inflation": "Inflación (%)",
    "gdp_pc": "PIB per cápita (USD 2021)",
    "exports_gdp": "Exportaciones (% PIB)",
    "d_ext_debt_gni": "Δ deuda externa (3 años)",
    "d_reserves_mo": "Δ reservas (3 años)",
    "d_gdp_growth": "Δ crecimiento (3 años)",
}

SEED = 42


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z ]", " ", s)
    s = re.sub(r"\b(the|of|republic|rep|dem|democratic|people s|islamic|"
               r"federal|state|states|and)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _wb_names() -> dict[str, str]:
    """Normalised World Bank country name → ISO3, from the committed panel."""
    import requests
    r = requests.get("https://api.worldbank.org/v2/country",
                     params={"format": "json", "per_page": 400}, timeout=60)
    return {_norm(c["name"]): c["id"] for c in r.json()[1]
            if c["region"]["value"] != "Aggregates"}


def load_labels(name_map: dict[str, str] | None = None) -> pd.DataFrame:
    """Default onsets keyed by ISO3.

    Countries that cannot be mapped are dropped and counted, never guessed.
    """
    lab = pd.read_csv(LABELS)
    lookup = dict(name_map or {})
    if not lookup:
        try:
            lookup = _wb_names()
        except Exception:
            lookup = {}

    def to_iso3(name: str) -> str | None:
        if name in ALIASES:
            return ALIASES[name]
        return lookup.get(_norm(name))

    lab["iso3"] = lab.country.map(to_iso3)
    return lab


def build_panel(labels: pd.DataFrame | None = None) -> pd.DataFrame:
    """Features at t joined to the onset at t+1, excluding rows already in default."""
    lab = labels if labels is not None else load_labels()
    lab = lab.dropna(subset=["iso3"])

    feats = pd.read_csv(FEATURES)
    d = feats.merge(lab[["iso3", "year", "in_default", "onset"]],
                    on=["iso3", "year"], how="inner")
    d = d.sort_values(["iso3", "year"]).reset_index(drop=True)

    # Three-year changes: a level tells you where a country is, a change tells
    # you where it is heading, and the early-warning literature is mostly about
    # the second.
    for col in ("ext_debt_gni", "reserves_mo", "gdp_growth"):
        d[f"d_{col}"] = d.groupby("iso3")[col].diff(3)

    # The label is next year's onset. Only defined where next year exists and
    # belongs to the same country.
    d["next_year"] = d.groupby("iso3")["year"].shift(-1)
    d["y"] = d.groupby("iso3")["onset"].shift(-1)
    d = d[(d.next_year == d.year + 1) & d.y.notna()]

    # A country already in default cannot enter default. Keeping these rows
    # would fill the negative class with observations where the event was
    # impossible, and flatter every metric.
    d = d[d.in_default == 0]
    d["y"] = d.y.astype(int)
    return d.reset_index(drop=True)


@dataclass(frozen=True)
class Result:
    n: int
    n_positive: int
    base_rate: float
    n_countries: int
    auc: float
    auc_std: float
    pr_auc: float
    pr_auc_lift: float
    importances: list[dict]
    unmapped: list[str]
    years: tuple[int, int]

    @property
    def beats_chance(self) -> bool:
        """A grouped AUC has sampling noise; one standard deviation clear of
        0,5 is the weakest claim worth making."""
        return self.auc - self.auc_std > 0.5

    def to_dict(self) -> dict:
        return {
            "n": self.n, "n_positive": self.n_positive,
            "base_rate": self.base_rate, "n_countries": self.n_countries,
            "auc": self.auc, "auc_std": self.auc_std,
            "pr_auc": self.pr_auc, "pr_auc_lift": self.pr_auc_lift,
            "importances": self.importances, "unmapped": self.unmapped,
            "years": list(self.years), "beats_chance": self.beats_chance,
            "seed": SEED,
        }


def _model():
    from sklearn.ensemble import HistGradientBoostingClassifier

    # Gradient boosting on histograms, which is the same family as LightGBM and
    # already a dependency. It also takes NaN natively — load-bearing here,
    # because external-debt coverage is 41 % and imputing it would invent the
    # very variable the model leans on.
    return HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.05, max_depth=4,
        l2_regularization=1.0, random_state=SEED,
    )


def evaluate(panel: pd.DataFrame | None = None, n_splits: int = 5) -> Result:
    from sklearn.inspection import permutation_importance
    from sklearn.metrics import average_precision_score, roc_auc_score
    from sklearn.model_selection import GroupKFold

    d = panel if panel is not None else build_panel()
    cols = [c for c in FEATURE_LABELS if c in d.columns]
    X, y, g = d[cols].to_numpy(dtype=float), d.y.to_numpy(), d.iso3.to_numpy()

    aucs: list[float] = []
    prs: list[float] = []
    oof = np.full(len(y), np.nan)

    for train, test in GroupKFold(n_splits=n_splits).split(X, y, groups=g):
        if y[test].sum() == 0:          # a fold with no event cannot be scored
            continue
        m = _model().fit(X[train], y[train])
        p = m.predict_proba(X[test])[:, 1]
        oof[test] = p
        aucs.append(float(roc_auc_score(y[test], p)))
        prs.append(float(average_precision_score(y[test], p)))

    full = _model().fit(X, y)
    imp = permutation_importance(full, X, y, n_repeats=10, random_state=SEED,
                                 scoring="roc_auc")
    order = np.argsort(imp.importances_mean)[::-1]
    importances = [
        {"feature": cols[i], "label": FEATURE_LABELS[cols[i]],
         "mean": float(imp.importances_mean[i]), "std": float(imp.importances_std[i])}
        for i in order
    ]

    base = float(y.mean())
    pr = float(np.mean(prs))
    unmapped = sorted(set(load_labels().pipe(lambda t: t[t.iso3.isna()]).country))

    return Result(
        n=len(d), n_positive=int(y.sum()), base_rate=base,
        n_countries=int(d.iso3.nunique()),
        auc=float(np.mean(aucs)), auc_std=float(np.std(aucs)),
        pr_auc=pr,
        # Against the only baseline that needs no model: guessing the base rate.
        pr_auc_lift=pr / base if base else float("nan"),
        importances=importances, unmapped=unmapped,
        years=(int(d.year.min()), int(d.year.max())),
    )


def _feature_frame() -> pd.DataFrame:
    """Every country's features, labelled or not.

    Read separately from `build_panel` on purpose. Spain is absent from the
    default database entirely — it has not defaulted in the covered period — so
    an inner join drops it, and the country the gauge exists to score would be
    the one country it could not score.
    """
    f = pd.read_csv(FEATURES).sort_values(["iso3", "year"]).reset_index(drop=True)
    for col in ("ext_debt_gni", "reserves_mo", "gdp_growth"):
        f[f"d_{col}"] = f.groupby("iso3")[col].diff(3)
    return f


def score_country(iso3: str, panel: pd.DataFrame | None = None,
                  features: pd.DataFrame | None = None) -> dict | None:
    """Distress probability for one country's latest well-covered year.

    Fitted on every *other* country, so the country being asked about is never
    one the model was trained on. For a country with no default history that is
    automatic — it has no labels to train on — but it is enforced either way.
    """
    d = panel if panel is not None else build_panel()
    f = features if features is not None else _feature_frame()
    cols = [c for c in FEATURE_LABELS if c in d.columns]

    own = f[f.iso3 == iso3].copy()
    if own.empty:
        return None
    # The most recent year with at least half the features present. Scoring the
    # latest row regardless would hand the model a nearly empty vector from a
    # year the WDI has not finished publishing.
    own["cover"] = own[cols].notna().sum(axis=1)
    usable = own[own.cover >= len(cols) / 2]
    if usable.empty:
        return None
    last = usable.sort_values("year").iloc[-1]

    others = d[d.iso3 != iso3]
    m = _model().fit(others[cols].to_numpy(dtype=float), others.y.to_numpy())
    p = float(m.predict_proba(last[cols].to_numpy(dtype=float).reshape(1, -1))[0, 1])
    return {
        "iso3": iso3, "year": int(last.year), "probability": p,
        "base_rate": float(d.y.mean()),
        "in_label_set": bool((d.iso3 == iso3).any()),
        "coverage": f"{int(last.cover)}/{len(cols)}",
        "features": {c: (None if pd.isna(last[c]) else float(last[c])) for c in cols},
    }


def main() -> None:
    lab = load_labels()
    n_unmapped = lab[lab.iso3.isna()].country.nunique()
    print(f"etiquetas: {len(lab):,} país-año · "
          f"{int(lab.onset.sum()):,} inicios de impago · "
          f"{n_unmapped} países sin código ISO (estados disueltos, se descartan)")

    d = build_panel(lab)
    r = evaluate(d)

    print(f"\npanel: {r.n:,} filas · {r.n_countries} países · "
          f"{r.years[0]}-{r.years[1]}")
    print(f"inicios en el panel: {r.n_positive} ({r.base_rate:.2%})")
    print(f"\nAUC agrupada por país: {r.auc:.3f} ± {r.auc_std:.3f}")
    print(f"PR-AUC: {r.pr_auc:.3f} frente a {r.base_rate:.3f} sin modelo "
          f"({r.pr_auc_lift:.1f}×)")
    print(f"veredicto: {'supera al azar' if r.beats_chance else 'NO supera al azar'}")

    print("\nprobabilidad estimada, último año con datos:")
    for iso3 in ("ESP", "ITA", "GRC", "ARG"):
        s_ = score_country(iso3, d)
        if s_:
            tag = "" if s_["in_label_set"] else "  (fuera del conjunto etiquetado)"
            print(f"  {iso3} {s_['year']}: {s_['probability']:.2%} "
                  f"(base {s_['base_rate']:.2%}, cobertura {s_['coverage']}){tag}")
    print("\nimportancia por permutación (caída de AUC):")
    for i in r.importances[:6]:
        print(f"  {i['label'][:44]:<46} {i['mean']:+.4f} ± {i['std']:.4f}")

    esp = score_country("ESP", d)

    OUT.mkdir(parents=True, exist_ok=True)
    payload = r.to_dict()
    payload["spain"] = esp
    (OUT / "distress.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\ninforme → {OUT / 'distress.json'}")


if __name__ == "__main__":
    main()
