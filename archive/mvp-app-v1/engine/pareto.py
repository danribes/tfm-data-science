from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize

from data.models import FetchResult
from engine.scenario import ScenarioLevers, run_scenario

LEVER_BOUNDS = {
    "tax_wedge_delta_pp": (-5.0, 5.0),
    "primary_balance_target_pct": (-4.0, 4.0),
    "indexation_delta_pp": (-1.5, 1.0),
    "public_wage_bill_share_delta": (-0.10, 0.10),
}


@dataclass
class ParetoPoint:
    levers: Dict[str, float]
    objectives: Dict[str, float]


def _shift_allocation(base_shares: Dict[str, float], wage_bill_delta: float) -> Dict[str, float]:
    shares = dict(base_shares)
    shares["public_wage_bill"] = max(0.0, shares["public_wage_bill"] + wage_bill_delta)
    other_keys = [k for k in shares if k != "public_wage_bill"]
    remaining = 1.0 - shares["public_wage_bill"]
    other_sum = sum(shares[k] for k in other_keys)
    if other_sum <= 0:
        raise ValueError("allocation shares collapsed to zero while shifting public_wage_bill")
    for k in other_keys:
        shares[k] = shares[k] / other_sum * remaining
    return shares


class _ScenarioProblem(Problem):
    def __init__(self, country_iso3: str, panel: Dict[str, FetchResult], base_levers: ScenarioLevers,
                 lever_bounds: Dict[str, Tuple[float, float]]):
        self.country_iso3 = country_iso3
        self.panel = panel
        self.base_levers = base_levers
        self.lever_keys = list(lever_bounds.keys())
        xl = np.array([lever_bounds[k][0] for k in self.lever_keys])
        xu = np.array([lever_bounds[k][1] for k in self.lever_keys])
        super().__init__(n_var=len(self.lever_keys), n_obj=3, n_ieq_constr=0, xl=xl, xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        f1 = np.zeros(X.shape[0])
        f2 = np.zeros(X.shape[0])
        f3 = np.zeros(X.shape[0])

        for i, row in enumerate(X):
            levers = ScenarioLevers(
                horizon_years=self.base_levers.horizon_years,
                tax_wedge_delta_pp=row[self.lever_keys.index("tax_wedge_delta_pp")],
                primary_balance_target_pct=row[self.lever_keys.index("primary_balance_target_pct")],
                indexation_delta_pp=row[self.lever_keys.index("indexation_delta_pp")],
                allocation_shares=_shift_allocation(self.base_levers.allocation_shares,
                                                     row[self.lever_keys.index("public_wage_bill_share_delta")]),
            )
            result = run_scenario(self.country_iso3, self.panel, levers)
            f1[i] = result.debt_path[-1].debt_gdp_pct
            last_alloc = result.fiscal_space_by_year[-1].allocations_pct_gdp
            f2[i] = -(last_alloc["health"] + last_alloc["education"])
            f3[i] = -(last_alloc["welfare"] + last_alloc["public_wage_bill"])

        out["F"] = np.column_stack([f1, f2, f3])


def compute_pareto_frontier(country_iso3: str, panel: Dict[str, FetchResult], base_levers: ScenarioLevers,
                             lever_bounds: Dict[str, Tuple[float, float]] = None,
                             population_size: int = 40, generations: int = 30) -> List[ParetoPoint]:
    bounds = lever_bounds or LEVER_BOUNDS
    problem = _ScenarioProblem(country_iso3, panel, base_levers, bounds)
    algorithm = NSGA2(pop_size=population_size)
    res = minimize(problem, algorithm, ("n_gen", generations), seed=1, verbose=False)

    keys = list(bounds.keys())
    X = res.X if res.X.ndim == 2 else res.X.reshape(1, -1)
    F = res.F if res.F.ndim == 2 else res.F.reshape(1, -1)

    points = []
    for x_row, f_row in zip(X, F):
        levers = {k: float(v) for k, v in zip(keys, x_row)}
        objectives = {
            "final_debt_gdp_pct": float(f_row[0]),
            "health_education_funding_pct_gdp": float(-f_row[1]),
            "welfare_wagebill_pct_gdp": float(-f_row[2]),
        }
        points.append(ParetoPoint(levers=levers, objectives=objectives))
    return points
