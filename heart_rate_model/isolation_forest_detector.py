"""
Isolation Forest 基线异常检测器
"""

import numpy as np
import pickle
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class IForestDetector:
    def __init__(self, contamination=0.1, window_size=10):
        self.contamination = contamination
        self.window_size = window_size
        self.model = None
        self.scaler = StandardScaler()

    def _extract_features(self, data):
        data = np.array(data)
        n = len(data)
        feats = []
        for i in range(n):
            w = data[max(0, i - self.window_size + 1):i + 1]
            f = [
                data[i], np.mean(w),
                np.std(w) if len(w) > 1 else 0,
                np.min(w), np.max(w),
                np.max(w) - np.min(w),
                data[i] - data[i - 1] if i > 0 else 0,
                data[i] - 2 * data[i - 1] + data[i - 2] if i > 1 else 0
            ]
            feats.append(f)
        return np.array(feats)

    def fit(self, data):
        if isinstance(data, list):
            arrs = [np.array(d).flatten() for d in data if len(np.array(d).flatten()) > 0]
            data = np.concatenate(arrs) if arrs else np.array([])
        else:
            data = np.array(data).flatten()
        if len(data) == 0:
            raise ValueError("Empty data")
        X = self.scaler.fit_transform(self._extract_features(data))
        self.model = IsolationForest(
            contamination=self.contamination, random_state=42,
            n_estimators=100, max_samples='auto'
        )
        self.model.fit(X)
        print(f"[OK] IForest 训练完成, 样本={len(X)}, 特征维度={X.shape[1]}")

    def predict(self, data):
        if self.model is None:
            raise ValueError("模型未训练")
        X = self.scaler.transform(self._extract_features(np.array(data)))
        return (self.model.predict(X) == -1).astype(int)

    def score(self, data):
        if self.model is None:
            raise ValueError("模型未训练")
        X = self.scaler.transform(self._extract_features(np.array(data)))
        raw = self.model.score_samples(X)
        return 1 - (raw - raw.min()) / (raw.max() - raw.min() + 1e-8)

    def save(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump({'model': self.model, 'scaler': self.scaler,
                         'contamination': self.contamination, 'window_size': self.window_size}, f)
        print(f"[OK] IForest saved: {filepath}")

    @classmethod
    def load(cls, filepath):
        with open(filepath, 'rb') as f:
            d = pickle.load(f)
        det = cls(contamination=d['contamination'], window_size=d['window_size'])
        det.model = d['model']
        det.scaler = d['scaler']
        return det
