# 井下实时心率监测系统 - 统一配置文件
# 修改此文件以调整系统参数

# ==================== MQTT配置 ====================
MQTT_CONFIG = {
    # MQTT服务器地址和端口
    'broker': 'broker.emqx.io',  # 使用公共MQTT测试服务器
    'port': 1883,
    
    # 认证信息（如果需要）
    'username': None,  # 例如: 'admin'
    'password': None,  # 例如: 'password123'
    
    # 订阅主题
    'topics': {
        'realtime': '/bdohs/data/#',      # 实时数据主题
        'history': '/bdohs/datalist/#',   # 历史数据主题
        'status': '$SYS/brokers/+/clients/+/connected',      # 客户端上线主题
        'disconnect': '$SYS/brokers/+/clients/+/disconnected'  # 客户端离线主题
    },
    
    # 数据参数
    'batch_size': 18,      # 每批数据量（3分钟/10秒 = 18条）
    'keepalive': 60,       # 保持连接时间（秒）
    'clean_session': True  # 是否清除会话
}

# ==================== 模型配置 ====================
MODEL_CONFIG = {
    # 模型文件路径
    'model_path': 'output/models/lgbm_model.pkl',
    
    # 检测开关
    'enable_ml_detection': True,    # 是否启用机器学习检测
    'enable_rule_detection': True,  # 是否启用规则检测
    
    # 滑动窗口参数
    'window_size': 30  # 5分钟/10秒 = 30条
}

# ==================== 数据清洗配置 ====================
FILTER_CONFIG = {
    # 心率有效范围（超出范围视为异常值需清洗）
    'lower_bound': 30,   # 最低心率（次/分钟）
    'upper_bound': 220,  # 最高心率（次/分钟）
    
    # 滤波器参数
    'median_kernel': 3,          # 中值滤波窗口大小
    'moving_avg_window': 3,      # 移动平均窗口大小
    'butterworth_cutoff': 0.02,  # 巴特沃斯滤波截止频率
    'butterworth_order': 2       # 巴特沃斯滤波阶数
}

# ==================== 异常检测规则配置 ====================
DETECTOR_CONFIG = {
    # 心率过快检测
    'high_rate_threshold': 150,    # 阈值（次/分钟）
    'high_rate_consecutive': 3,    # 连续条数
    
    # 心率过慢检测
    'low_rate_threshold': 60,      # 阈值（次/分钟）
    'low_rate_consecutive': 2,     # 连续条数
    
    # 极值报警
    'extreme_high': 200,  # 极高值（次/分钟）
    'extreme_low': 30,    # 极低值（次/分钟）
    
    # 心律不齐检测
    'arrhythmia_threshold': 30  # 相邻差值阈值（次/分钟）
}

# ==================== 数据生成配置 ====================
GENERATOR_CONFIG = {
    # 基础参数
    'batch_size': 18,           # 每批数据量
    'sampling_interval': 10,    # 采样间隔（秒）
    'base_heart_rate': 75,      # 基础心率（次/分钟）
    
    # 异常概率
    'anomaly_prob': 0.15,  # 异常数据概率（15%）
    
    # 环境因素模拟
    'simulate_environment': True  # 是否模拟井下环境
}

# ==================== 日志配置 ====================
LOG_CONFIG = {
    # 日志开关
    'save_logs': True,     # 是否保存监测日志
    'save_results': True,  # 是否保存检测结果
    
    # 日志路径
    'log_dir': 'output/logs',        # 日志目录
    'result_dir': 'output/results',  # 结果目录
    
    # 显示设置
    'verbose': True,  # 是否显示详细信息
    'show_window_data': True  # 是否显示完整窗口数据
}

# ==================== 训练配置 ====================
TRAIN_CONFIG = {
    # 训练参数
    'default_batches': 200,  # 默认训练批次
    'test_size': 0.2,        # 测试集比例
    
    # LightGBM参数
    'lgbm_params': {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'verbose': -1
    },
    
    # 训练轮数
    'num_boost_round': 100
}

# ==================== 监测配置 ====================
MONITOR_CONFIG = {
    # 监测间隔
    'default_interval': 180,  # 默认监测间隔（秒）
    
    # 数据保存
    'save_monitoring_data': True,  # 是否保存监测数据
    'max_cache_size': 60  # 最大缓存数据条数
}

# ==================== 数据库配置 ====================
DATABASE_CONFIG = {
    # MySQL配置
    'mysql': {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'yk_demo',
        'charset': 'utf8mb4'
    }
}

# ==================== Redis配置 ====================
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': None,  # 如果需要密码
    'decode_responses': True,  # 自动解码为字符串
    'history_expire': 600,  # 历史数据过期时间（秒）默认10分钟
    'max_history_count': 60  # 每个设备最多存储60条历史记录（10分钟）
}
