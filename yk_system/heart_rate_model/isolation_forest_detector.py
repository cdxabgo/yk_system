"""
Isolation Forest 基线异常检测器

作为传统机器学习方法的对比基线。
无监督方法，不需要标签，通过随机划分来隔离异常点。
"""

import numpy as np
import pandas as pd
import pickle
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class IForestDetector:
    """Isolation Forest 异常检测器"""

    def __init__(self, contamination=0.1, window_size=10):
        """
        Args:
            contamination: 预期异常比例
            window_size: 滑动窗口大小（用于提取统计特征）
        """
        self.contamination = contamination
        self.window_size = window_size
        self.model = None
        self.scaler = StandardScaler()

    def _extract_window_features(self, data):
        """
        从一维心率序列提取窗口统计特征

        Returns: (n_samples, n_features) 特征矩阵
        """
        data = np.array(data)
        n = len(data)

        features = []
        for i in range(n):
            window_start = max(0, i - self.window_size + 1)
            window = data[window_start:i + 1]

            feats = [
                data[i],                          # 当前心率
                np.mean(window),                  # 窗口均值
                np.std(window) if len(window) > 1 else 0,  # 窗口标准差
                np.min(window),                   # 窗口最小值
                np.max(window),                   # 窗口最大值
                np.max(window) - np.min(window),  # 窗口极差
            ]

            # 变化率特征
            if i > 0:
                feats.append(data[i] - data[i - 1])          # 一阶差分
                if i > 1:
                    feats.append(data[i] - 2 * data[i - 1] + data[i - 2])  # 二阶差分
                else:
                    feats.append(0)
            else:
                feats.extend([0, 0])

            features.append(feats)

        return np.array(features)

    def fit(self, data):
        """
        训练 Isolation Forest（无监督，不需要标签）

        Args:
            data: 1D array of heart rates，或 list of 1D arrays
        """
        if isinstance(data, list):
            arrs = [np.array(d).flatten() for d in data if len(np.array(d).flatten()) > 0]
            if len(arrs) == 0:
                raise ValueError("Empty data")
            data = np.concatenate(arrs)
        else:
            data = np.array(data).flatten()

        # 提取特征
        X = self._extract_window_features(data)
        X = self.scaler.fit_transform(X)

        # 训练
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto'
        )
        self.model.fit(X)

        print(f"[OK] Isolation Forest 训练完成")
        print(f"  样本数: {len(X)}, 特征维度: {X.shape[1]}")
        print(f"  预期异常比例: {self.contamination * 100:.1f}%")

    def predict(self, data):
        """
        预测异常

        Args:
            data: 1D array of heart rates

        Returns:
            binary array (0=正常, 1=异常)
        """
        if self.model is None:
            raise ValueError("模型未训练")

        data = np.array(data)
        X = self._extract_window_features(data)
        X = self.scaler.transform(X)

        # IsolationForest: -1=异常, 1=正常
        raw_pred = self.model.predict(X)
        predictions = (raw_pred == -1).astype(int)

        return predictions

    def score(self, data):
        """
        返回异常分数 (0-1, 越高越异常)
        """
        if self.model is None:
            raise ValueError("模型未训练")

        data = np.array(data)
        X = self._extract_window_features(data)
        X = self.scaler.transform(X)

        # Score: 越小越异常
        raw_scores = self.model.score_samples(X)
        # 归一化到 [0, 1]，越高越异常
        scores = 1 - (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min() + 1e-8)
        return scores

    def save(self, filepath):
        """保存模型"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'contamination': self.contamination,
                'window_size': self.window_size
            }, f)
        print(f"[OK] Isolation Forest 已保存: {filepath}")

    @classmethod
    def load(cls, filepath):
        """加载模型"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        detector = cls(
            contamination=data['contamination'],
            window_size=data['window_size']
        )
        detector.model = data['model']
        detector.scaler = data['scaler']
        return detector


if __name__ == '__main__':
    from data_generator import HeartRateDataGenerator
    from data_filter import HeartRateFilter

    print("=" * 60)
    print("Isolation Forest 测试")
    print("=" * 60)

    generator = HeartRateDataGenerator()
    filter_obj = HeartRateFilter()

    # 生成混合数据用于训练（IsolationForest 无监督，混合数据也可以）
    all_data = []
    for _ in range(200):
        rates, _, _ = generator.generate_normal_data(18)
        all_data.append(rates)

    # 训练
    detector = IForestDetector(contamination=0.1, window_size=10)
    detector.fit(all_data)

    # 测试
    print("\n--- 正常数据 ---")
    normal, _, _ = generator.generate_normal_data(18)
    pred_n = detector.predict(normal)
    scores_n = detector.score(normal)
    print(f"误报: {pred_n.sum()}/{len(pred_n)}, 分数均值: {scores_n.mean():.4f}")

    print("\n--- 高心率异常 ---")
    abnormal, labels, _ = generator.generate_high_rate_anomaly(18)
    filtered = filter_obj.comprehensive_filter(abnormal)
    pred_a = detector.predict(filtered)
    scores_a = detector.score(filtered)
    print(f"检出: {pred_a.sum()}/{len(pred_a)}, 分数均值: {scores_a.mean():.4f}")
    print(f"真实标签: {sum(labels)}/{len(labels)}")

    print("\n--- 保存 ---")
    os.makedirs('output/models', exist_ok=True)
    detector.save('output/models/isolation_forest.pkl')
