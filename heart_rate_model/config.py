# 井下实时心率监测系统 - 统一配置文件
# 修改此文件以调整系统参数

# ==================== MQTT配置（保留，兼容旧版） ====================
MQTT_CONFIG = {
    'broker': 'broker.emqx.io',
    'port': 1883,
    'username': None,
    'password': None,
    'batch_size': 18,
    'keepalive': 60,
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
    'poll_interval': 5,  # 数据库轮询间隔（秒）
    'poll_batch_size': 100,  # 每次轮询读取的最大记录数
    'continuous_batch_size': 18,  # 累计新增到该条数后触发一次连续异常检测
    
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
