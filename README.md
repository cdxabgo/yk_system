# yk_system（井下实时心率监测系统）

一个用于“心率数据采集 → 异常检测 → 实时展示”的联调项目：

- **后端（Java / Spring Boot）**：业务 API、SSE 实时推送
- **前端（Vue3 + Vite）**：监测页面与看板
- **Python 服务（Flask）**：心率分析与数据推送

---

## 1. 项目结构

```text
yk_system/
├── backend/             # Java 后端（8081）
├── frontend/            # Vue 前端（3000）
├── heart_rate_model/    # Python 服务（5000）
└── Java调用示例/         # Java 调用示例
```

---

## 2. 核心链路（实时联调）

```text
心率数据 -> Python 服务 -> POST /api/realtime/push -> Java 后端 -> SSE /api/realtime/stream -> 前端
```

> 前端实时展示走 **SSE**，不需要前端直接接 MQTT。

---

## 3. 环境要求

- **Java 21**（backend `pom.xml` 目标版本）
- **Node.js 18+**
- **Python 3.9+**
- **MySQL 8+**（默认库名：`yk_demo`）

---

## 4. 快速启动（推荐顺序）

### 4.1 启动 Java 后端

```bash
cd /home/runner/work/yk_system/yk_system/backend
mvn spring-boot:run
```

- 默认地址：`http://localhost:8081`

### 4.2 启动前端

```bash
cd /home/runner/work/yk_system/yk_system/frontend
npm install
npm run dev
```

- 默认地址：`http://localhost:3000`

### 4.3 启动 Python 服务

```bash
cd /home/runner/work/yk_system/yk_system/heart_rate_model
pip install -r requirements.txt
python rest_api.py
```

- 默认地址：`http://localhost:5000`

---

## 5. 联调要点（你关心的点）

### 可以同时开“后端模拟器 + Python 服务”吗？

**可以。** 两边数据都会进入同一套链路。

后端模拟器开关在：
`/home/runner/work/yk_system/yk_system/backend/src/main/resources/application.yml`

```yaml
heart-rate:
  simulator:
    enabled: false
```

- `false`：默认关闭（推荐真实联调）
- `true`：开启模拟数据（演示/兜底测试用）

> 建议：进行 Python 真链路排查时保持 `enabled: false`，避免模拟数据干扰判断。

### Python 推送 Java 地址如何改？

默认推送到 `http://localhost:8081`，可通过环境变量修改：

```bash
export JAVA_BACKEND_URL=http://your-java-host:8081
```

---

## 6. 关键接口

### Java 后端

- `GET /api/realtime/stream`：前端 SSE 订阅
- `POST /api/realtime/push`：Python 推送实时结果

### Python 服务

- `GET /api/health`：健康检查
- `POST /api/monitor/start`：启动监测
- `POST /api/monitor/stop`：停止监测
- `GET /api/monitor/status`：监测状态

前端开发代理：

- `/api` → `http://localhost:8081`
- `/python` → `http://localhost:5000`

---

## 7. 常见问题

### 1）后端 `mvn test` 报 `invalid target release: 21`

你的本地 JDK 版本低于 21。切换到 Java 21 后再执行。

### 2）前端能打开但没有实时数据

按顺序检查：

1. Java、前端、Python 三个服务是否都已启动
2. Python 是否成功调用了 `/api/realtime/push`
3. 前端页面是否已连接 SSE（`/api/realtime/stream`）

### 3）如何只做前后端联调，不引入模拟数据

保持：

```yaml
heart-rate:
  simulator:
    enabled: false
```

---

## 8. 一组常用命令

```bash
# frontend 构建
cd /home/runner/work/yk_system/yk_system/frontend && npm run build

# backend 测试（需要 Java 21）
cd /home/runner/work/yk_system/yk_system/backend && mvn test

# python 服务启动
cd /home/runner/work/yk_system/yk_system/heart_rate_model && python rest_api.py
```
