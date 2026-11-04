"""
AquaSense AI - Sensor Anomaly Detection Module
Uses Scikit-learn IsolationForest to detect multivariate statistical anomalies
in water sensor streams, separate from fixed-threshold limit checks.

DISCLAIMER:
This AI model detects statistical deviations in physical sensor parameters (TDS, pH, turbidity).
It does not claim to detect bacteria, viruses, microbial pathogens, heavy metals,
or chemical pollutants that do not measurably alter these three physical parameters.
"""

import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.ensemble import IsolationForest

class SensorAnomalyDetector:
    def __init__(self, min_samples_for_ml: int = 12, max_buffer_size: int = 150):
        self.min_samples = min_samples_for_ml
        self.max_buffer_size = max_buffer_size
        self.history_buffer: List[List[float]] = []  # Clean baseline training samples [[tds, ph, turbidity], ...]
        self.model: Optional[IsolationForest] = None
        self.baseline_stats: Dict[str, Dict[str, float]] = {}

        # FIX 1: Monotonic sample counter and retrain cadence tracker
        self.total_samples_analyzed: int = 0
        self.eligible_samples_since_retrain: int = 0

        # FIX 2: Consecutive anomaly tracker to prevent buffer contamination while avoiding baseline freeze
        self.consecutive_anomalies: int = 0
        self.max_consecutive_anomalies_before_adaptation: int = 40

        # FIX 3: Realistic sensor resolution standard deviation floors
        # Prevents tiny ADC noise or potentiometer jitter from triggering false positive alerts
        self.min_std_floors = {
            "tds": 8.0,        # ~8 ppm minimum floor (typical municipal fluctuation is 5-15 ppm)
            "ph": 0.25,        # ~0.25 pH units floor (normal drinking water electrode noise is +/- 0.1-0.2)
            "turbidity": 0.6    # ~0.6 simulated units floor (prevents tiny dial adjustments from alarming)
        }

    def add_historical_samples(self, samples: List[List[float]]):
        """Pre-populate or update buffer from DB records."""
        for s in samples:
            if len(s) == 3:
                self.history_buffer.append([float(x) for x in s])
                self.total_samples_analyzed += 1
        if len(self.history_buffer) > self.max_buffer_size:
            self.history_buffer = self.history_buffer[-self.max_buffer_size:]
        self._retrain()
        self.eligible_samples_since_retrain = 0

    def _retrain(self):
        """Fit Isolation Forest and calculate rolling statistical metrics."""
        if len(self.history_buffer) < self.min_samples:
            self.model = None
            return

        X = np.array(self.history_buffer)

        # Calculate means and std deviations
        means = np.mean(X, axis=0)
        stds = np.std(X, axis=0)

        # Apply sensor-resolution-aware standard deviation floors (FIX 3)
        std_tds = max(float(stds[0]), self.min_std_floors["tds"])
        std_ph = max(float(stds[1]), self.min_std_floors["ph"])
        std_turb = max(float(stds[2]), self.min_std_floors["turbidity"])

        self.baseline_stats = {
            "tds": {"mean": float(means[0]), "std": std_tds},
            "ph": {"mean": float(means[1]), "std": std_ph},
            "turbidity": {"mean": float(means[2]), "std": std_turb}
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
        self.total_samples_analyzed += 1

        # FIX 2: Handle warmup safely - build initial clean baseline before ML inference
        if len(self.history_buffer) < self.min_samples:
            self.history_buffer.append(point)
            if len(self.history_buffer) >= self.min_samples:
                self._retrain()
                self.eligible_samples_since_retrain = 0

            return {
                "anomaly_detected": False,
                "anomaly_score": 0.0,
                "parameter": None,
                "z_scores": {"TDS": 0.0, "pH": 0.0, "Turbidity": 0.0},
                "explanation": f"Establishing baseline: {len(self.history_buffer)}/{self.min_samples} readings collected for AI pattern learning.",
                "disclaimer": "AI evaluates multivariate deviations; not a test for microbiological or heavy metal contaminants."
            }

        # Ensure model is ready
        if self.model is None:
            self._retrain()

        # Compute z-scores against rolling baseline with sensor-appropriate floors (FIX 3)
        z_thresholds = {"low": 3.2, "medium": 2.5, "high": 2.0}
        z_limit = z_thresholds.get(sensitivity.lower(), 2.5)

        tds_stats = self.baseline_stats.get("tds", {"mean": tds, "std": self.min_std_floors["tds"]})
        ph_stats = self.baseline_stats.get("ph", {"mean": ph, "std": self.min_std_floors["ph"]})
        turb_stats = self.baseline_stats.get("turbidity", {"mean": turbidity, "std": self.min_std_floors["turbidity"]})

        z_tds = abs(tds - tds_stats["mean"]) / max(tds_stats["std"], self.min_std_floors["tds"])
        z_ph = abs(ph - ph_stats["mean"]) / max(ph_stats["std"], self.min_std_floors["ph"])
        z_turb = abs(turbidity - turb_stats["mean"]) / max(turb_stats["std"], self.min_std_floors["turbidity"])

        z_scores = {"TDS": z_tds, "pH": z_ph, "Turbidity": z_turb}
        max_param, max_z = max(z_scores.items(), key=lambda item: item[1])

        # Evaluate Isolation Forest prediction
        X_test = np.array([point])
        iso_score = float(self.model.decision_function(X_test)[0])
        iso_pred = int(self.model.predict(X_test)[0])  # -1 for anomaly, 1 for normal

        # Combine ML decision with statistical deviation
        is_anomaly = (iso_pred == -1 and max_z >= (z_limit * 0.9)) or (max_z > z_limit)
        normalized_score = round(float(np.clip((1.0 - iso_score) * 50, 0, 100)), 1)

        # FIX 2: Separate incoming readings from clean baseline training samples
        # Do not add confirmed anomalous readings to the clean baseline.
        # Avoid permanently freezing the baseline: if an anomalous condition persists
        # for > max_consecutive_anomalies_before_adaptation (e.g. permanent water source relocation),
        # gradually allow baseline adaptation.
        if is_anomaly:
            self.consecutive_anomalies += 1
            should_add_to_baseline = (self.consecutive_anomalies > self.max_consecutive_anomalies_before_adaptation)
        else:
            self.consecutive_anomalies = 0
            should_add_to_baseline = True

        if should_add_to_baseline:
            self.history_buffer.append(point)
            if len(self.history_buffer) > self.max_buffer_size:
                self.history_buffer.pop(0)

            # FIX 1: Retrain after every 10 new eligible samples
            self.eligible_samples_since_retrain += 1
            if self.eligible_samples_since_retrain >= 10:
                self._retrain()
                self.eligible_samples_since_retrain = 0

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
