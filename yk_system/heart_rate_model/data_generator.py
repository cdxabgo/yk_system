"""
心率数据生成模块（改进版）
- 支持逐点精确标签（不再使用规则检测器做标注）
- 新增心律不齐异常类型
- 生成器知道每个数据点是否异常以及异常类型
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class HeartRateDataGenerator:
    """心率数据生成器（逐点标签版）"""

    def __init__(self, base_rate=75, noise_std=5):
        self.base_rate = base_rate
        self.noise_std = noise_std

    def generate_normal_data(self, num_points=18):
        """
        生成正常心率数据

        Returns:
            (heart_rates, labels, anomaly_types) — 每点一个标签
        """
        heart_rates = self.base_rate + np.random.normal(0, self.noise_std, num_points)
        heart_rates = np.clip(heart_rates, 50, 100)
        labels = np.zeros(num_points, dtype=int)
        anomaly_types = [''] * num_points
        return heart_rates.tolist(), labels.tolist(), anomaly_types

    def generate_high_rate_anomaly(self, num_points=18, anomaly_start=5, anomaly_duration=5):
        """
        生成高心率异常：anomaly_start 开始持续异常

        Returns:
            (heart_rates, labels, anomaly_types)
        """
        heart_rates, labels, anomaly_types = self._init_from_normal(num_points)

        for i in range(anomaly_start, min(anomaly_start + anomaly_duration, num_points)):
            heart_rates[i] = 150 + np.random.uniform(0, 20)
            labels[i] = 1
            anomaly_types[i] = 'high_rate'

        return heart_rates, labels, anomaly_types

    def generate_low_rate_anomaly(self, num_points=18, anomaly_start=5, anomaly_duration=5):
        """
        生成低心率异常

        Returns:
            (heart_rates, labels, anomaly_types)
        """
        heart_rates, labels, anomaly_types = self._init_from_normal(num_points)

        for i in range(anomaly_start, min(anomaly_start + anomaly_duration, num_points)):
            heart_rates[i] = 50 + np.random.uniform(0, 8)
            labels[i] = 1
            anomaly_types[i] = 'low_rate'

        return heart_rates, labels, anomaly_types

    def generate_critical_low_anomaly(self, num_points=18, anomaly_start=8, anomaly_duration=3):
        """
        生成极低心率异常（≤30 bpm）

        Returns:
            (heart_rates, labels, anomaly_types)
        """
        heart_rates, labels, anomaly_types = self._init_from_normal(num_points)

        for i in range(anomaly_start, min(anomaly_start + anomaly_duration, num_points)):
            heart_rates[i] = 30 + np.random.uniform(0, 8)
            labels[i] = 1
            anomaly_types[i] = 'extreme_value'

        return heart_rates, labels, anomaly_types

    def generate_extreme_high_anomaly(self, num_points=18, anomaly_position=None):
        """
        生成极高心率异常（≥200 bpm）

        Returns:
            (heart_rates, labels, anomaly_types)
        """
        if anomaly_position is None:
            anomaly_position = np.random.randint(5, 15)

        heart_rates, labels, anomaly_types = self._init_from_normal(num_points)

        heart_rates[anomaly_position] = 200 + np.random.uniform(0, 20)
        labels[anomaly_position] = 1
        anomaly_types[anomaly_position] = 'extreme_value'

        return heart_rates, labels, anomaly_types

    def generate_arrhythmia_anomaly(self, num_points=18, jump_positions=None):
        """
        生成心律不齐异常（相邻点心率剧烈变化 ≥30 bpm）

        Returns:
            (heart_rates, labels, anomaly_types)
        """
        heart_rates, labels, anomaly_types = self._init_from_normal(num_points)

        if jump_positions is None:
            # 随机制造 1-2 个突变点
            num_jumps = np.random.randint(1, 3)
            jump_positions = sorted(np.random.choice(range(3, num_points - 1), num_jumps, replace=False))

        for pos in jump_positions:
            if pos > 0:
                current = heart_rates[pos]
                # 制造 ≥30 的变化
                if np.random.random() > 0.5:
                    heart_rates[pos] = current + 30 + np.random.uniform(0, 15)
                else:
                    heart_rates[pos] = max(40, current - 30 - np.random.uniform(0, 15))

                labels[pos] = 1
                anomaly_types[pos] = 'arrhythmia'
                # 突变前的点也标记
                labels[pos - 1] = 1
                anomaly_types[pos - 1] = 'arrhythmia'

        # 限制范围
        heart_rates = np.clip(heart_rates, 30, 220).tolist()

        return heart_rates, labels, anomaly_types

    def generate_gradual_trend_anomaly(self, num_points=18, trend_direction='up'):
        """
        生成趋势异常（心率持续上升/下降）
        """
        heart_rates = []
        labels = np.zeros(num_points, dtype=int)
        anomaly_types = [''] * num_points

        if trend_direction == 'up':
            # 从 75 逐渐升到 130+
            for i in range(num_points):
                heart_rates.append(75 + (i / num_points) * 65 + np.random.normal(0, 3))
        else:
            # 从 90 逐渐降到 45
            for i in range(num_points):
                heart_rates.append(90 - (i / num_points) * 50 + np.random.normal(0, 3))

        heart_rates = np.clip(heart_rates, 30, 220)

        # 趋势后半段标记为异常
        for i in range(int(num_points * 0.6), num_points):
            labels[i] = 1
            anomaly_types[i] = 'trend_anomaly'

        return heart_rates.tolist(), labels.tolist(), anomaly_types

    def _init_from_normal(self, num_points):
        """生成正常基线数据并初始化标签"""
        heart_rates, _, _ = self.generate_normal_data(num_points)
        return heart_rates, np.zeros(num_points, dtype=int), [''] * num_points

    def generate_dataset_with_timestamps(self, heart_rates, labels, anomaly_types,
                                          start_time=None):
        """为心率数据添加时间戳"""
        if start_time is None:
            start_time = datetime.now()

        timestamps = [start_time + timedelta(seconds=10 * i) for i in range(len(heart_rates))]

        return pd.DataFrame({
            'timestamp': timestamps,
            'heart_rate': heart_rates,
            'is_abnormal': labels,
            'anomaly_type': anomaly_types
        })

    def generate_mixed_dataset(self, num_batches=10):
        """
        生成混合数据集（每个 batch 18 条，逐点标签）

        返回的 DataFrame 包含精确的逐点标签，可直接用于训练
        """
        all_data = []
        start_time = datetime.now()

        # 异常类型及其生成概率
        anomaly_types = [
            ('normal', 0.40),
            ('high_rate', 0.18),
            ('low_rate', 0.14),
            ('critical_low', 0.06),
            ('extreme_high', 0.04),
            ('arrhythmia', 0.12),
            ('trend_up', 0.03),
            ('trend_down', 0.03),
        ]

        types, probs = zip(*anomaly_types)

        for i in range(num_batches):
            batch_start_time = start_time + timedelta(minutes=3 * i)
            choice = np.random.choice(types, p=probs)

            if choice == 'normal':
                heart_rates, labels, types_list = self.generate_normal_data()
            elif choice == 'high_rate':
                start = np.random.randint(3, 8)
                dur = np.random.randint(3, 6)
                heart_rates, labels, types_list = self.generate_high_rate_anomaly(
                    anomaly_start=start, anomaly_duration=dur)
            elif choice == 'low_rate':
                start = np.random.randint(3, 8)
                dur = np.random.randint(3, 6)
                heart_rates, labels, types_list = self.generate_low_rate_anomaly(
                    anomaly_start=start, anomaly_duration=dur)
            elif choice == 'critical_low':
                start = np.random.randint(5, 12)
                heart_rates, labels, types_list = self.generate_critical_low_anomaly(
                    anomaly_start=start, anomaly_duration=3)
            elif choice == 'extreme_high':
                pos = np.random.randint(5, 15)
                heart_rates, labels, types_list = self.generate_extreme_high_anomaly(
                    anomaly_position=pos)
            elif choice == 'arrhythmia':
                heart_rates, labels, types_list = self.generate_arrhythmia_anomaly()
            elif choice == 'trend_up':
                heart_rates, labels, types_list = self.generate_gradual_trend_anomaly(trend_direction='up')
            else:  # trend_down
                heart_rates, labels, types_list = self.generate_gradual_trend_anomaly(trend_direction='down')

            df = self.generate_dataset_with_timestamps(
                heart_rates, labels, types_list, batch_start_time)
            df['batch_id'] = i
            df['batch_choice'] = choice  # 记录生成时选的类型（用于调试）

            all_data.append(df)

        result = pd.concat(all_data, ignore_index=True)
        return result


if __name__ == "__main__":
    generator = HeartRateDataGenerator()

    print("=" * 60)
    print("生成器测试（逐点标签版）")
    print("=" * 60)

    # 测试各类型
    for test_type in ['normal', 'high_rate', 'low_rate', 'arrhythmia', 'extreme_high']:
        print(f"\n--- {test_type} ---")
        if test_type == 'normal':
            hr, labels, types = generator.generate_normal_data()
        elif test_type == 'high_rate':
            hr, labels, types = generator.generate_high_rate_anomaly()
        elif test_type == 'low_rate':
            hr, labels, types = generator.generate_low_rate_anomaly()
        elif test_type == 'arrhythmia':
            hr, labels, types = generator.generate_arrhythmia_anomaly()
        elif test_type == 'extreme_high':
            hr, labels, types = generator.generate_extreme_high_anomaly()

        for idx, (h, l, t) in enumerate(zip(hr, labels, types)):
            marker = " ← 异常" if l else ""
            type_info = f" [{t}]" if t else ""
            print(f"  [{idx:2d}] {h:6.1f} bpm  label={l}{type_info}{marker}")

    # 生成混合数据集
    print(f"\n{'=' * 60}")
    print("生成混合数据集")
    print(f"{'=' * 60}")
    df = generator.generate_mixed_dataset(num_batches=10)
    print(f"总数据点: {len(df)}")
    print(f"异常点: {df['is_abnormal'].sum()} "
          f"({df['is_abnormal'].mean() * 100:.1f}%)")

    print("\n异常类型分布:")
    for t, count in df[df['is_abnormal'] == 1]['anomaly_type'].value_counts().items():
        print(f"  {t}: {count}")
