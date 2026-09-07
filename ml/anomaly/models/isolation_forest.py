import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, List, Any, Tuple

class IsolationForestAnomalyModel:
    """
    Wrapper for scikit-learn IsolationForest anomaly detection model.
    """
    def __init__(self, n_estimators: int = 100, contamination: float = 0.05, random_state: int = 42):
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray) -> "IsolationForestAnomalyModel":
        """Fits the Isolation Forest on feature matrix X."""
        if X.size == 0:
            return self
        self.model.fit(X)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Returns -1 for outliers/anomalies, 1 for inliers."""
        if not self.is_fitted:
            self.fit(X)
        return self.model.predict(X)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Returns anomaly decision scores (lower means more anomalous)."""
        if not self.is_fitted:
            self.fit(X)
        return self.model.decision_function(X)

    def fit_predict_confidence(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fits model and returns (predictions, confidence_scores).
        Confidence scores scale between 0.70 and 0.99 for detected anomalies (-1).
        """
        if X.shape[0] == 0:
            return np.array([]), np.array([])

        self.fit(X)
        preds = self.predict(X)
        scores = self.decision_function(X)

        confidences = np.zeros_like(scores)
        for i in range(len(scores)):
            if preds[i] == -1:
                # Scikit-learn decision_function score for outliers is negative (e.g. -0.3 to -0.01)
                score = scores[i]
                conf = min(0.99, max(0.70, 0.50 - score))
                confidences[i] = round(float(conf), 2)
            else:
                confidences[i] = 0.0

        return preds, confidences
