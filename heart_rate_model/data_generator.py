# 心率数据生成模块
# 生成模拟的心率测试数据，包括正常数据和异常数据


import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class HeartRateDataGenerator:
    """心率数据生成器"""
    
    def __init__(self, base_rate=75, noise_std=5):
        """
        初始化数据生成器
        
        Args:
            base_rate: 基础心率（默认75次/分钟）
            noise_std: 噪声标准差
        """
        self.base_rate = base_rate
        self.noise_std = noise_std
    
    def generate_normal_data(self, num_points=18):
        """
        生成正常心率数据
        
        Args:
            num_points: 数据点数量（默认18，对应3分钟/10秒间隔）
        
        Returns:
            心率数据列表
        """
        # 生成基础心率数据，添加随机噪声
        heart_rates = self.base_rate + np.random.normal(0, self.noise_std, num_points)
        # 确保心率在合理范围内（50-100）
        heart_rates = np.clip(heart_rates, 50, 100)
        return heart_rates.tolist()
    
    def generate_high_rate_anomaly(self, num_points=18, anomaly_start=5, anomaly_duration=5):
        """
        生成高心率异常数据（持续超过150次/分钟）
        
        Args:
            num_points: 总数据点数量
            anomaly_start: 异常开始位置
            anomaly_duration: 异常持续时长（数据点数）
        
        Returns:
            包含异常的心率数据列表
        """
        heart_rates = self.generate_normal_data(num_points)
        # 在指定位置插入高心率异常
        for i in range(anomaly_start, min(anomaly_start + anomaly_duration, num_points)):
            heart_rates[i] = 150 + np.random.uniform(0, 20)
        return heart_rates
    
    def generate_low_rate_anomaly(self, num_points=18, anomaly_start=5, anomaly_duration=5):
        """
        生成低心率异常数据（持续低于60次/分钟）
        
        Args:
            num_points: 总数据点数量
            anomaly_start: 异常开始位置
            anomaly_duration: 异常持续时长（数据点数）
        
        Returns:
            包含异常的心率数据列表
        """
        heart_rates = self.generate_normal_data(num_points)
        # 在指定位置插入低心率异常
        for i in range(anomaly_start, min(anomaly_start + anomaly_duration, num_points)):
            heart_rates[i] = 50 + np.random.uniform(0, 8)
        return heart_rates
    
    def generate_critical_low_anomaly(self, num_points=18, anomaly_start=8, anomaly_duration=3):
        """
        生成极低心率异常数据（突然降至40次/分钟以下）
        
        Args:
            num_points: 总数据点数量
            anomaly_start: 异常开始位置
            anomaly_duration: 异常持续时长（数据点数）
        
        Returns:
            包含异常的心率数据列表
        """
        heart_rates = self.generate_normal_data(num_points)
        # 在指定位置插入极低心率异常
        for i in range(anomaly_start, min(anomaly_start + anomaly_duration, num_points)):
            heart_rates[i] = 30 + np.random.uniform(0, 8)
        return heart_rates
    
    def generate_dataset_with_timestamps(self, heart_rates, start_time=None):
        """
        为心率数据添加时间戳
        
        Args:
            heart_rates: 心率数据列表
            start_time: 起始时间（默认为当前时间）
        
        Returns:
            包含时间戳和心率的DataFrame
        """
        if start_time is None:
            start_time = datetime.now()
        
        timestamps = [start_time + timedelta(seconds=10*i) for i in range(len(heart_rates))]
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'heart_rate': heart_rates
        })
        
        return df
    
    def generate_mixed_dataset(self, num_batches=10):
        """
        生成混合数据集，包含正常和各种异常数据
        
        Args:
            num_batches: 批次数量
        
        Returns:
            完整的测试数据集DataFrame
        """
        all_data = []
        start_time = datetime.now()
        
        for i in range(num_batches):
            batch_start_time = start_time + timedelta(minutes=3*i)
            
            # 随机选择数据类型
            choice = np.random.choice(['normal', 'high', 'low', 'critical'], p=[0.5, 0.2, 0.15, 0.15])
            
            if choice == 'normal':
                heart_rates = self.generate_normal_data()
                anomaly_type = 'normal'
            elif choice == 'high':
                heart_rates = self.generate_high_rate_anomaly()
                anomaly_type = 'high_rate'
            elif choice == 'low':
                heart_rates = self.generate_low_rate_anomaly()
                anomaly_type = 'low_rate'
            else:
                heart_rates = self.generate_critical_low_anomaly()
                anomaly_type = 'critical_low'
            
            df = self.generate_dataset_with_timestamps(heart_rates, batch_start_time)
            df['batch_id'] = i
            df['anomaly_type'] = anomaly_type
            
            all_data.append(df)
        
        return pd.concat(all_data, ignore_index=True)


if __name__ == "__main__":
    # 测试数据生成器
    generator = HeartRateDataGenerator()
    
    print("=== 正常心率数据 ===")
    normal_data = generator.generate_normal_data()
    print(f"数据点数: {len(normal_data)}")
    print(f"数据: {[f'{x:.1f}' for x in normal_data]}")
    
    print("\n=== 高心率异常数据 ===")
    high_data = generator.generate_high_rate_anomaly()
    print(f"数据: {[f'{x:.1f}' for x in high_data]}")
    
    print("\n=== 低心率异常数据 ===")
    low_data = generator.generate_low_rate_anomaly()
    print(f"数据: {[f'{x:.1f}' for x in low_data]}")
    
    print("\n=== 极低心率异常数据 ===")
    critical_data = generator.generate_critical_low_anomaly()
    print(f"数据: {[f'{x:.1f}' for x in critical_data]}")
    
    print("\n=== 生成混合数据集 ===")
    dataset = generator.generate_mixed_dataset(num_batches=5)
    print(f"\n数据集形状: {dataset.shape}")
    print(f"\n前10条数据:")
    print(dataset.head(10))
    print(f"\n异常类型分布:")
    print(dataset.groupby('anomaly_type').size())
