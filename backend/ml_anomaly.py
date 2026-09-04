"""Anomaly detection for water quality readings.

Uses a two-layer strategy:
  1. Physically-sound threshold checks (a pH of 14 or DO of -1 is always wrong).
  2. A periodically-retrained Isolation Forest over the recent history that
     flags *statistical* outliers — readings that are unusual for this
     particular body of water even if they pass the physical bounds.

The Isolation Forest is a classic unsupervised learner: it isolates anomalies
by how few splits it takes to separate a point from the rest — ideal for
unlabeled sensor streams.
"""
from datetime import datetime, timezone

import numpy as np
from sklearn.ensemble import IsolationForest

# ---------------------------------------------------------------------------
# Physical / regulatory thresholds. Values outside these are anomalies outright.
# ---------------------------------------------------------------------------
PARAMETER_RANGES = {
    "ph":               (6.5, 8.5),    # WHO / CPCB drinking-water guidance
    "temperature":      (0.0, 45.0),   # °C — beyond this the sensor/biology is suspect
    "turbidity":        (0.0, 100.0),  # NTU — 100+ is severely polluted
    "dissolved_oxygen": (0.0, 14.0),   # mg/L — 14 is near saturation at 0°C
    "conductivity":     (0.0, 5000.0), # µS/cm
    "tds":              (0.0, 5000.0), # mg/L
}

# Beyond this threshold the parameter is dangerous regardless of local baseline.
SEVERITY_RANGES = {
    "ph":               {"low": 6.0,  "high": 9.0,  "critical": 5.0},
    "temperature":      {"low": 4.0,  "high": 35.0, "critical": 40.0},
    "turbidity":        {"high": 5.0, "critical": 25.0},   # NTU
    "dissolved_oxygen": {"low": 4.0,  "critical": 2.0},    # mg/L
    "conductivity":     {"high": 1500.0, "critical": 3000.0},
    "tds":              {"high": 500.0,  "critical": 1000.0},
}

# Order used to build the feature vector fed to the model.
FEATURE_COLUMNS = ["ph", "temperature", "turbidity", "dissolved_oxygen", "conductivity", "tds"]

# Number of recent readings the forest is trained on, and how often we retrain.
WINDOW_SIZE = 500
CONTAMINATION = 0.05  # expected fraction of anomalies in a healthy stream


class AnomalyDetector:
    def __init__(self):
        self._model = None
        self._train_features = None  # (N, 6) array the forest was fit on
        self._last_train_at = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def analyze(self, reading_values: dict, recent_history: list) -> dict:
        """Classify a single reading.

        `reading_values` is a dict of parameter->value for THIS reading.
        `recent_history` is a list of dicts (parameter->value) from prior
        readings, used to (re)train the statistical model.

        Returns {"is_anomaly": bool, "reason": str|None, "severity": str|None,
                 "parameter": str|None}.
        """
        self._maybe_retrain(recent_history)

        anomalies = []
        # 1) Physical threshold violations — hard, explainable.
        for param, (lo, hi) in PARAMETER_RANGES.items():
            val = reading_values.get(param)
            if val is None:
                continue
            if val < lo or val > hi:
                anomalies.append(
                    (param, f"{param} value {val:.2f} is outside the safe range [{lo}, {hi}]",
                     self._severity_for(param, val))
                )

        # 2) Statistical outlier via the trained forest.
        stat = self._statistical_check(reading_values)
        if stat is not None:
            param, reason, severity = stat
            anomalies.append((param, reason, severity))

        if not anomalies:
            return {"is_anomaly": False, "reason": None, "severity": None, "parameter": None}

        # Pick the most severe anomaly to surface.
        anomalies.sort(key=lambda a: self._severity_rank(a[2]))
        param, reason, severity = anomalies[-1]
        return {"is_anomaly": True, "reason": reason, "severity": severity, "parameter": param}

    # ------------------------------------------------------------------
    # Statistical (Isolation Forest) layer
    # ------------------------------------------------------------------
    def _statistical_check(self, reading_values: dict):
        if self._model is None or self._train_features is None:
            return None

        vec = self._to_vector(reading_values)
        if vec is None or not np.isfinite(vec).all():
            return None

        score = self._model.decision_function(vec.reshape(1, -1))[0]
        if score < -0.1:  # negative => more anomalous (decision func, higher is normal)
            # Identify which parameter contributes most to the deviation.
            param = self._biggest_deviation(vec)
            if param is not None:
                val = reading_values.get(param)
                return (
                    param,
                    f"{param} value {val:.2f} deviates from the local baseline "
                    f"(statistical outlier)",
                    self._severity_for(param, val),
                )
        return None

    def _biggest_deviation(self, vec):
        """Return the feature with the largest standardized deviation."""
        if self._train_features is None:
            return None
        mean = self._train_features.mean(axis=0)
        std = self._train_features.std(axis=0) + 1e-9
        z = np.abs((vec - mean) / std)
        idx = int(np.argmax(z))
        return FEATURE_COLUMNS[idx]

    def _maybe_retrain(self, history):
        """Retrain every WINDOW_SIZE readings (or on first call)."""
        if not history:
            return
        now = datetime.now(timezone.utc)
        should_train = (
            self._model is None
            or len(history) >= WINDOW_SIZE
            and (self._last_train_at is None
                 or (now - self._last_train_at).total_seconds() > 3600)
        )
        if not should_train:
            return

        matrix = []
        for row in history[:WINDOW_SIZE]:
            vec = self._to_vector(row)
            if vec is not None and np.isfinite(vec).all():
                matrix.append(vec)
        if len(matrix) < 30:  # need a minimum sample to fit meaningfully
            return

        X = np.array(matrix)
        self._model = IsolationForest(
            contamination=CONTAMINATION,
            n_estimators=100,
            random_state=42,
        ).fit(X)
        self._train_features = X
        self._last_train_at = now

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _to_vector(row):
        """Build the 6-feature vector, or None if it has too few known values."""
        vals = [row.get(c) for c in FEATURE_COLUMNS]
        known = [v for v in vals if v is not None]
        if len(known) < 4:  # too sparse to be meaningful
            return None
        return np.array([v if v is not None else float(np.nanmean(known))
                         for v in vals], dtype=float)

    @staticmethod
    def _severity_for(param, val):
        ranges = SEVERITY_RANGES.get(param, {})
        critical = ranges.get("critical")
        high = ranges.get("high")
        low = ranges.get("low")
        if critical is not None and val <= critical:
            return "critical"
        if critical is not None and val >= critical and param in ("temperature", "ph", "turbidity", "conductivity", "tds"):
            return "critical"
        if high is not None and val >= high:
            return "high"
        if low is not None and val <= low:
            return "high"
        return "medium"

    @staticmethod
    def _severity_rank(sev):
        return {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(sev, 1)


# Shared singleton so the model state persists across requests.
detector = AnomalyDetector()
