"""
心率数据生成模块（改进版）
支持逐点精确标签 — 生成器知道每个数据点是否异常
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class HeartRateDataGenerator:
    """心率数据生成器（逐点标签版）"""

    def __init__(self, base_rate=75, noise_std=5):
        self.base_rate = base_rate
        self.noise_std = noise_std

    def _init_normal(self, num_points):
        hr = (self.base_rate + np.random.normal(0, self.noise_std, num_points)).tolist()
        hr = [min(100., max(50., h)) for h in hr]
        return hr, np.zeros(num_points, dtype=int).tolist(), [''] * num_points

    def generate_normal_data(self, num_points=18):
        hr, _, _ = self._init_normal(num_points)
        return hr, [0] * num_points, [''] * num_points

    def generate_high_rate_anomaly(self, num_points=18, anomaly_start=5, anomaly_duration=5):
        hr, labels, types = self._init_normal(num_points)
        for i in range(anomaly_start, min(anomaly_start + anomaly_duration, num_points)):
            hr[i] = 150 + np.random.uniform(0, 20)
            labels[i] = 1
            types[i] = 'high_rate'
        return hr, labels, types

    def generate_low_rate_anomaly(self, num_points=18, anomaly_start=5, anomaly_duration=5):
        hr, labels, types = self._init_normal(num_points)
        for i in range(anomaly_start, min(anomaly_start + anomaly_duration, num_points)):
            hr[i] = 50 + np.random.uniform(0, 8)
            labels[i] = 1
            types[i] = 'low_rate'
        return hr, labels, types

    def generate_critical_low_anomaly(self, num_points=18, anomaly_start=8, anomaly_duration=3):
        hr, labels, types = self._init_normal(num_points)
        for i in range(anomaly_start, min(anomaly_start + anomaly_duration, num_points)):
            hr[i] = 30 + np.random.uniform(0, 8)
            labels[i] = 1
            types[i] = 'extreme_value'
        return hr, labels, types

    def generate_extreme_high_anomaly(self, num_points=18, anomaly_position=None):
        if anomaly_position is None:
            anomaly_position = np.random.randint(5, 15)
        hr, labels, types = self._init_normal(num_points)
        hr[anomaly_position] = 200 + np.random.uniform(0, 20)
        labels[anomaly_position] = 1
        types[anomaly_position] = 'extreme_value'
        return hr, labels, types

    def generate_arrhythmia_anomaly(self, num_points=18, jump_positions=None):
        hr, labels, types = self._init_normal(num_points)
        if jump_positions is None:
            num_jumps = np.random.randint(1, 3)
            jump_positions = sorted(np.random.choice(range(3, num_points - 1), num_jumps, replace=False))
        for pos in jump_positions:
            if pos > 0:
                if np.random.random() > 0.5:
                    hr[pos] = hr[pos] + 30 + np.random.uniform(0, 15)
                else:
                    hr[pos] = max(40, hr[pos] - 30 - np.random.uniform(0, 15))
                labels[pos] = 1
                labels[pos - 1] = 1
                types[pos] = 'arrhythmia'
                types[pos - 1] = 'arrhythmia'
        return [min(220., max(30., h)) for h in hr], labels, types

    def generate_gradual_trend_anomaly(self, num_points=18, trend_direction='up'):
        hr, labels, types = self._init_normal(num_points)
        if trend_direction == 'up':
            for i in range(num_points):
                hr[i] = 75 + (i / num_points) * 65 + np.random.normal(0, 3)
        else:
            for i in range(num_points):
                hr[i] = 90 - (i / num_points) * 50 + np.random.normal(0, 3)
        hr = [min(220., max(30., h)) for h in hr]
        for i in range(int(num_points * 0.6), num_points):
            labels[i] = 1
            types[i] = 'trend_anomaly'
        return hr, labels, types

    def generate_dataset_with_timestamps(self, hr, labels, types, start_time=None):
        if start_time is None:
            start_time = datetime.now()
        return pd.DataFrame({
            'timestamp': [start_time + timedelta(seconds=10 * i) for i in range(len(hr))],
            'heart_rate': hr,
            'is_abnormal': labels,
            'anomaly_type': types
        })

    def generate_mixed_dataset(self, num_batches=10):
        all_data = []
        start_time = datetime.now()
        gen_types = [
            ('normal', 0.40), ('high_rate', 0.18), ('low_rate', 0.14),
            ('critical_low', 0.06), ('extreme_high', 0.04),
            ('arrhythmia', 0.12), ('trend_up', 0.03), ('trend_down', 0.03),
        ]
        names, probs = zip(*gen_types)

        for i in range(num_batches):
            t0 = start_time + timedelta(minutes=3 * i)
            choice = np.random.choice(names, p=probs)

            if choice == 'normal':
                hr, labels, types = self.generate_normal_data()
            elif choice == 'high_rate':
                hr, labels, types = self.generate_high_rate_anomaly(
                    anomaly_start=np.random.randint(3, 8), anomaly_duration=np.random.randint(3, 6))
            elif choice == 'low_rate':
                hr, labels, types = self.generate_low_rate_anomaly(
                    anomaly_start=np.random.randint(3, 8), anomaly_duration=np.random.randint(3, 6))
            elif choice == 'critical_low':
                hr, labels, types = self.generate_critical_low_anomaly(anomaly_start=np.random.randint(5, 12))
            elif choice == 'extreme_high':
                hr, labels, types = self.generate_extreme_high_anomaly(anomaly_position=np.random.randint(5, 15))
            elif choice == 'arrhythmia':
                hr, labels, types = self.generate_arrhythmia_anomaly()
            elif choice == 'trend_up':
                hr, labels, types = self.generate_gradual_trend_anomaly(trend_direction='up')
            else:
                hr, labels, types = self.generate_gradual_trend_anomaly(trend_direction='down')

            df = self.generate_dataset_with_timestamps(hr, labels, types, t0)
            df['batch_id'] = i
            df['batch_choice'] = choice
            all_data.append(df)

        return pd.concat(all_data, ignore_index=True)


if __name__ == "__main__":
    g = HeartRateDataGenerator()
    df = g.generate_mixed_dataset(num_batches=50)
    print(f"数据点: {len(df)}, 异常: {df['is_abnormal'].sum()} ({df['is_abnormal'].mean()*100:.1f}%)")
    print("异常类型分布:")
    print(df[df['is_abnormal'] == 1]['anomaly_type'].value_counts())
