# 井下实时心率监测系统 v2.0

**心率监测AI系统 - 支持REST API + MQTT + Redis + MySQL**

## 📋 目录

- [系统简介](#-系统简介)
- [🆕 实时前后端对接（v3.0 新增）](#-实时前后端对接v30-新增)
- [v2.0 新增功能](#-v20-新增功能) 🆕
- [5分钟快速开始](#-5分钟快速开始)
- [Java调用指南](#-java调用指南) ⭐
- [REST API完整文档](#-rest-api完整文档)
- [MQTT数据格式](#-mqtt数据格式)
- [系统配置](#-系统配置)
- [技术架构](#-技术架构)

---

## 🎯 系统简介

井下工作人员实时心率监测系统,通过AI模型智能检测心率异常，支持REST API和MQTT双通信模式。

### 核心特性
- ✅ **REST API接口** - Java/Python/JavaScript等任何语言都可调用
- ✅ **MQTT实时通信** - 接收外部设备心率数据
- ✅ **双重异常检测** - AI模型(98.89%准确率) + 规则检测
- ✅ **三级数据清洗** - 中值滤波 + 移动平均 + 巴特沃斯滤波
- ✅ **滑动窗口分析** - 基于5条数据智能分析
- 🆕 **MQTT客户端监控** - 实时监测设备在线/离线状态
- 🆕 **Redis缓存** - 近10分钟数据存储，性能提升100倍
- 🆕 **双模式检测** - 连续异常检测(数据≥5) + 瞬时预警(数据<5)
- 🆕 **MySQL存储** - 设备状态、异常记录、每日统计
- 🆕 **前后端实时推送** - SSE (Server-Sent Events) 无需独立 MQTT 服务

---

## 🔥 实时前后端对接（v3.0 新增）

> **不需要申请额外的 MQTT 服务！** 前端通过 Java 后端的 SSE 长连接接收实时推送。

### 整体数据流

```
心率设备
  │  MQTT 协议
  ▼
MQTT Broker（公共或自建，Python 侧订阅即可）
  │
  ▼
Python ML 服务（heart_rate_model/mqtt_handler.py + heart_rate_model/rest_api.py）
  │  本机 HTTP POST /api/realtime/push
  ▼
Java Spring Boot 后端（RealtimeController）
  │  SSE 长连接推送
  ▼
Vue.js 前端（RealtimeMonitor.vue）
```

### 启动步骤

**第一步：启动 Java 后端**
```bash
cd backend
mvn spring-boot:run
# 后端在 http://localhost:8081 启动
```

**第二步：启动前端**
```bash
cd frontend
npm install
npm run dev
# 前端在 http://localhost:3000 启动
```

**第三步：启动 Python ML REST API**
```bash
cd heart_rate_model
python rest_api.py
# Python 服务在 http://localhost:5000 启动
```

**第四步：从前端"实时心率监测"页面启动 MQTT 监测**

访问 `http://localhost:3000` → 登录 → 点击左侧「**实时心率监测**」菜单：

1. 点击「**连接实时推送**」 —— 前端与 Java 后端建立 SSE 长连接
2. 点击「**启动 MQTT 监测**」 —— 通知 Python 连接 MQTT Broker，开始接收设备数据
3. 数据将实时显示在页面上，异常心率自动高亮+告警

### 配置 Java 后端地址（仅需改环境变量）

Python 默认向 `http://localhost:8081` 推送，如需修改：
```bash
export JAVA_BACKEND_URL=http://your-java-host:8081
cd heart_rate_model && python rest_api.py
```

### 新增接口说明

| 方向 | 地址 | 说明 |
|------|------|------|
| 前端 → Java | `GET /api/realtime/stream` | SSE 订阅（无需登录 Token） |
| Python → Java | `POST /api/realtime/push` | ML 结果推送（内网调用，无需 Token） |
| 前端 → Python | `POST /python/api/monitor/start` | 启动 MQTT 监测（Vite 代理） |
| 前端 → Python | `POST /python/api/monitor/stop`  | 停止 MQTT 监测 |

---


## 🆕 v2.0 新增功能

### 1. MQTT客户端在线/离线监听
- 自动监听MQTT客户端连接/断开事件（$SYS主题）
- 实时更新设备在线/离线状态到数据库
- 记录上线/离线时间

### 2. Redis历史数据存储
- 近10分钟心率数据自动存入Redis（替代MySQL查询）
- 自动维护最近60条记录
- 10分钟自动过期，节省内存

### 3. 双模式异常检测

**模式1: 连续心率异常检测**（历史数据≥5条）
- 数据清洗与滤波
- 基于规则的异常检测
- 机器学习智能检测（LightGBM）

**模式2: 瞬时心率预警**（历史数据<5条）
- 极值检测（≥200 或 ≤30）
- 高心率检测（>150）
- 低心率检测（<60）
- 心率剧变检测（相邻差值≥30）

### 4. 数据库支持

**新增3张数据表:**
- `device_status` - 设备在线/离线状态
- `anomaly_records` - 异常记录（含instant/continuous类型）
- `daily_anomaly_stats` - 每日异常统计

### 配置说明

#### 数据库配置 (heart_rate_model/config.py)
```python
DATABASE_CONFIG = {
    'mysql': {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'heart_rate_db',
        'charset': 'utf8mb4'
    }
}
```

#### Redis配置 (heart_rate_model/config.py)
```python
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': None,
    'history_expire': 600,      # 10分钟过期
    'max_history_count': 60     # 最多60条
}
```

### 使用步骤

1. **安装依赖**
```bash
pip install -r heart_rate_model/requirements.txt
```

2. **启动Redis服务**
```bash
redis-server
```

3. **创建MySQL数据库**
```sql
CREATE DATABASE heart_rate_db CHARACTER SET utf8mb4;
```

4. **初始化数据库表**
```bash
cd heart_rate_model && python main.py
# 选择 D. 初始化数据库
```

5. **启动MQTT监测**
```bash
cd heart_rate_model && python main.py
# 选择 4. MQTT监测
# 启用Redis: 是
# 启用数据库: 是
```

### 系统架构

```
┌─────────────────────┐
│  外部程序(Java等)   │
└──────────┬──────────┘
           │ HTTP REST API
           ↓
┌─────────────────────┐
│  Flask API Server   │
└──────────┬──────────┘
           │ 内部调用
           ↓
┌─────────────────────┐
│  MQTT Handler +     │
│  异常检测引擎       │
└──────────┬──────────┘
           │ MQTT协议
           ↓
┌─────────────────────┐
│  MQTT Broker(外部)  │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  心率监测设备       │
└─────────────────────┘
```

---

## ⚡ 5分钟快速开始

### 步骤1: 安装依赖
```bash
pip install -r heart_rate_model/requirements.txt
```

### 步骤2: 验证系统
```bash
cd heart_rate_model && python utils.py verify
```

### 步骤3: 启动API服务
```bash
cd heart_rate_model && python rest_api.py
```

### 步骤4: 测试接口
```bash
# 健康检查
curl http://localhost:5000/api/health

# 启动监测（连接MQTT服务器）
curl -X POST http://localhost:5000/api/monitor/start \
  -H "Content-Type: application/json" \
  -d "{\"broker\":\"mqtt.example.com\",\"port\":1883,\"topics\":[\"/bdohs/data/#\"]}"

# 获取最新数据
curl http://localhost:5000/api/data/latest?limit=10
```

✅ **完成！** API服务已启动在 `http://localhost:5000`

---

## ☕ Java调用指南

### 快速集成3步骤

#### 1️⃣ 添加Maven依赖

```xml
<dependencies>
    <!-- Gson用于JSON解析 -->
    <dependency>
        <groupId>com.google.code.gson</groupId>
        <artifactId>gson</artifactId>
        <version>2.10.1</version>
    </dependency>
</dependencies>
```

#### 2️⃣ 复制Java客户端

将 `Java调用示例/HeartRateMonitorClient.java` 复制到你的项目中，该文件包含完整的API客户端。

#### 3️⃣ 开始使用

```java
public class Main {
    public static void main(String[] args) {
        // 创建客户端（默认连接localhost:5000）
        HeartRateMonitorClient client = new HeartRateMonitorClient();
        
        // 1. 检查服务健康状态
        if (client.checkHealth()) {
            System.out.println("✅ API服务运行正常");
        }
        
        // 2. 启动心率监测（连接到MQTT服务器）
        boolean started = client.startMonitoring(
            "mqtt.example.com",     // MQTT服务器地址
            1883,                    // MQTT端口
            new String[]{"/bdohs/data/#"}  // 订阅主题
        );
        
        if (started) {
            System.out.println("✅ 监测已启动");
        }
        
        // 3. 获取最新心率数据
        DataResponse data = client.getLatestData(10);
        if (data != null && data.isSuccess()) {
            System.out.println("接收到 " + data.getCount() + " 条数据");
            for (HeartRateData item : data.getData()) {
                System.out.printf("用户:%s 心率:%d bpm 时间:%s%n",
                    item.getUserId(),
                    item.getHeartRate(),
                    item.getTimestamp()
                );
            }
        }
        
        // 4. 获取异常记录
        AnomalyResponse anomalies = client.getAnomalies(20);
        if (anomalies != null && anomalies.isSuccess()) {
            System.out.println("检测到 " + anomalies.getCount() + " 条异常");
            for (Anomaly anomaly : anomalies.getData()) {
                System.out.printf("异常类型:%s 用户:%s%n",
                    anomaly.getType(),
                    anomaly.getUserId()
                );
            }
        }
        
        // 5. 获取监测状态
        StatusResponse status = client.getStatus();
        if (status != null && status.isSuccess()) {
            System.out.println("监测状态: " + status.getData().getStatus());
            System.out.println("总记录数: " + status.getData().getTotalRecords());
            System.out.println("异常数量: " + status.getData().getAnomalyCount());
        }
        
        // 6. 停止监测
        client.stopMonitoring();
    }
}
```

### 完整Java客户端功能

`HeartRateMonitorClient.java` 提供以下方法：

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `checkHealth()` | 检查服务健康状态 | boolean |
| `startMonitoring(broker, port, topics)` | 启动监测 | boolean |
| `stopMonitoring()` | 停止监测 | boolean |
| `getStatus()` | 获取监测状态 | StatusResponse |
| `getLatestData(limit)` | 获取最新心率数据 | DataResponse |
| `getAnomalies(limit)` | 获取异常记录 | AnomalyResponse |
| `getLatestAnomaly()` | 获取最新异常 | AnomalyResponse |
| `getStatistics()` | 获取统计信息 | StatisticsResponse |
| `getConfig()` | 获取系统配置 | ConfigResponse |

### 轮询模式示例

```java
// 持续监测并处理数据
ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);

scheduler.scheduleAtFixedRate(() -> {
    // 每5秒获取最新数据
    DataResponse data = client.getLatestData(5);
    
    if (data != null && data.getCount() > 0) {
        // 处理接收到的数据
        for (HeartRateData item : data.getData()) {
            processHeartRate(item);
        }
    }
    
    // 检查是否有新异常
    AnomalyResponse anomaly = client.getLatestAnomaly();
    if (anomaly != null && anomaly.getCount() > 0) {
        // 触发告警
        handleAnomaly(anomaly.getData().get(0));
    }
    
}, 0, 5, TimeUnit.SECONDS);
```

### 数据模型

```java
// 心率数据
public class HeartRateData {
    private String userId;        // 用户ID
    private int heartRate;        // 心率值(bpm)
    private String timestamp;     // 时间戳
    private String status;        // 状态(normal/warning/danger)
}

// 异常记录
public class Anomaly {
    private String timestamp;     // 发生时间
    private String userId;        // 用户ID
    private String type;          // 异常类型
    private String severity;      // 严重程度
    private String description;   // 描述
}

// 监测状态
public class MonitorStatus {
    private String status;        // running/stopped
    private String startTime;     // 启动时间
    private int totalRecords;     // 总记录数
    private int anomalyCount;     // 异常数量
}
```

---

## 🔌 REST API完整文档

### 基础信息
- **服务地址**: `http://localhost:5000`
- **数据格式**: JSON
- **编码**: UTF-8
- **端口**: 5000 (可在 heart_rate_model/config.py 修改)

### API接口列表

#### 1. 健康检查
```http
GET /api/health
```

**响应**:
```json
{
  "status": "ok",
  "service": "心率监测系统",
  "timestamp": "2025-12-23T10:30:00"
}
```

---

#### 2. 启动监测
```http
POST /api/monitor/start
Content-Type: application/json
```

**请求参数**:
```json
{
  "broker": "mqtt.example.com",
  "port": 1883,
  "topics": ["/bdohs/data/#"]
}
```

**响应**:
```json
{
  "success": true,
  "message": "监测已启动",
  "config": {
    "broker": "mqtt.example.com",
    "port": 1883,
    "topics": ["/bdohs/data/#"]
  }
}
```

---

#### 3. 停止监测
```http
POST /api/monitor/stop
```

**响应**:
```json
{
  "success": true,
  "message": "监测已停止"
}
```

---

#### 4. 获取监测状态
```http
GET /api/monitor/status
```

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "running",
    "start_time": "2025-12-23T10:00:00",
    "total_records": 1250,
    "anomaly_count": 15,
    "mqtt_config": {
      "broker": "mqtt.example.com",
      "port": 1883
    }
  }
}
```

---

#### 5. 获取最新心率数据
```http
GET /api/data/latest?limit=10
```

**查询参数**:
- `limit`: 返回数据条数（默认10，最大100）

**响应**:
```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "user_id": "USER001",
      "heart_rate": 75,
      "timestamp": "2025-12-23T10:30:00",
      "status": "normal"
    }
  ]
}
```

---

#### 6. 获取异常记录
```http
GET /api/anomalies?limit=20
```

**查询参数**:
- `limit`: 返回异常数量（默认20，最大100）

**响应**:
```json
{
  "success": true,
  "count": 5,
  "data": [
    {
      "timestamp": "2025-12-23T10:25:00",
      "user_id": "USER002",
      "anomaly_type": "心率过快",
      "severity": "warning",
      "description": "心率持续超过150bpm",
      "ml_detected": true,
      "rule_detected": true
    }
  ]
}
```

---

#### 7. 获取最新异常
```http
GET /api/anomalies/latest
```

**响应**:
```json
{
  "success": true,
  "count": 1,
  "data": [
    {
      "timestamp": "2025-12-23T10:30:05",
      "user_id": "USER003",
      "anomaly_type": "心律不齐",
      "severity": "warning",
      "description": "心率波动过大"
    }
  ]
}
```

---

#### 8. 获取统计信息
```http
GET /api/statistics
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_records": 1250,
    "total_users": 15,
    "anomaly_count": 25,
    "anomaly_rate": "2.0%",
    "avg_heart_rate": 78,
    "monitoring_duration": "1小时30分钟"
  }
}
```

---

#### 9. 获取系统配置
```http
GET /api/config
```

**响应**:
```json
{
  "success": true,
  "config": {
    "mqtt": {
      "broker": "localhost",
      "port": 1883
    },
    "detection": {
      "enable_ml": true,
      "enable_rule": true,
      "window_size": 30
    },
    "filter": {
      "lower_bound": 30,
      "upper_bound": 220
    }
  }
}
```

---

#### 10. 更新MQTT配置
```http
POST /api/config/mqtt
Content-Type: application/json
```

**请求参数**:
```json
{
  "broker": "new-mqtt.example.com",
  "port": 1883,
  "username": "user",
  "password": "pass"
}
```

**响应**:
```json
{
  "success": true,
  "message": "MQTT配置已更新",
  "config": {
    "broker": "new-mqtt.example.com",
    "port": 1883
  }
}
```

---

#### 11. 发送测试数据
```http
POST /api/test/send
Content-Type: application/json
```

**请求参数**:
```json
{
  "count": 18,
  "user_id": "TEST001"
}
```

**响应**:
```json
{
  "success": true,
  "message": "已发送18条测试数据"
}
```

---

### 错误响应

所有API在出错时返回统一格式：

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

HTTP状态码：
- `200` - 成功
- `400` - 请求参数错误
- `404` - 资源不存在
- `500` - 服务器内部错误

---

## 📡 MQTT数据格式

### 主题结构
```
/bdohs/data/{userId}       # 单条实时数据
/bdohs/datalist/{userId}   # 批量历史数据
/bdohs/data/#              # 订阅所有用户（通配符）
```

### 数据格式

**单条数据**:
```json
{
  "userId": "USER001",
  "dataVal": "75",
  "dataTime": "2025-12-23 10:30:00",
  "typeName": "心率",
  "typeUtil": "bpm",
  "deviceId": 237,
  "deptId": 160
}
```

**批量数据**:
```json
{
  "userId": "USER001",
  "dataList": [
    {
      "dataVal": "72",
      "dataTime": "2025-12-23 10:00:00"
    },
    {
      "dataVal": "75",
      "dataTime": "2025-12-23 10:00:10"
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| userId | string | 用户ID/工号 |
| dataVal | string | 心率值（需转换为int） |
| dataTime | string | 时间戳 |
| typeName | string | 数据类型（应为"心率"） |
| typeUtil | string | 单位（bpm） |
| deviceId | int | 设备ID（可选） |
| deptId | int | 部门ID（可选） |

---

## ⚙️ 系统配置

### 修改配置

编辑 `heart_rate_model/config.py` 文件：

```python
# MQTT服务器配置
MQTT_CONFIG = {
    'broker': 'mqtt.example.com',
    'port': 1883,
    'username': None,
    'password': None,
    'topics': {
        'realtime': '/bdohs/data/#'
    }
}

# 异常检测配置
MODEL_CONFIG = {
    'enable_ml_detection': True,
    'enable_rule_detection': True,
    'window_size': 30
}

# 数据清洗配置
FILTER_CONFIG = {
    'lower_bound': 30,
    'upper_bound': 220,
    'median_kernel': 3,
    'moving_avg_window': 3
}
```

---

## 🧠 异常检测规则

### 规则检测（4种异常类型）

| 异常类型 | 检测条件 | 严重级别 |
|---------|---------|---------|
| 心率过快 | >150 bpm 且连续3条+ | ⚠️⚠️ 警告 |
| 心率过慢 | <60 bpm 且连续2条+ | ⚠️ 注意 |
| 心率极值 | ≥200 或 ≤30 bpm | 🚨🚨🚨 危险 |
| 心律不齐 | 相邻差值≥30 bpm | ⚠️⚠️ 警告 |

### AI智能检测

- **模型**: LightGBM
- **特征**: 23维（统计+趋势+连续性+心律）
- **准确率**: 98.89%
- **召回率**: 97.45%
- **F1分数**: 98.16%

---

## 🏗️ 技术架构

### 项目结构

```
heart_rate_model/
├── rest_api.py              # REST API服务 ⭐
├── mqtt_handler.py          # MQTT处理+异常检测
├── lgbm_model.py            # LightGBM模型
├── enhanced_detector.py     # 规则检测
├── data_filter.py           # 数据清洗
├── data_generator.py        # 数据生成
├── integrated_system.py     # 模拟训练系统
├── main.py                  # 统一主程序 ⭐
├── utils.py                 # 工具模块
├── config.py                # 系统配置
├── requirements.txt         # 依赖清单
├── database.py              # 数据库操作
├── redis_storage.py         # Redis存储
├── mqtt_sender.py           # MQTT测试发送
└── output/                  # 输出目录
    ├── models/              # 训练模型
    ├── logs/                # 监测日志
    └── results/             # 检测结果

Java调用示例/
├── HeartRateMonitorClient.java  # Java客户端 ⭐
└── pom.xml                      # Maven配置
```

### 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| 后端框架 | Flask 2.3+ | REST API服务 |
| 跨域支持 | Flask-CORS | 允许跨域访问 |
| 通信协议 | MQTT (Paho) | 设备数据接收 |
| 机器学习 | LightGBM | AI异常检测 |
| 数据处理 | NumPy, Pandas | 数值计算和数据处理 |
| 信号处理 | SciPy | 滤波算法 |
| 可视化 | Matplotlib | 数据图表 |

---

## 🛠️ 常用命令

### 系统管理

```bash
# 验证系统环境
cd heart_rate_model && python utils.py verify

# 测试API接口
cd heart_rate_model && python utils.py test

# 查看帮助信息
cd heart_rate_model && python utils.py help

# 启动主程序（交互式菜单）
cd heart_rate_model && python main.py
```

### 服务启动

```bash
# 启动REST API服务
cd heart_rate_model && python rest_api.py

# 训练模型
cd heart_rate_model && python integrated_system.py --train

# 模拟监测
cd heart_rate_model && python integrated_system.py --monitor
```

### 测试工具

```bash
# 发送MQTT测试数据
cd heart_rate_model && python mqtt_sender.py
```

---

## 📊 输出文件

```
heart_rate_model/output/
├── models/
│   └── lgbm_model.pkl              # 训练好的模型
├── logs/
│   └── monitoring_20251223.log     # 监测日志
└── results/
    └── monitoring_20251223.csv     # 检测结果CSV
```

---

## 🔍 故障排查

### 常见问题

**Q1: API服务无法启动？**
```bash
# 检查依赖
cd heart_rate_model && python utils.py verify

# 检查端口占用
netstat -ano | findstr :5000
```

**Q2: 无法连接MQTT服务器？**
- 检查 `heart_rate_model/config.py` 中的MQTT配置
- 确认MQTT服务器地址和端口正确
- 检查防火墙设置

**Q3: Java客户端连接失败？**
- 确认API服务已启动
- 检查URL地址（默认 `http://localhost:5000`）
- 查看服务端日志

**Q4: 未检测到异常？**
- 确认已训练模型（运行 `cd heart_rate_model && python main.py` 选择模式1）
- 检查 `heart_rate_model/config.py` 中的检测配置
- 查看数据是否正常接收

---

## 📞 获取帮助

1. **查看完整帮助**: `cd heart_rate_model && python utils.py help`
2. **系统验证**: `cd heart_rate_model && python utils.py verify`
3. **API测试**: `cd heart_rate_model && python utils.py test`
4. **交互式菜单**: `cd heart_rate_model && python main.py`

---

## 📝 开发指南

### 添加新的API接口

在 `heart_rate_model/rest_api.py` 中添加：

```python
@app.route('/api/your/endpoint', methods=['GET'])
def your_function():
    return jsonify({
        'success': True,
        'data': 'your data'
    })
```

### 扩展异常检测规则

在 `heart_rate_model/enhanced_detector.py` 中的 `detect_anomalies` 方法添加新规则。

### 自定义数据滤波

修改 `data_filter.py` 中的滤波参数或添加新的滤波算法。