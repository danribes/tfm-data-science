"""
Runtime wrapper for the shipped fiscal-stress ML model.

Loads the model artifact produced offline by scripts/train_stress_model.py and
scores a single country-year's feature vector into a 0-100 stress score plus a
percentile against the training cross-country distribution.

Degrades gracefully: if the model artifact is missing, corrupt, or the
supplied feature dict is incomplete, `.available` is False, `.load_error`
explains why, and `.score()` returns an honest unavailable result. This
module never raises to the caller -- the app must keep working without ML.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np

MODEL_PATH = Path(__file__).parent.parent / "models" / "fiscal_stress_model.joblib"
TRAINING_DISTRIBUTION_PATH = Path(__file__).parent.parent / "models" / "training_scores.json"

FEATURES = [
    "debt_gdp", "gdp_growth", "inflation", "unemployment",
    "real_interest_rate", "net_lending_borrowing", "corruption_control",
]


@dataclass
class StressScoreResult:
    score: Optional[float]       # 0-100, None if model unavailable
    percentile: Optional[float]  # vs. training cross-country distribution
    available: bool
    error: Optional[str] = None


class FiscalStressModel:
    def __init__(self):
        self._model = None
        self._training_scores: List[float] = []
        self._load_error: Optional[str] = None
        self._load()

    def _load(self) -> None:
        if not MODEL_PATH.exists():
            self._load_error = f"model artifact not found at {MODEL_PATH}"
            return

        try:
            self._model = joblib.load(MODEL_PATH)
            if TRAINING_DISTRIBUTION_PATH.exists():
                self._training_scores = json.loads(TRAINING_DISTRIBUTION_PATH.read_text())
        except Exception as exc:
            self._load_error = f"failed to load model: {exc}"
            self._model = None

    @property
    def available(self) -> bool:
        return self._model is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def score(self, features: Dict[str, float]) -> StressScoreResult:
        if not self.available:
            return StressScoreResult(score=None, percentile=None, available=False, error=self._load_error)

        missing = [f for f in FEATURES if f not in features]
        if missing:
            return StressScoreResult(score=None, percentile=None, available=False,
                                      error=f"missing features for scoring: {missing}")

        x = np.array([[features[f] for f in FEATURES]])
        raw = float(self._model.predict_proba(x)[0, 1])
        score = max(0.0, min(100.0, raw * 100.0))

        percentile = None
        if self._training_scores:
            percentile = 100.0 * sum(1 for s in self._training_scores if s <= score) / len(self._training_scores)

        return StressScoreResult(score=score, percentile=percentile, available=True, error=None)
