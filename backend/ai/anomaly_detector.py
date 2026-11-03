"""
AquaSense AI - Sensor Anomaly Detection Module
Uses Scikit-learn to detect multivariate statistical anomalies in water sensor streams,
separate from fixed-threshold limit checks.

DISCLAIMER:
This AI model detects statistical deviations in physical sensor parameters (TDS, pH, turbidity).
It does not claim to detect bacteria, viruses, microbial pathogens, heavy metals,
or chemical pollutants that do not measurably alter these three physical parameters.
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from sklearn.ensemble import IsolationForest

class SensorAnomalyDetector:
    def __init__(self, min_samples_for_ml: int = 12):
        self.min_samples = min_samples_for_ml
        self.history_buffer: List[List[float]] = [] # [[tds, ph, turbidity], ...]
        self.max_buffer_size = 150
        self.model: Optional[IsolationForest] = None
        self.baseline_stats: Dict[str, Dict[str, float]] = {}

    def add_historical_samples(self, samples: List[List[float]]):
        """Pre-populate or update buffer from DB records."""
        for s in samples:
            if len(s) == 3:
                self.history_buffer.append(s)
        if len(self.history_buffer) > self.max_buffer_size:
            self.history_buffer = self.history_buffer[-self.max_buffer_size:]
        self._retrain()

    def _retrain(self):
        """Fit Isolation Forest and calculate rolling statistical metrics."""
        if len(self.history_buffer) < self.min_samples:
            self.model = None
            return

        X = np.array(self.history_buffer)
        
        # Calculate means and std deviations
        means = np.mean(X, axis=0)
        stds = np.std(X, axis=0)
        # Avoid zero division
        stds = np.where(stds < 1e-4, 1.0, stds)

        self.baseline_stats = {
            "tds": {"mean": float(means[0]), "std": float(stds[0])},
            "ph": {"mean": float(means[1]), "std": float(stds[1])},
            "turbidity": {"mean": float(means[2]), "std": float(stds[2])}
        }

        # Fit IsolationForest
        contamination_rate = 0.08
        self.model = IsolationForest(
            n_estimators=50,
            contamination=contamination_rate,
            random_state=42
        )
        self.model.fit(X)

    def analyze_reading(
        self,
        tds: float,
        ph: float,
        turbidity: float,
        sensitivity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Analyze incoming reading for AI anomaly patterns relative to historical baseline.
        Returns anomaly status, score, primary contributing parameter, and plain-English explanation.
        """
        point = [float(tds), float(ph), float(turbidity)]
        
        # Append to buffer
        self.history_buffer.append(point)
        if len(self.history_buffer) > self.max_buffer_size:
            self.history_buffer.pop(0)

        # Check if enough history has accumulated
        if len(self.history_buffer) < self.min_samples:
            return {
                "anomaly_detected": False,
                "anomaly_score": 0.0,
                "parameter": None,
                "explanation": f"Establishing baseline: {len(self.history_buffer)}/{self.min_samples} readings collected for AI pattern learning.",
                "disclaimer": "AI evaluates multivariate deviations; not a test for microbiological or heavy metal contaminants."
            }

        # Retrain periodically (every 10 samples) or on first availability
        if self.model is None or len(self.history_buffer) % 10 == 0:
            self._retrain()

        # Compute z-scores against rolling baseline
        z_thresholds = {"low": 3.2, "medium": 2.5, "high": 2.0}
        z_limit = z_thresholds.get(sensitivity.lower(), 2.5)

        tds_stats = self.baseline_stats.get("tds", {"mean": tds, "std": 1.0})
        ph_stats = self.baseline_stats.get("ph", {"mean": ph, "std": 1.0})
        turb_stats = self.baseline_stats.get("turbidity", {"mean": turbidity, "std": 1.0})

        z_tds = abs(tds - tds_stats["mean"]) / max(tds_stats["std"], 0.5)
        z_ph = abs(ph - ph_stats["mean"]) / max(ph_stats["std"], 0.1)
        z_turb = abs(turbidity - turb_stats["mean"]) / max(turb_stats["std"], 0.2)

        z_scores = {"TDS": z_tds, "pH": z_ph, "Turbidity": z_turb}
        max_param, max_z = max(z_scores.items(), key=lambda item: item[1])

        # Evaluate Isolation Forest prediction
        X_test = np.array([point])
        # decision_function returns lower values for abnormal points
        iso_score = float(self.model.decision_function(X_test)[0])
        iso_pred = int(self.model.predict(X_test)[0]) # -1 for anomaly, 1 for normal

        # Combine ML decision with statistical deviation
        is_anomaly = (iso_pred == -1 and max_z >= (z_limit * 0.9)) or (max_z > z_limit)

        normalized_score = round(float(np.clip((1.0 - iso_score) * 50, 0, 100)), 1)

        explanation = ""
        if is_anomaly:
            explanation = (
                f"Unusual water-quality pattern detected: {max_param} deviated significantly "
                f"(Z-score: {max_z:.1f}x relative to historical baseline avg of "
                f"{self.baseline_stats[max_param.lower()]['mean']:.1f}). "
                f"Multi-parameter profile diverged from learned steady-state operating patterns."
            )
        else:
            explanation = "Sensor pattern is consistent with historical learned operating baseline."

        return {
            "anomaly_detected": bool(is_anomaly),
            "anomaly_score": normalized_score,
            "parameter": max_param if is_anomaly else None,
            "z_scores": {k: round(v, 2) for k, v in z_scores.items()},
            "explanation": explanation,
            "disclaimer": "Evaluates physical sensor pattern divergence; does not detect bacterial or viral pathogens."
        }


# Global singleton detector
anomaly_detector = SensorAnomalyDetector()

