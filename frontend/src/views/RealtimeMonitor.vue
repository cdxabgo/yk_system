<template>
  <div class="realtime-container">
    <!-- 顶部控制栏 -->
    <el-card class="control-card">
      <div class="control-row">
        <div class="status-section">
          <span class="status-label">实时推送连接：</span>
          <el-tag :type="sseStatus === 'connected' ? 'success' : sseStatus === 'connecting' ? 'warning' : 'danger'">
            <el-icon style="margin-right:4px">
              <component :is="sseStatus === 'connected' ? 'CircleCheck' : sseStatus === 'connecting' ? 'Loading' : 'CircleClose'" />
            </el-icon>
            {{ sseStatusText }}
          </el-tag>
          <span class="clients-tip" v-if="sseStatus === 'connected'">已接收 {{ totalReceived }} 条数据</span>
        </div>

        <div class="action-section">
          <el-button
            :type="sseStatus === 'connected' ? 'danger' : 'primary'"
            :icon="sseStatus === 'connected' ? 'VideoPause' : 'VideoPlay'"
            @click="toggleSse"
          >
            {{ sseStatus === 'connected' ? '断开连接' : '连接实时推送' }}
          </el-button>

          <el-divider direction="vertical" />

          <span class="mqtt-label">Python 监测服务：</span>
          <el-tag :type="mqttStatus === 'running' ? 'success' : 'info'" size="small">
            {{ mqttStatus === 'running' ? '▶ 运行中' : '■ 未运行' }}
          </el-tag>
          <el-button
            v-if="mqttStatus !== 'running'"
            type="success"
            size="small"
            :icon="'VideoPlay'"
            :loading="startingMqtt"
            style="margin-left:8px"
            @click="startMqttMonitor"
          >启动 MQTT 监测</el-button>
          <el-button
            v-else
            type="warning"
            size="small"
            :icon="'VideoPause'"
            style="margin-left:8px"
            @click="stopMqttMonitor"
          >停止</el-button>
        </div>
      </div>
    </el-card>

    <div class="main-content">
      <!-- 左侧：职工实时心率卡片 -->
      <div class="cards-section">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon style="vertical-align:middle;margin-right:6px"><Odometer /></el-icon>
                职工实时心率
              </span>
              <el-button :icon="'RefreshRight'" size="small" @click="clearData">清空</el-button>
            </div>
          </template>

          <div v-if="Object.keys(userCards).length === 0" class="empty-hint">
            <el-empty description="暂无实时数据，请先连接并启动 MQTT 监测" />
          </div>

          <div v-else class="user-cards">
            <div
              v-for="(card, uid) in userCards"
              :key="uid"
              :class="['user-card', card.isAbnormal ? 'card-abnormal' : 'card-normal']"
            >
              <div class="card-uid">用户 {{ uid }}</div>
              <div class="card-rate" :class="card.isAbnormal ? 'rate-danger' : 'rate-ok'">
                {{ card.heartRate !== null ? card.heartRate.toFixed(0) : '--' }}
                <span class="rate-unit">bpm</span>
              </div>
              <div class="card-time">{{ card.dataTime }}</div>
              <div class="card-status">
                <el-tag :type="card.isAbnormal ? 'danger' : 'success'" size="small">
                  {{ card.isAbnormal ? '⚠ 异常' : '✓ 正常' }}
                </el-tag>
              </div>
              <!-- 心率迷你趋势条 -->
              <div class="mini-trend" v-if="card.history.length > 1">
                <span
                  v-for="(v, i) in card.history.slice(-20)"
                  :key="i"
                  class="trend-bar"
                  :style="{ height: trendBarHeight(v) + 'px', background: trendBarColor(v) }"
                  :title="`${v} bpm`"
                />
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧：异常告警列表 -->
      <div class="alerts-section">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon style="vertical-align:middle;margin-right:6px;color:#f56c6c"><Warning /></el-icon>
                异常告警
                <el-badge v-if="alerts.length > 0" :value="alerts.length" type="danger" style="margin-left:6px" />
              </span>
              <el-button :icon="'Delete'" size="small" @click="clearAlerts">清空</el-button>
            </div>
          </template>

          <div v-if="alerts.length === 0" class="empty-hint">
            <el-empty description="暂无异常告警" />
          </div>

          <el-scrollbar max-height="600px" v-else>
            <div
              v-for="(alert, idx) in [...alerts].reverse()"
              :key="idx"
              class="alert-item"
            >
              <div class="alert-top">
                <el-tag type="danger" size="small">异常</el-tag>
                <span class="alert-uid">用户 {{ alert.userId }}</span>
                <span class="alert-time">{{ alert.dataTime }}</span>
              </div>
              <div class="alert-body">
                <span class="alert-rate" style="color:#f56c6c;font-weight:bold">
                  {{ alert.heartRate !== null ? alert.heartRate.toFixed(0) : '--' }} bpm
                </span>
                <span v-if="alert.anomalyType" class="alert-type">{{ alert.anomalyType }}</span>
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Odometer, Warning, CircleCheck, CircleClose, Loading,
  VideoPlay, VideoPause, RefreshRight, Delete
} from '@element-plus/icons-vue'

