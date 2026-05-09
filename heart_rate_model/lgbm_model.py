# 基于LightGBM的心率异常检测模型
# 使用检测规则的特征工程


import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pickle
from typing import Tuple
import os


class LGBMAnomalyDetector:
    """基于LightGBM的心率异常检测器"""
    
    def __init__(self, window_size=30):
        """
        初始化检测器
        
        参数:
            window_size: 滑动窗口大小（5分钟 = 30条数据）
        """
        self.window_size = window_size
        self.model = None
        self.feature_names = None
        
        # 检测阈值（与增强检测器一致）
        self.high_rate_threshold = 150
        self.high_rate_consecutive = 3
        self.low_rate_threshold = 60
        self.low_rate_consecutive = 2
        self.extreme_high = 200
        self.extreme_low = 30
        self.arrhythmia_threshold = 30
        
    def extract_features(self, heart_rates: np.ndarray) -> np.ndarray:
        """
        提取特征（包含连续性和心律不齐特征）
        
        参数:
            heart_rates: 心率数据数组
            
        返回:
            特征矩阵
        """
        features = []
        
        for i in range(len(heart_rates)):
            # 获取滑动窗口数据
            window_start = max(0, i - self.window_size + 1)
            window_data = heart_rates[window_start:i+1]
            
            feature_dict = {}
            
            # 1. 当前心率
            current_rate = heart_rates[i]
            feature_dict['current_rate'] = current_rate
            
            # 2. 统计特征
            feature_dict['mean'] = np.mean(window_data)
            feature_dict['std'] = np.std(window_data)# 标准差
            feature_dict['min'] = np.min(window_data)
            feature_dict['max'] = np.max(window_data)
            feature_dict['range'] = np.max(window_data) - np.min(window_data)
            
            # 3. 变化特征
            if len(window_data) > 1:
                feature_dict['rate_change'] = window_data[-1] - window_data[-2]
                feature_dict['rate_change_pct'] = (window_data[-1] - window_data[-2]) / window_data[-2] if window_data[-2] != 0 else 0
                
                # 加速度
                if len(window_data) > 2:
                    feature_dict['acceleration'] = window_data[-1] - 2*window_data[-2] + window_data[-3]
                else:
                    feature_dict['acceleration'] = 0
                    
                # 趋势斜率
                x = np.arange(len(window_data))
                coeffs = np.polyfit(x, window_data, 1)
                feature_dict['trend_slope'] = coeffs[0]
            else:
                feature_dict['rate_change'] = 0
                feature_dict['rate_change_pct'] = 0
                feature_dict['acceleration'] = 0
                feature_dict['trend_slope'] = 0
            
            # 4. 阈值特征
            feature_dict['is_high'] = 1 if current_rate > self.high_rate_threshold else 0
            feature_dict['is_low'] = 1 if current_rate < self.low_rate_threshold else 0
            feature_dict['is_critical'] = 1 if current_rate < 40 else 0
            feature_dict['is_extreme'] = 1 if (current_rate >= self.extreme_high or current_rate <= self.extreme_low) else 0
            
            # 5. 连续性特征
            # 检查窗口内连续高心率
            if len(window_data) >= self.high_rate_consecutive:
                consecutive_high = 0
                for rate in window_data[-self.high_rate_consecutive:]:
                    if rate > self.high_rate_threshold:
                        consecutive_high += 1
                feature_dict['consecutive_high_count'] = consecutive_high
                feature_dict['has_consecutive_high'] = 1 if consecutive_high >= self.high_rate_consecutive else 0
            else:
                feature_dict['consecutive_high_count'] = 0
                feature_dict['has_consecutive_high'] = 0
            
            # 检查窗口内连续低心率
            if len(window_data) >= self.low_rate_consecutive:
                consecutive_low = 0
                for rate in window_data[-self.low_rate_consecutive:]:
                    if rate < self.low_rate_threshold:
                        consecutive_low += 1
                feature_dict['consecutive_low_count'] = consecutive_low
                feature_dict['has_consecutive_low'] = 1 if consecutive_low >= self.low_rate_consecutive else 0
            else:
                feature_dict['consecutive_low_count'] = 0
                feature_dict['has_consecutive_low'] = 0
            
            # 6. 心律不齐特征
            if len(window_data) > 1:
                # 最大相邻差值
                max_diff = max(abs(window_data[j] - window_data[j-1]) for j in range(1, len(window_data)))
                feature_dict['max_adjacent_diff'] = max_diff
                feature_dict['has_arrhythmia'] = 1 if max_diff >= self.arrhythmia_threshold else 0
                
                # 当前相邻差值
                current_diff = abs(window_data[-1] - window_data[-2])
                feature_dict['current_adjacent_diff'] = current_diff
            else:
                feature_dict['max_adjacent_diff'] = 0
                feature_dict['has_arrhythmia'] = 0
                feature_dict['current_adjacent_diff'] = 0
            
            # 7. 窗口内异常比例
            high_ratio = sum(1 for r in window_data if r > self.high_rate_threshold) / len(window_data)
            low_ratio = sum(1 for r in window_data if r < self.low_rate_threshold) / len(window_data)
            feature_dict['high_rate_ratio'] = high_ratio
            feature_dict['low_rate_ratio'] = low_ratio
            
            features.append(feature_dict)
        
        # 转换为DataFrame再转为numpy数组
        df = pd.DataFrame(features)
        self.feature_names = df.columns.tolist()
        return df.values
    
    def prepare_training_data(self, df: pd.DataFrame, 
                             heart_rate_column: str = 'heart_rate_filtered') -> Tuple[np.ndarray, np.ndarray]:
        """
        准备训练数据
        
        参数:
            df: 包含心率数据和标签的DataFrame
            heart_rate_column: 心率列名
            
        返回:
            特征矩阵和标签数组
        """
        all_features = []
        all_labels = []
        
        # 按批次处理
        if 'batch_id' in df.columns:
            for batch_id in df['batch_id'].unique():
                batch_df = df[df['batch_id'] == batch_id]
                heart_rates = batch_df[heart_rate_column].values
                labels = batch_df['is_anomaly'].values.astype(int)
                
                # 提取特征
                features = self.extract_features(heart_rates)
                
                all_features.append(features)
                all_labels.append(labels)
        else:
            heart_rates = df[heart_rate_column].values
            labels = df['is_anomaly'].values.astype(int)
            features = self.extract_features(heart_rates)
            all_features.append(features)
            all_labels.append(labels)
        
        # 合并所有批次
        X = np.vstack(all_features)
        y = np.concatenate(all_labels)
        
        return X, y
    
    def train(self, X: np.ndarray, y: np.ndarray, 
             params: dict = None, num_boost_round: int = 100):
        """
        训练LightGBM模型
        
        参数:
            X: 特征矩阵
            y: 标签数组
            params: LightGBM参数
            num_boost_round: 迭代次数
        """
        # 默认参数
        if params is None:
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': 0,
                'max_depth': 6,
                'min_child_samples': 20,
                'scale_pos_weight': sum(y == 0) / sum(y == 1) if sum(y == 1) > 0 else 1  # 处理类别不平衡
            }
        
        # 创建LightGBM数据集
        train_data = lgb.Dataset(X, label=y, feature_name=self.feature_names)
        
        # 训练模型
        print("开始训练LightGBM模型...")
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=num_boost_round,
            valid_sets=[train_data],
            valid_names=['train']
        )
        print("✓ 模型训练完成")
        
    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """
        预测异常
        
        参数:
            X: 特征矩阵
            threshold: 分类阈值
            
        返回:
            预测结果（0或1）
        """
        if self.model is None:
            raise ValueError("模型未训练，请先调用train()方法")
        
        proba = self.model.predict(X)
        predictions = (proba >= threshold).astype(int)
        return predictions
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        预测概率
        
        参数:
            X: 特征矩阵
            
        返回:
            异常概率
        """
        if self.model is None:
            raise ValueError("模型未训练，请先调用train()方法")
        
        return self.model.predict(X)
    
    def get_feature_importance(self, importance_type: str = 'gain') -> pd.DataFrame:
        """
        获取特征重要性
        
        参数:
            importance_type: 重要性类型（'gain' 或 'split'）
            
        返回:
            特征重要性DataFrame
        """
        if self.model is None:
            raise ValueError("模型未训练")
        
        importance = self.model.feature_importance(importance_type=importance_type)
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        })
        feature_importance = feature_importance.sort_values('importance', ascending=False)
        return feature_importance
    
    def save_model(self, filepath: str):
        """保存模型"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'window_size': self.window_size,
            'params': {
                'high_rate_threshold': self.high_rate_threshold,
                'high_rate_consecutive': self.high_rate_consecutive,
                'low_rate_threshold': self.low_rate_threshold,
                'low_rate_consecutive': self.low_rate_consecutive,
                'extreme_high': self.extreme_high,
                'extreme_low': self.extreme_low,
                'arrhythmia_threshold': self.arrhythmia_threshold
            }
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"✓ 模型已保存到: {filepath}")
    
    def load_model(self, filepath: str):
        """加载模型"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.window_size = model_data['window_size']
        
        # 恢复参数
        params = model_data['params']
        self.high_rate_threshold = params['high_rate_threshold']
        self.high_rate_consecutive = params['high_rate_consecutive']
        self.low_rate_threshold = params['low_rate_threshold']
        self.low_rate_consecutive = params['low_rate_consecutive']
        self.extreme_high = params['extreme_high']
        self.extreme_low = params['extreme_low']
        self.arrhythmia_threshold = params['arrhythmia_threshold']
        
        print(f"✓ 模型已加载: {filepath}")


if __name__ == '__main__':
    # 测试代码
    from data_generator import HeartRateDataGenerator
    from data_filter import HeartRateFilter
    from enhanced_detector import EnhancedAnomalyDetector
    
    print("=" * 70)
    print("LightGBM心率异常检测模型 - 训练演示")
    print("=" * 70)
    
    # 生成训练数据
    print("\n[1/6] 生成训练数据...")
    generator = HeartRateDataGenerator()
    df_train = generator.generate_mixed_dataset(num_batches=100)
    print(f"      ✓ 训练数据: {len(df_train)} 条")
    
    # 数据滤波
    print("\n[2/6] 数据滤波...")
    filter_obj = HeartRateFilter()
    for batch_id in df_train['batch_id'].unique():
        batch_mask = df_train['batch_id'] == batch_id
        heart_rates = df_train.loc[batch_mask, 'heart_rate'].values
        filtered_rates = filter_obj.comprehensive_filter(heart_rates)
        df_train.loc[batch_mask, 'heart_rate_filtered'] = filtered_rates
    print("      ✓ 滤波完成")
    
    # 使用增强检测器生成标签
    print("\n[3/6] 生成训练标签...")
    rule_detector = EnhancedAnomalyDetector()
    df_train = rule_detector.analyze_dataframe(df_train)
    print(f"      ✓ 标签生成完成")
    print(f"      正常样本: {sum(df_train['is_anomaly'] == False)}")
    print(f"      异常样本: {sum(df_train['is_anomaly'] == True)}")
    
    # 准备训练数据
    print("\n[4/6] 提取特征...")
    detector = LGBMAnomalyDetector(window_size=5)
    X, y = detector.prepare_training_data(df_train)
    print(f"      ✓ 特征矩阵: {X.shape}")
    print(f"      特征数量: {len(detector.feature_names)}")
    
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 训练模型
    print(f"\n[5/6] 训练LightGBM模型...")
    print(f"      训练集: {X_train.shape[0]} 样本")
    print(f"      测试集: {X_test.shape[0]} 样本")
    detector.train(X_train, y_train, num_boost_round=100)
    
    # 评估模型
    print("\n[6/6] 评估模型...")
    y_pred = detector.predict(X_test)
    y_pred_train = detector.predict(X_train)
    
    print(f"\n训练集准确率: {accuracy_score(y_train, y_pred_train):.4f}")
    print(f"测试集准确率: {accuracy_score(y_test, y_pred):.4f}")
    
    print("\n混淆矩阵:")
    print(confusion_matrix(y_test, y_pred))
    
    print("\n分类报告:")
    print(classification_report(y_test, y_pred, target_names=['正常', '异常']))
    
    # 特征重要性
    print("\n特征重要性 (Top 10):")
    print("-" * 70)
    importance_df = detector.get_feature_importance()
    print(importance_df.head(10).to_string(index=False))
    
    # 保存模型
    print("\n保存模型...")
    detector.save_model('output/models/lgbm_model.pkl')
    
    print("\n" + "=" * 70)
    print("训练完成！")
    print("=" * 70)
