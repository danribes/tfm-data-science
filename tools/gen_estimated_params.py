"""Freeze the estimated structural parameters into the gold slice.

The engine must not import the research layer — it would drag pandas-weight
dependencies into every scenario call and invert the dependency direction. But
the estimates must not be pasted into constants.py either, because a number
copied by hand drifts from the panel that produced it the first time anyone
re-runs the estimation.

So the estimates are written here, once, next to the interval and the sample
that justify them, and constants.py loads the file.

    PYTHONPATH=. python tools/gen_estimated_params.py
"""
from __future__ import annotations

import json
from pathlib import Path

from research import validate

OUT = Path(__file__).resolve().parents[1] / "data" / "gold" / "estimated_params.json"

#: Estimate name in validate.run_all() -> engine constant it replaces.
MAP = {"IPV_LR": "IPV_LR", "IPV_REV": "IPV_REV"}


def main() -> None:
    out = validate.run_all()
    params: dict[str, dict] = {}

    for row in out["comparisons"]:
        const = row.get("constant")
        if const not in MAP:
            continue
        params[const] = {
            "value": round(float(row["coef"]), 4),
            "se": round(float(row["se"]), 4),
            "ci_low": round(float(row["ci_low"]), 4),
            "ci_high": round(float(row["ci_high"]), 4),
            "n": int(row["n"]),
            "n_units": int(row["n_units"]),
            "calibrated_v16": float(row["calibrated"]),
            "verdict": row["verdict"],
            "source": row["source"],
        }

    fp = out.get("fiscal_persistence")
    if fp:
        params["PB_PERSIST"] = {
            "value": round(float(fp["coef"]), 4),
            "se": round(float(fp["se"]), 4),
            "ci_low": round(float(fp["ci_low"]), 4),
            "ci_high": round(float(fp["ci_high"]), 4),
            "n": int(fp["n"]),
            "n_units": int(fp["n_units"]),
            "calibrated_v16": None,
            "verdict": "sin equivalente en la calibración v16",
            "source": "panel fiscal 18 países · 1960+",
        }

    OUT.write_text(
        json.dumps({"vintage": out["vintage"], "params": params}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT}")
    for k, v in params.items():
        cal = v["calibrated_v16"]
        print(f"  {k:12s} {v['value']:7.4f} [{v['ci_low']}, {v['ci_high']}]"
              f"  v16={cal}  {v['verdict']}")


if __name__ == "__main__":
    main()
