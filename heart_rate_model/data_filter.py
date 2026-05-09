# 数据滤波清洗模块
# 使用数字信号处理技术对心率数据进行滤波和清洗


import numpy as np
import pandas as pd
from scipy import signal


class HeartRateFilter:
    """心率数据滤波器"""
    
    def __init__(self, sampling_interval=10):
        """
        初始化滤波器
        
        Args:
            sampling_interval: 采样间隔（秒）
        """
        self.sampling_interval = sampling_interval
        self.sampling_rate = 1.0 / sampling_interval  # 采样率：0.1 Hz
    
    def remove_outliers(self, heart_rates, lower_bound=30, upper_bound=220):
        """
        移除异常值（超出生理范围的数据）
        
        Args:
            heart_rates: 心率数据数组
            lower_bound: 下界（默认30次/分钟）
            upper_bound: 上界（默认220次/分钟）
        
        Returns:
            清洗后的心率数据
        """
        cleaned_data = np.array(heart_rates, dtype=float)
        
        # 标记超出范围的值为NaN
        mask = (cleaned_data < lower_bound) | (cleaned_data > upper_bound)
        cleaned_data[mask] = np.nan
        
        # 使用线性插值填充NaN值
        if np.any(np.isnan(cleaned_data)):
            valid_indices = np.where(~np.isnan(cleaned_data))[0]
            if len(valid_indices) > 0:
                cleaned_data = np.interp(
                    np.arange(len(cleaned_data)),
                    valid_indices,
                    cleaned_data[valid_indices]
                )
        
        return cleaned_data
    
    def median_filter(self, heart_rates, kernel_size=3):
        """
        中值滤波，去除脉冲噪声（如70->200->75）
        
        Args:
            heart_rates: 心率数据数组
            kernel_size: 滤波器窗口大小（默认3）
        
        Returns:
            滤波后的心率数据
        """
        if len(heart_rates) < kernel_size:
            return heart_rates
        
        # 使用scipy的中值滤波
        filtered_data = signal.medfilt(heart_rates, kernel_size=kernel_size)
        return filtered_data
    
    def moving_average_filter(self, heart_rates, window_size=3):
        """
        移动平均滤波，平滑数据
        
        Args:
            heart_rates: 心率数据数组
            window_size: 窗口大小（默认3）
        
        Returns:
            滤波后的心率数据
        """
        if len(heart_rates) < window_size:
            return heart_rates
        
        # 使用卷积实现移动平均
        kernel = np.ones(window_size) / window_size
        filtered_data = np.convolve(heart_rates, kernel, mode='same')
        
        # 边界处理：使用原始数据
        edge = window_size // 2
        filtered_data[:edge] = heart_rates[:edge]
        filtered_data[-edge:] = heart_rates[-edge:]
        
        return filtered_data
    
    def butter_lowpass_filter(self, heart_rates, cutoff_freq=0.02, order=2):
        """
        巴特沃斯低通滤波器，去除高频噪声
        
        Args:
            heart_rates: 心率数据数组
            cutoff_freq: 截止频率（Hz，默认0.02）
            order: 滤波器阶数（默认2）
        
        Returns:
            滤波后的心率数据
        """
        if len(heart_rates) < 4:
            return heart_rates
        
        # 归一化截止频率
        nyquist_freq = 0.5 * self.sampling_rate
        normal_cutoff = cutoff_freq / nyquist_freq
        
        # 设计巴特沃斯滤波器
        b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
        
        # 应用滤波器（使用filtfilt避免相位失真）
        filtered_data = signal.filtfilt(b, a, heart_rates)
        
        return filtered_data
    
    def comprehensive_filter(self, heart_rates, use_median=True, use_ma=True, use_lowpass=False):
        """
        综合滤波处理流程
        
        Args:
            heart_rates: 心率数据数组
            use_median: 是否使用中值滤波
            use_ma: 是否使用移动平均滤波
            use_lowpass: 是否使用低通滤波
        
        Returns:
            清洗和滤波后的心率数据
        """
        # 1. 移除异常值
        filtered_data = self.remove_outliers(heart_rates)
        
        # 2. 中值滤波（可选）
        if use_median:
            filtered_data = self.median_filter(filtered_data)
        
        # 3. 移动平均滤波（可选）
        if use_ma:
            filtered_data = self.moving_average_filter(filtered_data)
        
        # 4. 低通滤波（可选）
        if use_lowpass:
            filtered_data = self.butter_lowpass_filter(filtered_data)
        
        return filtered_data
    
    def filter_dataframe(self, df, heart_rate_column='heart_rate', **filter_params):
        """
        对DataFrame中的心率数据进行滤波
        
        Args:
            df: 包含心率数据的DataFrame
            heart_rate_column: 心率数据列名
            **filter_params: 传递给comprehensive_filter的参数
        
        Returns:
            添加了滤波后数据的DataFrame副本
        """
        df_copy = df.copy()
        
        # 对每个批次分别进行滤波
        if 'batch_id' in df_copy.columns:
            filtered_rates = []
            for batch_id in df_copy['batch_id'].unique():
                batch_mask = df_copy['batch_id'] == batch_id
                batch_data = df_copy.loc[batch_mask, heart_rate_column].values
                filtered_batch = self.comprehensive_filter(batch_data, **filter_params)
                filtered_rates.extend(filtered_batch)
            df_copy['heart_rate_filtered'] = filtered_rates
        else:
            # 如果没有批次信息，直接滤波整个数据
            filtered_data = self.comprehensive_filter(
                df_copy[heart_rate_column].values, 
                **filter_params
            )
            df_copy['heart_rate_filtered'] = filtered_data
        
        return df_copy


if __name__ == "__main__":
    # 测试滤波器
    from data_generator import HeartRateDataGenerator
    
    print("=== 测试心率数据滤波器 ===\n")
    
    # 生成测试数据
    generator = HeartRateDataGenerator()
    heart_rates = generator.generate_normal_data()
    
    # 添加一些噪声和异常值
    noisy_data = heart_rates.copy()
    noisy_data[5] = 200  # 异常高值
    noisy_data[10] = 20  # 异常低值
    
    print("原始数据（含噪声）:")
    print([f'{x:.1f}' for x in noisy_data])
    
    # 创建滤波器
    filter_obj = HeartRateFilter()
    
    # 测试各种滤波方法
    print("\n=== 移除异常值后 ===")
    cleaned = filter_obj.remove_outliers(noisy_data)
    print([f'{x:.1f}' for x in cleaned])
    
    print("\n=== 中值滤波后 ===")
    median_filtered = filter_obj.median_filter(cleaned)
    print([f'{x:.1f}' for x in median_filtered])
    
    print("\n=== 移动平均滤波后 ===")
    ma_filtered = filter_obj.moving_average_filter(cleaned)
    print([f'{x:.1f}' for x in ma_filtered])
    
    print("\n=== 综合滤波后 ===")
    comprehensive = filter_obj.comprehensive_filter(noisy_data)
    print([f'{x:.1f}' for x in comprehensive])
    
    # 测试DataFrame滤波
    print("\n=== 测试DataFrame滤波 ===")
    dataset = generator.generate_mixed_dataset(num_batches=2)
    filtered_df = filter_obj.filter_dataframe(dataset)
    print("\n滤波前后对比（前10条）:")
    print(filtered_df[['heart_rate', 'heart_rate_filtered']].head(10))
