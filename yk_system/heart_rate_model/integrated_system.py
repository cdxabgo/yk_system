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

# 尝试导入 LSTM-AE
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

        # 检测规则
        self.rules = {
            '心率过快': '持续超过150次/分钟 且连续3条以上',
            '心率过慢': '持续低于60次/分钟 且连续2条以上',
            '心率极值': '>=200次/分钟 或 <=30次/分钟（即刻报警）',
            '心律不齐': '相邻数据差值 >=30次/分钟'
        }

        self.batch_count = 0
        self.total_anomalies = 0
        self.start_time = None

        # 历史数据缓存
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
        print(f"      [OK] 生成 {len(df_train)} 条数据")
        
        # 保存原始训练数据
        train_data_file = f'output/train_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        df_train.to_csv(train_data_file, index=False, encoding='utf-8-sig')
        print(f"      [OK] 训练数据已保存: {train_data_file}")
        
        # 2. 数据清洗
        print("\n[2/5] 数据清洗处理...")
        for batch_id in df_train['batch_id'].unique():
            batch_mask = df_train['batch_id'] == batch_id
            heart_rates = df_train.loc[batch_mask, 'heart_rate'].values
            filtered_rates = self.filter.comprehensive_filter(heart_rates)
            df_train.loc[batch_mask, 'heart_rate_filtered'] = filtered_rates
        print("      [OK] 清洗完成")
        
        # 3. 生成训练标签（使用规则检测器）
        print("\n[3/5] 生成训练标签...")
        df_train = self.rule_detector.analyze_dataframe(df_train)
        normal_count = sum(df_train['is_abnormal'] == False)
        anomaly_count = sum(df_train['is_abnormal'] == True)
        print(f"      [OK] 标签生成完成")
        print(f"      正常样本: {normal_count} ({normal_count/len(df_train)*100:.1f}%)")
        print(f"      异常样本: {anomaly_count} ({anomaly_count/len(df_train)*100:.1f}%)")
        
        # 4. 训练模型
        print("\n[4/5] 训练LightGBM模型...")
        X, y = self.ml_detector.prepare_training_data(df_train)
        print(f"      特征矩阵: {X.shape}")
        print(f"      特征维度: {len(self.ml_detector.feature_names)}")
        self.ml_detector.train(X, y, num_boost_round=100)
        
        # 5. 保存模型
        print("\n[5/5] 保存模型...")
        os.makedirs('output/models', exist_ok=True)
        self.ml_detector.save_model('output/models/lgbm_model.pkl')
        
        print("\n" + "=" * 80)
        print("[OK] 模型训练完成！")
        print("=" * 80)
    
    def load_all_models(self):
        """加载所有训练好的模型"""
        loaded = 0
        # LightGBM
        try:
            self.lgbm_detector.load_model('output/models/lgbm_model.pkl')
            loaded += 1
        except Exception:
            print("  [WARN] LightGBM 模型未找到")
        # Isolation Forest
        try:
            self.iforest_detector = IForestDetector.load('output/models/isolation_forest.pkl')
            loaded += 1
        except Exception:
            print("  [WARN] Isolation Forest 模型未找到")
        # LSTM-AE
        if HAS_TF:
            try:
                self.lstm_detector = LSTMAutoencoderDetector.load('output/models/lstm_ae.pkl')
                loaded += 1
            except Exception:
                print("  [WARN] LSTM-Autoencoder 模型未找到")
        return loaded > 0

    def load_model(self):
        """兼容旧接口"""
        return self.load_all_models()
    
    def detect_and_alert(self, window_data, batch_id):
        """
        三模型投票融合 + 规则联合检测

        Args:
            window_data: 滑动窗口数据
            batch_id: 批次ID
        """
        if len(window_data) < 5:
            return

        # 1. LightGBM 预测
        lgbm_preds = np.zeros(len(window_data), dtype=int)
        lgbm_scores = np.zeros(len(window_data))
        if self.lgbm_detector.model:
            try:
                features = self.lgbm_detector.extract_features(window_data)
                lgbm_preds = self.lgbm_detector.predict(features)
                lgbm_scores = self.lgbm_detector.predict_proba(features)
            except Exception:
                pass

        # 2. Isolation Forest 预测
        if_preds = self.iforest_detector.predict(window_data)
        if_scores = self.iforest_detector.score(window_data)

        # 3. LSTM-AE 预测
        lstm_preds = np.zeros(len(window_data), dtype=int)
        lstm_scores = np.zeros(len(window_data))
        if self.lstm_detector:
            try:
                lstm_preds = self.lstm_detector.predict(window_data)
                lstm_scores = self.lstm_detector.score(window_data)
            except Exception:
                pass

        # 4. 规则检测
        results = self.rule_detector.detect_all(window_data)

        # 5. 三模型硬投票（>=2 票同意 → 异常）
        for i in range(len(window_data)):
            votes = int(lgbm_preds[i]) + int(if_preds[i]) + int(lstm_preds[i])
            is_anomaly = votes >= 2  # 至少 2/3 模型同意

            if not is_anomaly:
                continue

            # 确定异常类型
            anomaly_types = []
            if i in results.get('high_rate', []):
                anomaly_types.append('心率过快')
            if i in results.get('low_rate', []):
                anomaly_types.append('心率过慢')
            if i in results.get('extreme_value', []):
                anomaly_types.append('心率极值')
            if i in results.get('arrhythmia', []):
                anomaly_types.append('心律不齐')

            if not anomaly_types:
                anomaly_types = self._classify_anomaly(window_data, i, window_data[i])

            if anomaly_types:
                self.total_anomalies += 1
                # 融合分数 = 三模型平均
                fused_score = (lgbm_scores[i] + if_scores[i] + lstm_scores[i]) / 3.0
                self.print_alert(
                    batch_id=batch_id, index=i,
                    current_rate=window_data[i],
                    window_data=window_data,
                    anomaly_types=anomaly_types,
                    confidence=fused_score
                )
    
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
        print("\n[OK] 系统已停止，感谢使用！\n")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='井下心率监测一体化系统')
    parser.add_argument('--train', action='store_true', 
                       help='训练模型模式')
    parser.add_argument('--train-batches', type=int, default=200,
                       help='训练批次数，默认200')
    parser.add_argument('--monitor', action='store_true',
                       help='实时监测模式')
    parser.add_argument('--interval', type=int, default=10,
                       help='监测间隔（秒），默认10秒')
    
    args = parser.parse_args()
    
    # 创建系统
    system = IntegratedHeartRateMonitor()
    system.print_header()
    
    if args.train:
        # 训练模式
        system.train_model(num_batches=args.train_batches)
        
    elif args.monitor:
        # 实时监测模式
        if not system.load_model():
            print("❌ 错误: 模型文件不存在")
            print("   请先运行: python integrated_system.py --train")
            return
        
        system.real_time_monitor(interval=args.interval)
        
    else:
        # 默认：完整流程演示
        print("🎯 [完整流程演示模式]")
        print("\n请选择操作:")
        print("  1. 训练模型")
        print("  2. 实时监测")
        print("  3. 完整流程（训练+监测）")
        
        choice = input("\n请输入选项 (1/2/3): ").strip()
        
        if choice == '1':
            system.train_model(num_batches=100)
            
        elif choice == '2':
            if not system.load_model():
                print("\n❌ 模型文件不存在，开始训练...")
                system.train_model(num_batches=100)
            
            input("\n按 Enter 键开始实时监测...")
            system.real_time_monitor(interval=10)
            
        elif choice == '3':
            # 完整流程
            print("\n" + "=" * 80)
            print("Step 1: 模型训练")
            print("=" * 80)
            system.train_model(num_batches=50)
            
            input("\n[OK] 训练完成！按 Enter 键开始实时监测...")
            
            print("\n" + "=" * 80)
            print("Step 2: 实时监测")
            print("=" * 80)
            system.real_time_monitor(interval=10)
        else:
            print("无效选项")


if __name__ == '__main__':
    main()
