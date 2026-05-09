# MQTT数据接收和处理模块
# 通过MQTT订阅实时心率数据并进行异常检测


import time
import os
from datetime import datetime
from typing import Dict, List
from data_filter import HeartRateFilter
from enhanced_detector import EnhancedAnomalyDetector
from lgbm_model import LGBMAnomalyDetector
import numpy as np

# 导入Redis和数据库模块
try:
    from redis_storage import RedisStorage
    from database import DatabaseManager
except ImportError as e:
    print(f"⚠️  导入Redis/数据库模块失败: {e}")
    RedisStorage = None
    DatabaseManager = None

# 导入配置
try:
    from config import MODEL_CONFIG, FILTER_CONFIG, REDIS_CONFIG, MONITOR_CONFIG
except ImportError:
    # 如果没有配置文件，使用默认配置
    REDIS_CONFIG = {
        'host': 'localhost',
        'port': 6379,
        'max_history_count': 60
    }
    MONITOR_CONFIG = {
        'poll_interval': 5,
        'poll_batch_size': 100
    }


class MQTTHeartRateMonitor:
    """基于数据库轮询的心率监测系统（保留类名兼容旧调用）"""
    
    def __init__(self, mqtt_broker=None, mqtt_port=None, enable_redis=False, enable_db=True, poll_interval=None, poll_batch_size=None):
        """
        初始化数据库轮询心率监测系统
        
        Args:
            mqtt_broker: 兼容参数（已忽略）
            mqtt_port: 兼容参数（已忽略）
            enable_redis: 是否启用Redis（默认False）
            enable_db: 是否启用数据库（默认True）
            poll_interval: 轮询间隔（秒）
            poll_batch_size: 每次轮询读取记录上限
        """
        resolved_poll_interval = poll_interval if poll_interval is not None else MONITOR_CONFIG.get('poll_interval', 5)
        resolved_poll_batch_size = poll_batch_size if poll_batch_size is not None else MONITOR_CONFIG.get('poll_batch_size', 100)
        self.poll_interval = float(resolved_poll_interval)
        self.poll_batch_size = int(resolved_poll_batch_size)
        self.running = False
        self.last_processed_id = 0
        
        # 数据回调函数（用于REST API）
        self.data_callback = None
        
        # 数据处理模块
        self.filter = HeartRateFilter()
        self.rule_detector = EnhancedAnomalyDetector()
        self.ml_detector = LGBMAnomalyDetector()
        
        # 尝试加载已训练的模型
        model_path = "output/models/lgbm_model.pkl"
        if os.path.exists(model_path):
            try:
                self.ml_detector.load_model(model_path)
                print(f"✅ 已加载模型: {model_path}\n")
            except Exception as e:
                print(f"⚠️  模型加载失败: {e}\n")
        
        # Redis存储（用于历史数据）
        self.redis_storage = None
        if enable_redis and RedisStorage:
            try:
                self.redis_storage = RedisStorage()
                print("✅ Redis存储已启用")
            except Exception as e:
                print(f"⚠️  Redis初始化失败: {e}")
        
        # 数据库管理（用于设备状态和异常记录）
        self.db_manager = None
        if enable_db and DatabaseManager:
            try:
                self.db_manager = DatabaseManager()
                print("✅ 数据库管理已启用")
            except Exception as e:
                print(f"⚠️  数据库初始化失败: {e}")
        
        # 数据缓存 - 按用户ID分组（仅用于临时缓存，主要存储在Redis）
        self.user_data_cache = {}  # {userId: [心率数据列表]}
        self.continuous_batch_size = int(MONITOR_CONFIG.get('continuous_batch_size', 18))
        self.records_since_last_continuous = {}
        
        # 统计信息
        self.total_received = 0
        self.total_anomalies = 0
        
    def _fetch_new_records(self) -> List[Dict]:
        """从数据库拉取新增心率记录"""
        if not self.db_manager:
            return []
        return self.db_manager.get_new_heart_rate_records(
            last_id=self.last_processed_id,
            limit=self.poll_batch_size
        )

    def _handle_db_record(self, record: Dict):
        """处理单条数据库心率记录"""
        try:
            user_id = str(record.get('employee_id'))
            heart_rate = float(record.get('heart_rate'))
            measure_time = record.get('measure_time')
            if hasattr(measure_time, 'strftime'):
                data_time = measure_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                data_time = str(measure_time)

            self.total_received += 1
            self.records_since_last_continuous[user_id] = self.records_since_last_continuous.get(user_id, 0) + 1
            print(f"\n[数据] 用户{user_id} 时间: {data_time} 心率: {heart_rate} bpm")

            # 先执行检测，再推送（检测结果在 analyze_user_data 内部通过回调推送）
            self.analyze_user_data(user_id)
        except Exception as e:
            print(f"❌ 数据库记录处理错误: {e}")
    
    def analyze_user_data(self, user_id):
        """
        分析用户心率数据 - 从数据库获取历史数据，支持两种检测模式
        
        Args:
            user_id: 用户ID
        """
        try:
            if not self.db_manager:
                print("⚠️  数据库未启用，无法分析")
                return

            history_data = self.db_manager.get_recent_employee_heart_rates(
                employee_id=user_id,
                limit=REDIS_CONFIG.get('max_history_count', 60)
            )
            if not history_data:
                print(f"⚠️  用户 {user_id} 暂无历史数据")
                return

            heart_rates = np.array([float(item['heart_rate']) for item in history_data])
            time_list = [item['measure_time'] for item in history_data]
            
            data_count = len(heart_rates)
            
            print(f"\n{'='*80}")
            print(f"📊 心率数据分析 - 用户 {user_id}")
            print(f"{'='*80}")
            print(f"时间范围: {time_list[0]} 至 {time_list[-1]}")
            print(f"数据数量: {data_count} 条")
            print(f"{'='*80}")
            
            # 判断使用哪种检测模式（优先瞬时预警，按批次补充连续检测）
            min_continuous_data = 5  # 至少5条数据才进行连续异常检测
            new_record_count = self.records_since_last_continuous.get(user_id, 0)
            can_run_continuous = new_record_count >= self.continuous_batch_size
            
            if data_count >= min_continuous_data and can_run_continuous:
                # 模式1: 数据量多且累计了新的批次 - 连续心率异常检测
                print(f"\n🔍 检测模式: 连续心率异常分析 (数据充足: {data_count}条)")
                self.continuous_anomaly_detection(user_id, heart_rates, time_list)
                self.records_since_last_continuous[user_id] = 0
            else:
                # 模式2: 瞬时心率预警
                print(f"\n⚡ 检测模式: 瞬时心率预警 (当前窗口: {data_count}条)")
                self.instant_anomaly_detection(user_id, heart_rates, time_list)
            
        except Exception as e:
            print(f"❌ 数据分析错误: {e}")
            import traceback
            traceback.print_exc()
    
    def continuous_anomaly_detection(self, user_id, heart_rates, time_list):
        """
        模式1: 连续心率异常检测（数据量充足时）
        对Redis中的历史数据进行完整分析，检测连续异常模式
        
        Args:
            user_id: 用户ID
            heart_rates: 心率数组
            time_list: 时间列表
        """
        try:
            # 1. 数据清洗
            print(f"\n🧹 步骤1: 数据清洗与滤波")
            print(f"{'─'*80}")
            
            cleaned_rates = self.filter.comprehensive_filter(heart_rates)
            
            print(f"原始数据统计:")
            print(f"  均值={np.mean(heart_rates):.1f} bpm, "
                  f"标准差={np.std(heart_rates):.1f} bpm, "
                  f"范围=[{np.min(heart_rates):.1f}, {np.max(heart_rates):.1f}]")
            print(f"清洗后统计:")
            print(f"  均值={np.mean(cleaned_rates):.1f} bpm, "
                  f"标准差={np.std(cleaned_rates):.1f} bpm, "
                  f"范围=[{np.min(cleaned_rates):.1f}, {np.max(cleaned_rates):.1f}]")
            
            # 2. 规则检测
            print(f"\n{'─'*80}")
            print(f"🔍 步骤2: 基于规则的异常检测")
            print(f"{'─'*80}")
            
            rule_anomalies = self.rule_detector.detect_all(cleaned_rates)
            
            # 统计规则检测结果
            rule_count = 0
            rule_indices = set()
            for anomaly_type, indices in rule_anomalies.items():
                if indices:
                    rule_count += len(indices)
                    rule_indices.update(indices)
            
            if rule_count == 0:
                print("✅ 规则检测: 未发现异常")
            else:
                print(f"⚠️  规则检测: 发现 {rule_count} 条异常数据")
            
            # 3. 机器学习检测
            print(f"\n{'─'*80}")
            print(f"🤖 步骤3: 机器学习智能检测")
            print(f"{'─'*80}")
            
            ml_indices = set()
            ml_probabilities = {}
            
            if not hasattr(self.ml_detector, 'model') or self.ml_detector.model is None:
                print("⚠️  模型未加载，跳过机器学习检测")
            else:
                try:
                    features = self.ml_detector.extract_features(cleaned_rates)
                    predictions = self.ml_detector.predict(features)
                    probabilities = self.ml_detector.predict_proba(features)
                    
                    ml_count = sum(predictions)
                    
                    if ml_count == 0:
                        print("✅ 机器学习检测: 未发现异常")
                    else:
                        print(f"⚠️  机器学习检测: 发现 {ml_count} 条异常数据")
                        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
                            if pred == 1:
                                ml_indices.add(i)
                                ml_probabilities[i] = prob
                except Exception as e:
                    print(f"⚠️  机器学习检测错误: {e}")
            
            # 4. 合并检测结果并输出异常报警
            all_anomaly_indices = rule_indices.union(ml_indices)
            
            if len(all_anomaly_indices) > 0:
                print(f"\n{'='*80}")
                print(f"🚨 连续异常检测结果")
                print(f"{'='*80}")
                print(f"总异常数: {len(all_anomaly_indices)} 条")
                print(f"  - 规则检测: {len(rule_indices)} 条")
                print(f"  - AI检测: {len(ml_indices)} 条")
                
                # 保存异常记录到数据库
                if self.db_manager:
                    for idx in all_anomaly_indices:
                        anomaly_type = self._get_anomaly_type_str(rule_anomalies, idx)
                        severity = self._get_severity(cleaned_rates[idx])
                        self.db_manager.insert_anomaly_record(
                            device_id=user_id,
                            heart_rate=float(cleaned_rates[idx]),
                            anomaly_type=f"continuous_{anomaly_type}",
                            severity=severity,
                            description=f"连续异常检测：{anomaly_type}"
                        )
                    # 更新今日统计
                    self.db_manager.update_daily_anomaly_count(user_id, 'continuous')
                
                self.total_anomalies += len(all_anomaly_indices)
                print(f"[OK] 异常记录已保存到数据库")
            else:
                print(f"\n[OK] 未发现连续异常")

            # 推送检测结果到 Java 后端（连续检测模式）
            if self.data_callback:
                latest_hr = cleaned_rates[-1] if len(cleaned_rates) > 0 else 0
                latest_time = time_list[-1] if time_list else ''
                filtered = [{'heart_rate': float(hr), 'time': str(t)}
                           for hr, t in zip(cleaned_rates, time_list)]
                ml_anomalies = [f'AI-连续异常(idx={i})' for i in ml_indices] if ml_indices else []
                rule_results = {k: list(v) for k, v in rule_anomalies.items() if v and k != 'all'}
                self.data_callback({
                    'user_id': user_id,
                    'heart_rate': float(latest_hr),
                    'data_time': str(latest_time),
                    'filtered_data': filtered,
                    'ml_anomalies': ml_anomalies,
                    'rule_anomalies': rule_results
                })
            
            print(f"\n{'='*80}")
            print(f"✅ 连续异常检测完成")
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"❌ 连续异常检测错误: {e}")
            import traceback
            traceback.print_exc()
    
    def instant_anomaly_detection(self, user_id, heart_rates, time_list):
        """
        模式2: 瞬时心率预警（数据量较少时）
        对最新的心率数据进行快速判断，及时发现瞬时异常
        
        Args:
            user_id: 用户ID
            heart_rates: 心率数组
            time_list: 时间列表
        """
        try:
            print(f"\n⚡ 瞬时心率分析")
            print(f"{'─'*80}")
            
            # 获取最新心率值
            latest_hr = heart_rates[-1]
            latest_time = time_list[-1]
            
            print(f"最新心率: {latest_hr:.1f} bpm ({latest_time})")
            
            # 快速判断是否异常
            is_anomaly = False
            anomaly_reasons = []
            severity = 'low'
            
            # 极值检测
            if latest_hr >= 200:
                is_anomaly = True
                anomaly_reasons.append("极高心率(≥200)")
                severity = 'high'
            elif latest_hr <= 30:
                is_anomaly = True
                anomaly_reasons.append("极低心率(≤30)")
                severity = 'high'
            # 高心率
            elif latest_hr > 150:
                is_anomaly = True
                anomaly_reasons.append("心率过快(>150)")
                severity = 'medium'
            # 低心率
            elif latest_hr < 60:
                is_anomaly = True
                anomaly_reasons.append("心率过慢(<60)")
                severity = 'medium'
            
            # 如果有历史数据，检查变化率
            if len(heart_rates) > 1:
                prev_hr = heart_rates[-2]
                hr_change = abs(latest_hr - prev_hr)
                
                if hr_change >= 30:
                    is_anomaly = True
                    anomaly_reasons.append(f"心率剧变(Δ{hr_change:.1f})")
                    if severity == 'low':
                        severity = 'medium'
            
            # 输出结果
            if is_anomaly:
                print(f"\n🚨 发现瞬时异常！")
                print(f"{'─'*80}")
                print(f"异常类型: {', '.join(anomaly_reasons)}")
                print(f"严重程度: {severity}")
                print(f"当前心率: {latest_hr:.1f} bpm")
                if len(heart_rates) > 1:
                    print(f"前一次值: {prev_hr:.1f} bpm")
                print(f"{'─'*80}")
                
                # 插入异常记录到数据库
                if self.db_manager:
                    anomaly_type = anomaly_reasons[0].split('(')[0]
                    self.db_manager.insert_anomaly_record(
                        device_id=user_id,
                        heart_rate=float(latest_hr),
                        anomaly_type=f"instant_{anomaly_type}",
                        severity=severity,
                        description=f"瞬时异常：{', '.join(anomaly_reasons)}"
                    )
                    
                    # 更新今日瞬时异常总数
                    self.db_manager.update_daily_anomaly_count(user_id, 'instant')
                    
                    # 获取并显示今日统计
                    stats = self.db_manager.get_daily_anomaly_stats(user_id)
                    if stats:
                        print(f"📊 今日统计: 瞬时异常 {stats['instant_anomaly_count']} 次, "
                              f"连续异常 {stats['continuous_anomaly_count']} 次")
                    
                    print(f"✅ 异常记录已保存到数据库")
                
                self.total_anomalies += 1
            else:
                print(f"✅ 心率正常 ({latest_hr:.1f} bpm)")

            # 触发数据回调推送异常检测结果
            if self.data_callback:
                filtered = []
                for hr, t in zip(heart_rates, time_list):
                    try:
                        filtered.append({'heart_rate': float(hr), 'time': str(t)})
                    except (TypeError, ValueError):
                        pass  # 忽略无法转换的心率值
                self.data_callback({
                    'user_id': user_id,
                    'heart_rate': latest_hr,
                    'data_time': latest_time,
                    'filtered_data': filtered,
                    'ml_anomalies': anomaly_reasons if is_anomaly else [],
                    'rule_anomalies': {}
                })

            print(f"\n{'='*80}\n")
            
        except Exception as e:
            print(f"❌ 瞬时异常检测错误: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_anomaly_type_str(self, rule_anomalies, index):
        """获取异常类型字符串"""
        types = []
        if index in rule_anomalies.get('high_rate', []):
            types.append('心率过快')
        if index in rule_anomalies.get('low_rate', []):
            types.append('心率过慢')
        if index in rule_anomalies.get('extreme_value', []):
            types.append('心率极值')
        if index in rule_anomalies.get('arrhythmia', []):
            types.append('心律不齐')
        return ','.join(types) if types else '未知异常'
    
    def _get_severity(self, heart_rate):
        """根据心率判断严重程度"""
        if heart_rate >= 200 or heart_rate <= 30:
            return 'high'
        elif heart_rate > 150 or heart_rate < 60:
            return 'medium'
        else:
            return 'low'

    
    def print_alert(self, user_id, index, current_rate, window_data, time_str, 
                   rule_anomalies, confidence):
        """
        打印异常报警信息（原程序格式）
        
        Args:
            user_id: 用户ID
            index: 异常索引
            current_rate: 当前心率
            window_data: 窗口数据
            time_str: 时间字符串
            rule_anomalies: 规则检测结果
            confidence: 置信度
        """
        # 确定异常类型
        anomaly_types = []
        if index in rule_anomalies.get('high_rate', []):
            anomaly_types.append('心率过快')
        if index in rule_anomalies.get('low_rate', []):
            anomaly_types.append('心率过慢')
        if index in rule_anomalies.get('extreme_value', []):
            anomaly_types.append('心率极值')
        if index in rule_anomalies.get('arrhythmia', []):
            anomaly_types.append('心律不齐')
        
        # 如果规则未检测到，根据心率值自动判断
        if len(anomaly_types) == 0:
            anomaly_types = self._classify_anomaly(window_data, index, current_rate)
        
        # 确定报警级别
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
        print(f"报警时间: {time_str}")
        print(f"用户ID:   {user_id}")
        print(f"数据点:   #{index}")
        print(f"当前心率: {current_rate:.1f} 次/分钟")
        print(f"异常类型: {', '.join(anomaly_types)}")
        print(f"置信度:   {confidence:.2%}")
        print(f"窗口数据 (共{len(window_data)}条):")
        print(f"  {' → '.join([f'{r:.1f}' for r in window_data])}")
        
        # 详细说明
        print(f"\n异常详情:")
        if '心率过快' in anomaly_types:
            high_count = len([r for r in window_data if r > 150])
            print(f"  • 心率持续超过150次/分钟，已连续{high_count}条")
        if '心率过慢' in anomaly_types:
            low_count = len([r for r in window_data if r < 60])
            print(f"  • 心率持续低于60次/分钟，已连续{low_count}条")
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
        
        print(f"\n累计异常: {self.total_anomalies + 1} 次")
        print("=" * 80)
    
    def _classify_anomaly(self, window_data, index, current_rate):
        """
        根据特征自动分类AI检测到的异常
        
        Args:
            window_data: 窗口数据
            index: 当前索引
            current_rate: 当前心率
            
        Returns:
            异常类型列表
        """
        anomaly_types = []
        
        # 1. 检查是否接近极值
        if current_rate >= 180 or current_rate <= 40:
            anomaly_types.append('心率极值')
        
        # 2. 检查是否接近高心率阈值
        elif current_rate > 140:
            high_count = sum(1 for r in window_data[max(0, index-5):index+1] if r > 140)
            if high_count >= 2:
                anomaly_types.append('心率过快')
        
        # 3. 检查是否接近低心率阈值
        elif current_rate < 65:
            low_count = sum(1 for r in window_data[max(0, index-5):index+1] if r < 65)
            if low_count >= 2:
                anomaly_types.append('心率过慢')
        
        # 4. 检查心率变化是否剧烈
        if index > 0:
            diff = abs(window_data[index] - window_data[index-1])
            if diff >= 25:
                if '心率过快' not in anomaly_types and '心率过慢' not in anomaly_types:
                    anomaly_types.append('心律不齐')
        
        # 5. 检查趋势
        if len(anomaly_types) == 0 and index >= 2:
            recent_rates = window_data[max(0, index-2):index+1]
            if len(recent_rates) >= 3:
                if recent_rates[-1] > recent_rates[0] + 40:
                    anomaly_types.append('心律不齐')
                elif recent_rates[0] > recent_rates[-1] + 40:
                    anomaly_types.append('心律不齐')
        
        return anomaly_types
    
    def start(self):
        """启动数据库轮询监听"""
        try:
            print("\n" + "="*80)
            print("🏥 井下实时心率监测系统 - 数据库轮询版本")
            print("="*80)
            print(f"🗄️  数据来源: MySQL employee_heart_rate")
            print(f"⏱️  轮询间隔: {self.poll_interval} 秒")
            print(f"📦  单次拉取上限: {self.poll_batch_size} 条")
            print("="*80 + "\n")

            if not self.db_manager:
                raise RuntimeError("数据库未初始化，无法启动轮询监测")

            self.running = True
            self.last_processed_id = self.db_manager.get_latest_heart_rate_id()
            print(f"✅ 当前最新记录ID: {self.last_processed_id}（仅处理后续新增数据）")
            print("🔄 开始轮询数据库...\n")

            while self.running:
                records = self._fetch_new_records()
                if not records:
                    time.sleep(self.poll_interval)
                    continue

                for record in records:
                    record_id = record.get('id')
                    if record_id is None:
                        continue
                    try:
                        record_id = int(record_id)
                    except (TypeError, ValueError):
                        continue
                    self.last_processed_id = max(self.last_processed_id, record_id)
                    self._handle_db_record(record)
            
        except KeyboardInterrupt:
            print("\n\n⏹️  收到停止信号，正在关闭...")
            self.stop()
        except Exception as e:
            print(f"❌ 启动错误: {e}")
            import traceback
            traceback.print_exc()
    
    def set_data_callback(self, callback):
        """
        设置数据回调函数（用于REST API）
        
        Args:
            callback: 回调函数，接收数据信息字典作为参数
        """
        self.data_callback = callback
    
    def subscribe(self, topic: str):
        """
        兼容旧接口：数据库轮询模式下无需订阅主题
        
        Args:
            topic: 主题字符串
        """
        print(f"ℹ️  数据库轮询模式已启用，忽略主题订阅: {topic}")
    
    def stop(self):
        """停止数据库轮询监听"""
        print("\n" + "="*80)
        print("📊 监测统计")
        print("="*80)
        print(f"总接收数据: {self.total_received} 条")
        print(f"总异常数量: {self.total_anomalies} 条")
        print(f"监测用户数: {len(self.user_data_cache)} 人")
        print("="*80 + "\n")
        self.running = False
        print("✅ 数据库轮询已停止")

if __name__ == "__main__":
    print(f"\n💡 提示: 可在 config.py 中修改 MONITOR_CONFIG 轮询参数\n")

    # 创建监测系统
    monitor = MQTTHeartRateMonitor()
    
    # 启动监听
    monitor.start()