// ─── SSE 状态 ───────────────────────────────────────────────
const sseStatus = ref('disconnected')  // 'connecting' | 'connected' | 'disconnected'
const sseStatusText = computed(() => ({
  connecting: '连接中...',
  connected: '已连接',
  disconnected: '未连接'
}[sseStatus.value]))

let eventSource = null
const totalReceived = ref(0)

// ─── Python MQTT 监测服务状态 ────────────────────────────────
const mqttStatus = ref('stopped')  // 'running' | 'stopped'
const startingMqtt = ref(false)

// ─── 心率阈值常量 ────────────────────────────────────────────
const HR_EXTREME_HIGH = 200   // 极高心率（危险）
const HR_EXTREME_LOW  = 30    // 极低心率（危险）
const HR_HIGH         = 150   // 高心率（警告）
const HR_LOW          = 60    // 低心率（警告）

// MQTT 默认配置（可在 config.py 中修改后，由后端下发）
const DEFAULT_MQTT_BROKER = 'broker.emqx.io'
const DEFAULT_MQTT_PORT   = 1883
const DEFAULT_MQTT_TOPICS = ['/bdohs/data/#']

// ─── 实时数据 ────────────────────────────────────────────────
// userCards: { [userId]: { heartRate, dataTime, isAbnormal, anomalyType, history: [] } }
const userCards = reactive({})
const alerts = ref([])

// ─── SSE 连接 ────────────────────────────────────────────────
function connectSse() {
  if (eventSource) return
  sseStatus.value = 'connecting'
  // /api/realtime/stream 经 Vite 代理转发至 Java 后端 8081
  eventSource = new EventSource('/api/realtime/stream')

  eventSource.addEventListener('connected', () => {
    sseStatus.value = 'connected'
    ElMessage.success('已连接到实时心率推送服务')
  })

  eventSource.addEventListener('heartrate', (e) => {
    try {
      const data = JSON.parse(e.data)
      handleRealtimeData(data)
    } catch (_) { /* ignore parse error */ }
  })

  eventSource.onerror = () => {
    sseStatus.value = 'disconnected'
    eventSource.close()
    eventSource = null
    // 3 秒后自动重连
    setTimeout(() => {
      if (sseStatus.value === 'disconnected') connectSse()
    }, 3000)
  }
}

function disconnectSse() {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  sseStatus.value = 'disconnected'
}

function toggleSse() {
  if (sseStatus.value === 'connected') {
    disconnectSse()
  } else {
    connectSse()
  }
}

// ─── 处理收到的实时心率数据 ──────────────────────────────────
function handleRealtimeData(data) {
  const uid = String(data.userId ?? 'unknown')
  const hr = data.heartRate != null ? Number(data.heartRate) : null
  const isAbnormal = !!data.isAbnormal
  const dataTime = data.dataTime
    ? new Date(data.dataTime).toLocaleTimeString('zh-CN')
    : new Date().toLocaleTimeString('zh-CN')

  if (!userCards[uid]) {
    userCards[uid] = { heartRate: hr, dataTime, isAbnormal, anomalyType: data.anomalyType, history: [] }
  } else {
    userCards[uid].heartRate = hr
    userCards[uid].dataTime = dataTime
    userCards[uid].isAbnormal = isAbnormal
    userCards[uid].anomalyType = data.anomalyType
  }

  if (hr !== null) {
    userCards[uid].history.push(hr)
    if (userCards[uid].history.length > 60) userCards[uid].history.shift()
  }

  totalReceived.value++

  if (isAbnormal) {
    alerts.value.push({ userId: uid, heartRate: hr, dataTime, anomalyType: data.anomalyType })
    if (alerts.value.length > 100) alerts.value.shift()
  }
}

// ─── Python MQTT 监测服务控制（通过 /python 代理） ────────────
async function checkMqttStatus() {
  try {
    const res = await fetch('/python/api/monitor/status')
    const json = await res.json()
    mqttStatus.value = json?.data?.status === 'running' ? 'running' : 'stopped'
  } catch (_) {
    mqttStatus.value = 'stopped'
  }
}

