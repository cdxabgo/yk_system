# 异常检测器

import numpy as np
import pandas as pd
from typing import List, Dict


class EnhancedAnomalyDetector:
    
    def __init__(self):
        """初始化检测器参数"""
        # 心率过快：连续3条以上 >150
        self.high_rate_threshold = 150
        self.high_rate_consecutive = 3
        
        # 心率过慢：连续2条以上 <60
        self.low_rate_threshold = 60
        self.low_rate_consecutive = 2
        
        # 极值：>=200 或 <=30
        self.extreme_high = 200
        self.extreme_low = 30
        
        # 心律不齐：相邻差值 >=30
        self.arrhythmia_threshold = 30
    
    def detect_high_rate(self, heart_rates: np.ndarray) -> List[int]:
        """
        检测高心率异常：持续超过150次/分钟且连续3条以上
        
        参数:
            heart_rates: 心率数据数组
            
        返回:
            异常数据的索引列表
        """
        anomalies = []
        consecutive = 0
        
        for i, rate in enumerate(heart_rates):
            if rate > self.high_rate_threshold:
                consecutive += 1
                # 只有达到连续要求才标记
                if consecutive >= self.high_rate_consecutive:
                    anomalies.append(i)
            else:
                consecutive = 0
        
        return anomalies
    
    def detect_low_rate(self, heart_rates: np.ndarray) -> List[int]:
        """
        检测低心率异常：持续低于60次/分钟且连续2条以上
        
        参数:
            heart_rates: 心率数据数组
            
        返回:
            异常数据的索引列表
        """
        anomalies = []
        consecutive = 0
        
        for i, rate in enumerate(heart_rates):
            if rate < self.low_rate_threshold:
                consecutive += 1
                # 只有达到连续要求才标记
                if consecutive >= self.low_rate_consecutive:
                    anomalies.append(i)
            else:
                consecutive = 0
        
        return anomalies
    
    def detect_extreme_value(self, heart_rates: np.ndarray) -> List[int]:
        """
        检测极值异常：心率 >=200 或 <=30
        
        参数:
            heart_rates: 心率数据数组
            
        返回:
            异常数据的索引列表
        """
        anomalies = []
        
        for i, rate in enumerate(heart_rates):
            if rate >= self.extreme_high or rate <= self.extreme_low:
                anomalies.append(i)
        
        return anomalies
    
    def detect_arrhythmia(self, heart_rates: np.ndarray) -> List[int]:
        """
        检测心律不齐：相邻数据差值 >=30次/分钟
        
        参数:
            heart_rates: 心率数据数组
            
        返回:
            异常数据的索引列表
        """
        anomalies = []
        
        for i in range(1, len(heart_rates)):
            diff = abs(heart_rates[i] - heart_rates[i-1])
            if diff >= self.arrhythmia_threshold:
                # 标记发生突变的两个点
                anomalies.extend([i-1, i])
        
        return sorted(list(set(anomalies)))
    
    def detect_all(self, heart_rates: np.ndarray) -> Dict:
        """
        执行所有异常检测
        
        参数:
            heart_rates: 心率数据数组
            
        返回:
            包含所有检测结果的字典
        """
        results = {
            'high_rate': self.detect_high_rate(heart_rates),
            'low_rate': self.detect_low_rate(heart_rates),
            'extreme_value': self.detect_extreme_value(heart_rates),
            'arrhythmia': self.detect_arrhythmia(heart_rates)
        }
        
        # 合并所有异常索引
        all_anomalies = set()
        for anomaly_list in results.values():
            all_anomalies.update(anomaly_list)
        results['all'] = sorted(list(all_anomalies))
        
        return results
    
    def analyze_dataframe(self, df: pd.DataFrame, 
                         heart_rate_column: str = 'heart_rate_filtered') -> pd.DataFrame:
        """
        分析DataFrame中的心率数据
        
        参数:
            df: 包含心率数据的DataFrame
            heart_rate_column: 心率列名
            
        返回:
            添加了异常标记的DataFrame
        """
        df_copy = df.copy()
        
        # 初始化异常列
        df_copy['is_anomaly'] = False
        df_copy['anomaly_type'] = ''
        df_copy['anomaly_details'] = ''
        
        # 按批次处理
        if 'batch_id' in df_copy.columns:
            for batch_id in df_copy['batch_id'].unique():
                batch_mask = df_copy['batch_id'] == batch_id
                batch_indices = df_copy[batch_mask].index
                heart_rates = df_copy.loc[batch_mask, heart_rate_column].values
                
                # 执行检测
                results = self.detect_all(heart_rates)
                
                # 标记异常
                for local_idx in results['all']:
                    global_idx = batch_indices[local_idx]
                    df_copy.at[global_idx, 'is_anomaly'] = True
                    
                    # 确定异常类型
                    types = []
                    if local_idx in results['high_rate']:
                        types.append('高心率')
                    if local_idx in results['low_rate']:
                        types.append('低心率')
                    if local_idx in results['extreme_value']:
                        types.append('极值')
                    if local_idx in results['arrhythmia']:
                        types.append('心律不齐')
                    
                    df_copy.at[global_idx, 'anomaly_type'] = ', '.join(types)
                    
                    # 添加详细信息
                    rate = heart_rates[local_idx]
                    details = []
                    if local_idx in results['high_rate']:
                        details.append(f'心率{rate:.1f}>150(连续{self.high_rate_consecutive}+)')
                    if local_idx in results['low_rate']:
                        details.append(f'心率{rate:.1f}<60(连续{self.low_rate_consecutive}+)')
                    if local_idx in results['extreme_value']:
                        if rate >= self.extreme_high:
                            details.append(f'极高值{rate:.1f}≥200')
                        else:
                            details.append(f'极低值{rate:.1f}≤30')
                    if local_idx in results['arrhythmia']:
                        if local_idx > 0:
                            diff = abs(rate - heart_rates[local_idx-1])
                            details.append(f'心律不齐(变化{diff:.1f}≥30)')
                    
                    df_copy.at[global_idx, 'anomaly_details'] = '; '.join(details)
        else:
            # 单批次处理
            heart_rates = df_copy[heart_rate_column].values
            results = self.detect_all(heart_rates)
            
            for idx in results['all']:
                df_copy.at[df_copy.index[idx], 'is_anomaly'] = True
                
                types = []
                if idx in results['high_rate']:
                    types.append('高心率')
                if idx in results['low_rate']:
                    types.append('低心率')
                if idx in results['extreme_value']:
                    types.append('极值')
                if idx in results['arrhythmia']:
                    types.append('心律不齐')
                
                df_copy.at[df_copy.index[idx], 'anomaly_type'] = ', '.join(types)
        
        return df_copy
    
    def get_summary(self, df: pd.DataFrame) -> Dict:
        """
        获取检测摘要统计
        
        参数:
            df: 检测后的DataFrame
            
        返回:
            统计摘要字典
        """
        total = len(df)
        anomalies = df[df['is_anomaly'] == True]
        
        summary = {
            'total_records': total,
            'total_anomalies': len(anomalies),
            'anomaly_rate': len(anomalies) / total if total > 0 else 0,
            'high_rate_count': len(anomalies[anomalies['anomaly_type'].str.contains('高心率', na=False)]),
            'low_rate_count': len(anomalies[anomalies['anomaly_type'].str.contains('低心率', na=False)]),
            'extreme_value_count': len(anomalies[anomalies['anomaly_type'].str.contains('极值', na=False)]),
            'arrhythmia_count': len(anomalies[anomalies['anomaly_type'].str.contains('心律不齐', na=False)])
        }
        
        return summary


if __name__ == '__main__':
    # 测试代码
    detector = EnhancedAnomalyDetector()
    
    # 测试数据
    test_data = np.array([
        75, 80, 78,  # 正常
        155, 160, 165, 158,  # 高心率（连续4条>150）
        80, 75,  # 正常
        58, 55, 54,  # 低心率（连续3条<60）
        75, 80,  # 正常
        85, 180,  # 心律不齐（差值95）
        75, 80,  # 正常
        210,  # 极高值
        75, 80,  # 正常
        25,  # 极低值
    ])
    
    results = detector.detect_all(test_data)
    
    print("=" * 70)
    print("增强版异常检测测试")
    print("=" * 70)
    print(f"测试数据: {test_data}")
    print(f"\n检测结果:")
    print(f"  高心率异常 (连续3+条>150): {results['high_rate']}")
    print(f"  低心率异常 (连续2+条<60): {results['low_rate']}")
    print(f"  极值异常 (≥200或≤30): {results['extreme_value']}")
    print(f"  心律不齐 (相邻差≥30): {results['arrhythmia']}")
    print(f"  所有异常索引: {results['all']}")
