# MQTT数据接收和处理模块
# 通过MQTT订阅实时心率数据并进行异常检测


import json
import time
import os
from datetime import datetime
from typing import Dict, List
import paho.mqtt.client as mqtt
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
    from config import MQTT_CONFIG, MODEL_CONFIG, FILTER_CONFIG, REDIS_CONFIG
except ImportError:
    # 如果没有配置文件，使用默认配置
    MQTT_CONFIG = {
        'broker': 'localhost',
        'port': 1883,
        'username': None,
        'password': None,
        'topics': {
            'realtime': '/bdohs/data/#',
            'history': '/bdohs/datalist/#',
            'status': '$SYS/brokers/+/clients/+/connected',  # 客户端连接状态主题
            'disconnect': '$SYS/brokers/+/clients/+/disconnected'  # 客户端断开连接主题
        },
        'batch_size': 18,
        'keepalive': 60
    }
    REDIS_CONFIG = {
        'host': 'localhost',
        'port': 6379,
        'max_history_count': 60
    }


class MQTTHeartRateMonitor:
    """基于MQTT的心率监测系统"""
    
    def __init__(self, mqtt_broker=None, mqtt_port=None, enable_redis=True, enable_db=True):
        """
        初始化MQTT心率监测系统
        
        Args:
            mqtt_broker: MQTT服务器地址（可选，默认从配置读取）
            mqtt_port: MQTT服务器端口（可选，默认从配置读取）
            enable_redis: 是否启用Redis（默认True）
            enable_db: 是否启用数据库（默认True）
        """
        self.mqtt_broker = mqtt_broker or MQTT_CONFIG.get('broker', 'localhost')
        self.mqtt_port = mqtt_port or MQTT_CONFIG.get('port', 1883)
        
        # MQTT客户端
        self.client = mqtt.Client(client_id="HeartRateMonitor_" + str(int(time.time())))
        
        # 数据回调函数（用于REST API）
        self.data_callback = None
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # 如果配置了用户名密码，设置认证
        username = MQTT_CONFIG.get('username')
        password = MQTT_CONFIG.get('password')
        if username and password:
            self.client.username_pw_set(username, password)
        
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
        self.batch_size = MQTT_CONFIG.get('batch_size', 18)  # 每3分钟18条数据
        
        # 统计信息
        self.total_received = 0
        self.total_anomalies = 0
        
        # 订阅主题配置
        topics = MQTT_CONFIG.get('topics', {})
        self.realtime_topic = topics.get('realtime', '/bdohs/data/#')  # 实时数据
        self.history_topic = topics.get('history', '/bdohs/datalist/#')  # 历史数据
        
    def on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            print("✅ 成功连接到MQTT服务器")
            # 订阅实时数据和历史数据主题
            client.subscribe(self.realtime_topic)
            client.subscribe(self.history_topic)
            print(f"📡 已订阅主题: {self.realtime_topic}")
            print(f"📡 已订阅主题: {self.history_topic}")
            
            # 订阅客户端状态主题（监听设备上线/离线）
            topics = MQTT_CONFIG.get('topics', {})
            status_topic = topics.get('status', '$SYS/brokers/+/clients/+/connected')
            disconnect_topic = topics.get('disconnect', '$SYS/brokers/+/clients/+/disconnected')
            
            client.subscribe(status_topic)
            client.subscribe(disconnect_topic)
            print(f"📡 已订阅状态主题: {status_topic}")
            print(f"📡 已订阅状态主题: {disconnect_topic}")
        else:
            print(f"❌ 连接失败，错误代码: {rc}")
    
    def on_message(self, client, userdata, msg):
        """MQTT消息接收回调"""
        try:
            # 检查是否是客户端状态消息
            if 'connected' in msg.topic or 'disconnected' in msg.topic:
                self.process_client_status(msg)
                return
            
            # 解析JSON数据
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # 判断是单条数据还是批量数据
            if isinstance(payload, list):
                # 历史数据批量处理
                self.process_batch_data(payload)
            else:
                # 实时数据单条处理
                self.process_realtime_data(payload)
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
        except Exception as e:
            print(f"❌ 数据处理错误: {e}")
    
    def process_client_status(self, msg):
        """
        处理客户端在线/离线状态消息
        
        Args:
            msg: MQTT消息对象
        """
        try:
            # 解析主题获取客户端ID
            # 主题格式: $SYS/brokers/{broker}/clients/{clientId}/connected 或 disconnected
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 5:
                client_id = topic_parts[4]
                is_online = 'connected' in msg.topic
                
                # 解析消息体获取更多信息（如果有）
                try:
                    payload = json.loads(msg.payload.decode('utf-8'))
                    device_id = payload.get('userId') or payload.get('clientId') or client_id
                except:
                    device_id = client_id
                
                # 更新数据库中的设备状态
                if self.db_manager:
                    self.db_manager.update_device_status(device_id, client_id, is_online)
                    status_text = "上线" if is_online else "离线"
                    print(f"\n🔔 设备状态变更: {device_id} ({client_id}) -> {status_text}\n")
                else:
                    print(f"\n⚠️  设备状态变更但数据库未启用: {device_id} -> {'在线' if is_online else '离线'}\n")
                    
        except Exception as e:
            print(f"❌ 处理客户端状态失败: {e}")

    
    def process_realtime_data(self, data: Dict):
        """
        处理实时数据（单条）- 存入Redis
        
        Args:
            data: 单条心率数据
        """
        try:
            # 提取关键字段
            user_id = data.get('userId')
            heart_rate = float(data.get('dataVal'))
            data_time = data.get('dataTime')
            type_name = data.get('typeName')
            
            # 验证数据类型
            if type_name != "心率":
                return
            
            # 存入Redis历史数据
            if self.redis_storage:
                self.redis_storage.add_heart_rate(user_id, heart_rate, data_time)
            
            # 初始化用户数据缓存（临时用于批量分析触发）
            if user_id not in self.user_data_cache:
                self.user_data_cache[user_id] = []
            
            # 添加到临时缓存
            self.user_data_cache[user_id].append({
                'heart_rate': heart_rate,
                'time': data_time,
                'raw_data': data
            })
            
            self.total_received += 1
            
            # 每接收到一条数据就显示
            print(f"\n📊 接收实时数据 [用户{user_id}] 时间: {data_time} 心率: {heart_rate} bpm")
            
            # 从Redis获取历史数据量，判断是否需要分析
            if self.redis_storage:
                history_count = self.redis_storage.get_history_count(user_id)
                # 当历史数据达到批量大小时，进行批量分析
                if history_count >= self.batch_size:
                    self.analyze_user_data(user_id)
                    # 清空临时缓存
                    self.user_data_cache[user_id] = []
            else:
                # 如果没有Redis，使用原来的逻辑
                if len(self.user_data_cache[user_id]) >= self.batch_size:
                    self.analyze_user_data(user_id)
                
        except Exception as e:
            print(f"❌ 实时数据处理错误: {e}")
    
    def process_batch_data(self, data_list: List[Dict]):
        """
        处理批量历史数据 - 存入Redis
        
        Args:
            data_list: 历史数据列表
        """
        try:
            if not data_list:
                return
            
            print(f"\n📦 接收批量历史数据，共 {len(data_list)} 条")
            
            # 按用户分组
            user_groups = {}
            for data in data_list:
                user_id = data.get('userId')
                if user_id not in user_groups:
                    user_groups[user_id] = []
                
                heart_rate = float(data.get('dataVal'))
                data_time = data.get('dataTime')
                
                user_groups[user_id].append({
                    'heart_rate': heart_rate,
                    'timestamp': data_time
                })
            
            # 对每个用户的数据进行处理
            for user_id, user_data in user_groups.items():
                # 按时间排序
                user_data.sort(key=lambda x: x['timestamp'])
                
                # 批量存入Redis
                if self.redis_storage:
                    self.redis_storage.batch_add_heart_rates(user_id, user_data)
                
                self.total_received += len(user_data)
                
                # 立即分析
                self.analyze_user_data(user_id)
                
        except Exception as e:
            print(f"❌ 批量数据处理错误: {e}")
                
        except Exception as e:
            print(f"❌ 批量数据处理错误: {e}")
    
    def analyze_user_data(self, user_id):
        """
        分析用户心率数据 - 从Redis获取历史数据，支持两种检测模式
        
        Args:
            user_id: 用户ID
        """
        try:
            # 从Redis获取近10分钟的历史数据
            if self.redis_storage:
                history_data = self.redis_storage.get_recent_heart_rates(user_id)
                if not history_data:
                    print(f"⚠️  用户 {user_id} 暂无历史数据")
                    return
                
                # 转换为心率值数组
                heart_rates = np.array([item['heart_rate'] for item in history_data])
                time_list = [item['timestamp'] for item in history_data]
            else:
                # 降级到缓存数据
                if user_id not in self.user_data_cache or not self.user_data_cache[user_id]:
                    return
                user_data = self.user_data_cache[user_id]
                heart_rates = np.array([item['heart_rate'] for item in user_data])
                time_list = [item['time'] for item in user_data]
            
            data_count = len(heart_rates)
            
            print(f"\n{'='*80}")
            print(f"📊 心率数据分析 - 用户 {user_id}")
            print(f"{'='*80}")
            print(f"时间范围: {time_list[0]} 至 {time_list[-1]}")
            print(f"数据数量: {data_count} 条")
            print(f"{'='*80}")
            
            # 判断使用哪种检测模式（5条数据为分界线）
            min_continuous_data = 5  # 至少5条数据才进行连续异常检测
            
            if data_count >= min_continuous_data:
                # 模式1: 数据量多 - 连续心率异常检测
                print(f"\n🔍 检测模式: 连续心率异常分析 (数据充足: {data_count}条)")
                self.continuous_anomaly_detection(user_id, heart_rates, time_list)
            else:
                # 模式2: 数据量少 - 瞬时心率预警
                print(f"\n⚡ 检测模式: 瞬时心率预警 (数据较少: {data_count}条)")
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
                print(f"✅ 异常记录已保存到数据库")
            else:
                print(f"\n✅ 未发现连续异常")
            
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
        """启动MQTT监听"""
        try:
            print("\n" + "="*80)
            print("🏥 井下实时心率监测系统 - MQTT版本")
            print("="*80)
            print(f"🌐 MQTT服务器: {self.mqtt_broker}:{self.mqtt_port}")
            print(f"📡 订阅主题: {self.realtime_topic}, {self.history_topic}")
            print("="*80 + "\n")
            
            # 连接到MQTT服务器
            self.client.connect(self.mqtt_broker, self.mqtt_port, 
                              MQTT_CONFIG.get('keepalive', 60))
            
            # 开始循环监听
            print("🔄 开始监听MQTT消息...\n")
            self.client.loop_forever()
            
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
        订阅MQTT主题
        
        Args:
            topic: 主题字符串
        """
        self.client.subscribe(topic)
        print(f"📡 已订阅主题: {topic}")
    
    def stop(self):
        """停止MQTT监听"""
        print("\n" + "="*80)
        print("📊 监测统计")
        print("="*80)
        print(f"总接收数据: {self.total_received} 条")
        print(f"总异常数量: {self.total_anomalies} 条")
        print(f"监测用户数: {len(self.user_data_cache)} 人")
        print("="*80 + "\n")
        
        self.client.disconnect()
        self.client.loop_stop()
        print("✅ MQTT连接已关闭")


# 导入必要的库
import numpy as np


if __name__ == "__main__":
    # 从配置文件读取MQTT服务器信息
    try:
        from config import MQTT_CONFIG
        MQTT_BROKER = MQTT_CONFIG.get('broker', 'localhost')
        MQTT_PORT = MQTT_CONFIG.get('port', 1883)
    except ImportError:
        MQTT_BROKER = "localhost"
        MQTT_PORT = 1883
    
    print(f"\n💡 提示: 可在 config.py 中修改MQTT服务器配置\n")
    
    # 创建监测系统
    monitor = MQTTHeartRateMonitor(mqtt_broker=MQTT_BROKER, mqtt_port=MQTT_PORT)
    
    # 启动监听
    monitor.start()
