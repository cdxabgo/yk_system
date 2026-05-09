# 井下心率监测一体化系统
# 整合数据生成、清洗、模型训练、实时监测、异常报警


import numpy as np
import pandas as pd
import time
import os
from datetime import datetime
from data_generator import HeartRateDataGenerator
from data_filter import HeartRateFilter
from enhanced_detector import EnhancedAnomalyDetector
from lgbm_model import LGBMAnomalyDetector
from isolation_forest_detector import IForestDetector
import warnings
warnings.filterwarnings('ignore')

try:
    from lstm_detector import LSTMAutoencoderDetector, HAS_TF
except ImportError:
    HAS_TF = False
    LSTMAutoencoderDetector = None


class IntegratedHeartRateMonitor:
    """井下心率监测一体化系统（三模型融合版）"""

    def __init__(self):
        """初始化系统"""
        self.generator = HeartRateDataGenerator()
        self.filter = HeartRateFilter()
        self.rule_detector = EnhancedAnomalyDetector()
        self.lgbm_detector = LGBMAnomalyDetector()
        self.iforest_detector = IForestDetector(contamination=0.1, window_size=10)
        self.lstm_detector = None

        self.rules = {
            '心率过快': '持续超过150次/分钟 且连续3条以上',
            '心率过慢': '持续低于60次/分钟 且连续2条以上',
            '心率极值': '>=200次/分钟 或 <=30次/分钟(即刻报警)',
            '心律不齐': '相邻数据差值 >=30次/分钟'
        }

        self.batch_count = 0
        self.total_anomalies = 0
        self.start_time = None
        self.history_data = []
        self.monitoring_records = []
    
    def print_header(self):
        """打印系统头部"""
        print("\n" + "=" * 80)
        print("🏥 井下实时心率监测一体化系统")
        print("=" * 80)
        print("系统功能:")
        print("  [1] 随机生成心率数据（含井下环境因素、数据缺失）")
        print("  [2] 数据清洗处理（中值滤波、移动平均、巴特沃斯滤波）")
        print("  [3] LightGBM机器学习模型（23维特征工程）")
        print("  [4] 实时异常检测与报警")
        print("\n检测规则:")
        for rule_name, rule_desc in self.rules.items():
            print(f"  • {rule_name}: {rule_desc}")
        print("=" * 80 + "\n")
    
    def train_model(self, num_batches=100):
        """
        训练LightGBM模型
        
        参数:
            num_batches: 训练批次数
        """
        print("🤖 [模型训练模式]")
        print("=" * 80)
        
        # 1. 生成训练数据
        print(f"\n[1/5] 生成训练数据 ({num_batches} 批次)...")
        df_train = self.generator.generate_mixed_dataset(num_batches=num_batches)
        print(f"      ✓ 生成 {len(df_train)} 条数据")
        
        # 保存原始训练数据
        train_data_file = f'output/train_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        df_train.to_csv(train_data_file, index=False, encoding='utf-8-sig')
        print(f"      ✓ 训练数据已保存: {train_data_file}")
        
        # 2. 数据清洗
        print("\n[2/5] 数据清洗处理...")
        for batch_id in df_train['batch_id'].unique():
            batch_mask = df_train['batch_id'] == batch_id
            heart_rates = df_train.loc[batch_mask, 'heart_rate'].values
            filtered_rates = self.filter.comprehensive_filter(heart_rates)
            df_train.loc[batch_mask, 'heart_rate_filtered'] = filtered_rates
        print("      ✓ 清洗完成")
        
        # 3. 使用生成器自带标签（不再用规则标注）
        print("\n[3/5] 使用生成器逐点标签...")
        normal_count = int((df_train['is_abnormal'] == 0).sum())
        anomaly_count = int((df_train['is_abnormal'] == 1).sum())
        print(f"      正常: {normal_count} ({normal_count/len(df_train)*100:.1f}%)")
        print(f"      异常: {anomaly_count} ({anomaly_count/len(df_train)*100:.1f}%)")

        # 4. 训练 LightGBM
        print("\n[4/5] 训练 LightGBM...")
        X, y = self.lgbm_detector.prepare_training_data(df_train)
        print(f"      特征矩阵: {X.shape}, 维度: {len(self.lgbm_detector.feature_names)}")
        self.lgbm_detector.train(X, y, num_boost_round=100)

        # 5. 保存模型
        print("\n[5/5] 保存模型...")
        os.makedirs('output/models', exist_ok=True)
        self.lgbm_detector.save_model('output/models/lgbm_model.pkl')
        # 同时训练 IForest (无监督，用全部数据)
        self.iforest_detector.fit(df_train['heart_rate_filtered'].values)
        self.iforest_detector.save('output/models/isolation_forest.pkl')
        # LSTM-AE (只用正常数据)
        if HAS_TF:
            normal_batches = [df_train[df_train['batch_id']==bid]['heart_rate_filtered'].values
                for bid in df_train['batch_id'].unique()
                if df_train[df_train['batch_id']==bid]['is_abnormal'].sum()==0]
            self.lstm_detector = LSTMAutoencoderDetector(sequence_length=15, latent_dim=8)
            self.lstm_detector.fit(normal_batches, epochs=30, verbose=0)
            self.lstm_detector.save('output/models/lstm_ae.pkl')

        print("\n" + "=" * 80)
        print("[OK] 模型训练完成!")
        print("=" * 80)
    
    def load_model(self):
        """加载所有模型"""
        loaded = 0
        try:
            self.lgbm_detector.load_model('output/models/lgbm_model.pkl')
            loaded += 1
        except Exception: pass
        try:
            self.iforest_detector = IForestDetector.load('output/models/isolation_forest.pkl')
            loaded += 1
        except Exception: pass
        if HAS_TF:
            try:
                self.lstm_detector = LSTMAutoencoderDetector.load('output/models/lstm_ae.pkl')
                loaded += 1
            except Exception: pass
        return loaded > 0

    def detect_and_alert(self, window_data, batch_id):
        """三模型投票融合检测"""
        if len(window_data) < 5:
            return

        # LightGBM
        lgbm_p = np.zeros(len(window_data), dtype=int)
        lgbm_s = np.zeros(len(window_data))
        if self.lgbm_detector.model:
            try:
                f = self.lgbm_detector.extract_features(window_data)
                lgbm_p = self.lgbm_detector.predict(f)
                lgbm_s = self.lgbm_detector.predict_proba(f)
            except Exception: pass

        # IForest
        if_p = self.iforest_detector.predict(window_data)
        if_s = self.iforest_detector.score(window_data)

        # LSTM-AE
        lstm_p = np.zeros(len(window_data), dtype=int)
        lstm_s = np.zeros(len(window_data))
        if self.lstm_detector:
            try:
                lstm_p = self.lstm_detector.predict(window_data)
                lstm_s = self.lstm_detector.score(window_data)
            except Exception: pass

        # 规则检测
        results = self.rule_detector.detect_all(window_data)

        for i in range(len(window_data)):
            if lgbm_p[i] + if_p[i] + lstm_p[i] < 2:
                continue  # >=2 票才报警

            types = []
            if i in results.get('high_rate', []):    types.append('心率过快')
            if i in results.get('low_rate', []):      types.append('心率过慢')
            if i in results.get('extreme_value', []): types.append('心率极值')
            if i in results.get('arrhythmia', []):    types.append('心律不齐')
            if not types:
                types = self._classify_anomaly(window_data, i, window_data[i])

            if types:
                self.total_anomalies += 1
                self.print_alert(batch_id, i, window_data[i], window_data, types,
                                 (lgbm_s[i] + if_s[i] + lstm_s[i]) / 3.0)
    
    def _classify_anomaly(self, window_data, index, current_rate):
        """
        根据特征自动分类AI检测到的异常
        
        参数:
            window_data: 窗口数据
            index: 当前索引
            current_rate: 当前心率
            
        返回:
            异常类型列表
        """
        anomaly_types = []
        
        # 1. 检查是否接近极值
        if current_rate >= 180 or current_rate <= 40:
            anomaly_types.append('心率极值')
        
        # 2. 检查是否接近高心率阈值
        elif current_rate > 140:
            # 检查窗口内是否有多个高心率
            high_count = sum(1 for r in window_data[max(0, index-5):index+1] if r > 140)
            if high_count >= 2:
                anomaly_types.append('心率过快')
        
        # 3. 检查是否接近低心率阈值
        elif current_rate < 65:
            # 检查窗口内是否有多个低心率
            low_count = sum(1 for r in window_data[max(0, index-5):index+1] if r < 65)
            if low_count >= 2:
                anomaly_types.append('心率过慢')
        
        # 4. 检查心率变化是否剧烈（心律不齐）
        if index > 0:
            diff = abs(window_data[index] - window_data[index-1])
            if diff >= 25:  # 稍微放宽阈值
                if '心率过快' not in anomaly_types and '心率过慢' not in anomaly_types:
                    anomaly_types.append('心律不齐')
        
        # 5. 如果还是无法分类,检查趋势
        if len(anomaly_types) == 0 and index >= 2:
            recent_rates = window_data[max(0, index-2):index+1]
            if len(recent_rates) >= 3:
                # 快速上升趋势
                if recent_rates[-1] > recent_rates[0] + 40:
                    anomaly_types.append('心律不齐')
                # 快速下降趋势
                elif recent_rates[0] > recent_rates[-1] + 40:
                    anomaly_types.append('心律不齐')
        
        return anomaly_types
    
    def print_alert(self, batch_id, index, current_rate, window_data, 
                   anomaly_types, confidence):
        """
        打印异常报警信息
        
        参数:
            batch_id: 批次ID
            index: 异常索引
            current_rate: 当前心率
            window_data: 窗口数据
            anomaly_types: 异常类型列表
            confidence: 置信度
        """
        # 报警符号
        if '心率极值' in anomaly_types:
            symbol = '🚨🚨🚨'
            level = '【危险】'
        elif '心率过快' in anomaly_types or '心律不齐' in anomaly_types:
            symbol = '⚠️⚠️'
            level = '【警告】'
        else:
            symbol = '⚠️'
            level = '【注意】'
        
        print("\n" + symbol + " " * 3 + level + " 异常报警 " + symbol)
        print("=" * 80)
        print(f"报警时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"批次编号: #{batch_id} | 数据点: #{index}")
        print(f"当前心率: {current_rate:.1f} 次/分钟")
        print(f"异常类型: {', '.join(anomaly_types)}")
        print(f"置信度:   {confidence:.2%}")
        print(f"窗口数据 (共{len(window_data)}条):")
        # 显示所有窗口数据
        print(f"  {' → '.join([f'{r:.1f}' for r in window_data])}")
        
        # 详细说明
        print(f"\n异常详情:")
        if '心率过快' in anomaly_types:
            print(f"  • 心率持续超过150次/分钟，已连续{len([r for r in window_data if r > 150])}条")
        if '心率过慢' in anomaly_types:
            print(f"  • 心率持续低于60次/分钟，已连续{len([r for r in window_data if r < 60])}条")
        if '心率极值' in anomaly_types:
            if current_rate >= 200:
                print(f"  • 心率达到极高值 {current_rate:.1f} ≥ 200 次/分钟！")
            else:
                print(f"  • 心率达到极低值 {current_rate:.1f} ≤ 30 次/分钟！")
        if '心律不齐' in anomaly_types:
            if len(window_data) > 1:
                max_diff = max(abs(window_data[i] - window_data[i-1]) 
                              for i in range(1, len(window_data)))
                print(f"  • 心率变化剧烈，最大相邻差值 {max_diff:.1f} 次/分钟")
                if index > 0:
                    current_diff = abs(window_data[index] - window_data[index-1])
                    print(f"  • 当前点相邻差值: {current_diff:.1f} 次/分钟")
        
        print(f"\n累计异常: {self.total_anomalies} 次")
        print("=" * 80)
    
    def save_monitoring_data(self):
        """保存监测数据到CSV文件"""
        if len(self.monitoring_records) > 0:
            df_monitor = pd.DataFrame(self.monitoring_records)
            filename = f'output/monitoring_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            df_monitor.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"\n💾 监测数据已保存: {filename}")
            print(f"   共保存 {len(self.monitoring_records)} 条记录")
    
    def print_batch_data(self, window_data, batch_id):
        """
        打印当前批次的窗口数据
        
        参数:
            window_data: 滑动窗口数据（30条）
            batch_id: 批次ID
        """
        print(f"\n📊 批次 #{batch_id} 滑动窗口数据 (共{len(window_data)}条):")
        print(f"  {' → '.join([f'{r:.1f}' for r in window_data])}")
        print(f"  统计: 均值={np.mean(window_data):.1f}, "
              f"最小={np.min(window_data):.1f}, "
              f"最大={np.max(window_data):.1f}")
    
    def real_time_monitor(self, interval=10):
        """
        实时监测模式
        
        参数:
            interval: 监测间隔（秒）
        """
        print("\n🔍 [实时监测模式]")
        print("=" * 80)
        print(f"监测间隔: {interval}秒/批次")
        print(f"数据规格: 每批次18条数据（每10秒1条）")
        print(f"按 Ctrl+C 停止监测")
        print("=" * 80)
        
        self.start_time = datetime.now()
        
        try:
            while True:
                self.batch_count += 1
                
                # 1. 生成数据（模拟接收）
                df = self.generator.generate_mixed_dataset(num_batches=1)
                
                # 2. 数据清洗
                heart_rates = df['heart_rate'].values
                filtered_rates = self.filter.comprehensive_filter(heart_rates)
                
                # 2.5 记录本批次数据
                for i, (raw, filtered) in enumerate(zip(heart_rates, filtered_rates)):
                    self.monitoring_records.append({
                        'batch_id': self.batch_count,
                        'data_index': i,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'heart_rate_raw': raw,
                        'heart_rate_filtered': filtered
                    })
                
                # 3. 更新历史数据（维护滑动窗口）
                self.history_data.extend(filtered_rates)
                # 只保留最近30条数据（5分钟窗口）
                if len(self.history_data) > 30:
                    self.history_data = self.history_data[-30:]
                
                # 4. 获取当前窗口数据
                window_data = np.array(self.history_data)
                
                # 5. 异常检测与报警（基于窗口数据）
                self.detect_and_alert(window_data, self.batch_count)
                
                # 6. 打印当前批次窗口数据
                self.print_batch_data(window_data, self.batch_count)
                
                # 5. 打印状态
                self.print_status()
                
                # 5. 等待下一批
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.print_summary()
            self.save_monitoring_data()
    
    def print_status(self):
        """打印当前状态"""
        current_time = datetime.now()
        running_time = current_time - self.start_time
        hours = int(running_time.total_seconds() // 3600)
        minutes = int((running_time.total_seconds() % 3600) // 60)
        seconds = int(running_time.total_seconds() % 60)
        
        print(f"\n[{current_time.strftime('%H:%M:%S')}] ", end="")
        print(f"批次 #{self.batch_count} | ", end="")
        print(f"运行时间: {hours:02d}:{minutes:02d}:{seconds:02d} | ", end="")
        print(f"累计异常: {self.total_anomalies} 次")
    
    def print_summary(self):
        """打印监测摘要"""
        end_time = datetime.now()
        running_time = end_time - self.start_time
        hours = int(running_time.total_seconds() // 3600)
        minutes = int((running_time.total_seconds() % 3600) // 60)
        seconds = int(running_time.total_seconds() % 60)
        
        print("\n\n" + "=" * 80)
        print("📊 监测摘要")
        print("=" * 80)
        print(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"运行时长: {hours:02d}:{minutes:02d}:{seconds:02d}")
        print(f"监测批次: {self.batch_count} 批")
        print(f"监测数据: {self.batch_count * 18} 条")
        print(f"检测异常: {self.total_anomalies} 次")
        if self.batch_count > 0:
            anomaly_rate = (self.total_anomalies / (self.batch_count * 18)) * 100
            print(f"异常率:   {anomaly_rate:.2f}%")
        print("=" * 80)
        print("\n✓ 系统已停止，感谢使用！\n")