async function startMqttMonitor() {
  startingMqtt.value = true
  try {
    const res = await fetch('/python/api/monitor/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ broker: DEFAULT_MQTT_BROKER, port: DEFAULT_MQTT_PORT, topics: DEFAULT_MQTT_TOPICS })
    })
    const json = await res.json()
    if (json.success) {
      ElMessage.success('MQTT 监测已启动')
      mqttStatus.value = 'running'
    } else {
      ElMessage.warning(json.message || '启动失败')
    }
  } catch (_) {
    ElMessage.error('无法连接到 Python REST API（请先运行 python main.py → 选项 7）')
  } finally {
    startingMqtt.value = false
  }
}

async function stopMqttMonitor() {
  try {
    await fetch('/python/api/monitor/stop', { method: 'POST' })
    mqttStatus.value = 'stopped'
    ElMessage.info('MQTT 监测已停止')
  } catch (_) {
    ElMessage.error('停止失败')
  }
}

// ─── 工具函数 ────────────────────────────────────────────────
function trendBarHeight(v) {
  const clamped = Math.min(Math.max(v, HR_EXTREME_LOW), HR_EXTREME_HIGH)
  return Math.round(((clamped - HR_EXTREME_LOW) / (HR_EXTREME_HIGH - HR_EXTREME_LOW)) * 36) + 4
}

function trendBarColor(v) {
  if (v >= HR_EXTREME_HIGH || v <= HR_EXTREME_LOW) return '#f56c6c'
  if (v > HR_HIGH || v < HR_LOW) return '#e6a23c'
  return '#67c23a'
}

function clearData() {
  Object.keys(userCards).forEach(k => delete userCards[k])
  totalReceived.value = 0
}

function clearAlerts() {
  alerts.value = []
}

// ─── 生命周期 ────────────────────────────────────────────────
let statusTimer = null

onMounted(() => {
  connectSse()
  checkMqttStatus()
  statusTimer = setInterval(checkMqttStatus, 10000)
})

onUnmounted(() => {
  disconnectSse()
  if (statusTimer) clearInterval(statusTimer)
})
</script>

<style scoped>
.realtime-container { display: flex; flex-direction: column; gap: 16px; }

.control-card :deep(.el-card__body) { padding: 12px 20px; }
.control-row { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.status-section { display: flex; align-items: center; gap: 10px; }
.action-section { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.status-label, .mqtt-label { font-size: 13px; color: #606266; }
.clients-tip { font-size: 12px; color: #909399; }

.main-content { display: flex; gap: 16px; align-items: flex-start; }
.cards-section { flex: 1; min-width: 0; }
.alerts-section { width: 300px; flex-shrink: 0; }
.section-card { height: 100%; }

.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 15px; font-weight: 600; color: #303133; }

.empty-hint { padding: 30px 0; }

.user-cards { display: flex; flex-wrap: wrap; gap: 12px; }

.user-card {
  border-radius: 8px;
  padding: 14px 16px;
  min-width: 140px;
  border: 2px solid transparent;
  transition: border-color 0.3s, box-shadow 0.3s;
  cursor: default;
}
.card-normal { background: #f0f9eb; border-color: #b3e19d; }
.card-abnormal { background: #fef0f0; border-color: #fbc4c4; animation: pulse 1.2s ease-in-out infinite; }

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245,108,108,0); }
  50% { box-shadow: 0 0 8px 3px rgba(245,108,108,0.4); }
}

.card-uid { font-size: 12px; color: #909399; margin-bottom: 4px; }
.card-rate { font-size: 36px; font-weight: 700; line-height: 1; margin-bottom: 2px; }
.rate-ok { color: #67c23a; }
.rate-danger { color: #f56c6c; }
.rate-unit { font-size: 14px; font-weight: 400; margin-left: 2px; }
.card-time { font-size: 11px; color: #c0c4cc; margin-bottom: 6px; }
.card-status { margin-bottom: 8px; }

.mini-trend { display: flex; align-items: flex-end; gap: 2px; height: 40px; overflow: hidden; }
.trend-bar { display: inline-block; width: 5px; border-radius: 2px 2px 0 0; transition: height 0.3s; }

.alert-item { padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.alert-item:last-child { border-bottom: none; }
.alert-top { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.alert-uid { font-size: 13px; font-weight: 600; }
.alert-time { font-size: 11px; color: #909399; margin-left: auto; }
.alert-body { display: flex; align-items: center; gap: 8px; }
.alert-rate { font-size: 16px; }
.alert-type { font-size: 12px; color: #f56c6c; }
</style>
