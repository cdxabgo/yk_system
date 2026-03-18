<template>
  <div class="realtime-container">
    <!-- 状态栏 -->
    <el-card class="guide-card">
      <div class="guide-steps">
        <div :class="['guide-step', polling ? 'step-done' : 'step-pending']">
          <div class="step-badge">🔄</div>
          <div class="step-body">
            <div class="step-title">数据库轮询监测</div>
            <div class="step-desc">每 10 秒从数据库获取各职工最新心率，模拟实时监测效果</div>
          </div>
          <el-tag
            :type="polling ? 'success' : 'info'"
            size="small"
            class="step-tag"
          >
            {{ polling ? '▶ 轮询中' : '■ 已停止' }}
          </el-tag>
          <el-button
            :type="polling ? 'danger' : 'primary'"
            size="small"
            @click="togglePolling"
          >
            {{ polling ? '停止' : '启动' }}
          </el-button>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="stats-row" v-if="polling || totalPolls > 0">
        <span class="clients-tip">
          🗄️ 已轮询 {{ totalPolls }} 次 &nbsp;|&nbsp;
          最后更新: {{ lastPollTime || '—' }}
          &nbsp;|&nbsp; 共 {{ Object.keys(userCards).length }} 位职工
        </span>
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
              <el-button :icon="RefreshRight" size="small" @click="clearData">清空</el-button>
            </div>
          </template>

          <div v-if="Object.keys(userCards).length === 0" class="empty-hint">
            <el-empty description="暂无数据，请点击「启动」开始轮询" />
          </div>

          <div v-else class="user-cards">
            <div
              v-for="(card, uid) in userCards"
              :key="uid"
              :class="['user-card', card.isAbnormal ? 'card-abnormal' : 'card-normal']"
            >
              <div class="card-uid">{{ card.employeeName || ('用户 ' + uid) }}</div>
              <div class="card-rate" :class="card.isAbnormal ? 'rate-danger' : 'rate-ok'">
                {{ card.heartRate !== null ? card.heartRate : '--' }}
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
              <el-button :icon="Delete" size="small" @click="clearAlerts">清空</el-button>
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
                <span class="alert-uid">{{ alert.employeeName || ('用户 ' + alert.userId) }}</span>
                <span class="alert-time">{{ alert.dataTime }}</span>
              </div>
              <div class="alert-body">
                <span class="alert-rate" style="color:#f56c6c;font-weight:bold">
                  {{ alert.heartRate !== null ? alert.heartRate : '--' }} bpm
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
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Odometer, Warning, RefreshRight, Delete } from '@element-plus/icons-vue'
import { heartRateApi } from '../api/index'

// ─── 心率阈值常量 ────────────────────────────────────────────
const HR_EXTREME_HIGH = 200
const HR_EXTREME_LOW  = 30
const HR_HIGH         = 150
const HR_LOW          = 60

// ─── 轮询状态 ────────────────────────────────────────────────
const polling     = ref(false)
const totalPolls  = ref(0)
const lastPollTime = ref('')

// ─── 实时数据 ────────────────────────────────────────────────
// userCards: { [userId]: { heartRate, dataTime, isAbnormal, anomalyType, employeeName, history[] } }
const userCards = reactive({})
const alerts    = ref([])

let pollTimer = null

// ─── 日期解析工具 ─────────────────────────────────────────────
function parseDataTime(str) {
  if (!str) return new Date()
  const isoStr = String(str).replace(' ', 'T')
  const d = new Date(isoStr)
  return isNaN(d.getTime()) ? new Date() : d
}

// ─── 处理轮询结果 ────────────────────────────────────────────
function handleLatestData(list) {
  if (!Array.isArray(list)) return

  list.forEach(data => {
    const uid = String(data.userId ?? 'unknown')
    const hr  = data.heartRate != null ? Number(data.heartRate) : null
    const isAbnormal  = !!data.isAbnormal
    const dataTime    = parseDataTime(data.dataTime).toLocaleTimeString('zh-CN')
    const employeeName = data.employeeName || ''

    if (!userCards[uid]) {
      userCards[uid] = { heartRate: hr, dataTime, isAbnormal, anomalyType: data.anomalyType, employeeName, history: [] }
    } else {
      userCards[uid].heartRate   = hr
      userCards[uid].dataTime    = dataTime
      userCards[uid].isAbnormal  = isAbnormal
      userCards[uid].anomalyType = data.anomalyType
      userCards[uid].employeeName = employeeName
    }

    if (hr !== null) {
      userCards[uid].history.push(hr)
      if (userCards[uid].history.length > 60) userCards[uid].history.shift()
    }

    if (isAbnormal) {
      // 仅当本次轮询发现新异常（与上条告警的职工+采集时间不同）时才记录
      const rawTime = String(data.dataTime ?? '')
      const last = alerts.value[alerts.value.length - 1]
      const isDuplicate = last && String(last.userId) === uid && last.rawTime === rawTime
      if (!isDuplicate) {
        alerts.value.push({ userId: uid, heartRate: hr, dataTime, rawTime, anomalyType: data.anomalyType, employeeName })
        if (alerts.value.length > 100) alerts.value.shift()
      }
    }
  })

  totalPolls.value++
  lastPollTime.value = new Date().toLocaleTimeString('zh-CN')
}

// ─── 轮询控制 ────────────────────────────────────────────────
async function poll() {
  try {
    const res = await heartRateApi.latest()
    if (res.data) {
      handleLatestData(res.data)
    }
  } catch (_) {
    // 网络错误时静默跳过，不中断轮询
  }
}

function startPolling() {
  if (polling.value) return
  polling.value = true
  poll() // 立即执行一次
  pollTimer = setInterval(poll, 10000)
  ElMessage.success('已启动数据库轮询监测（每10秒）')
}

function stopPolling() {
  polling.value = false
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  ElMessage.info('轮询已停止')
}

function togglePolling() {
  if (polling.value) {
    stopPolling()
  } else {
    startPolling()
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
  totalPolls.value  = 0
  lastPollTime.value = ''
}

function clearAlerts() {
  alerts.value = []
}

// ─── 生命周期 ────────────────────────────────────────────────
onMounted(() => {
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.realtime-container { display: flex; flex-direction: column; gap: 16px; }

/* ── 状态卡 ─────────────────────────────────────── */
.guide-card :deep(.el-card__body) { padding: 14px 20px; }

.guide-steps {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.guide-step {
  flex: 1;
  min-width: 260px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 2px solid #e4e7ed;
  background: #fafafa;
  transition: border-color 0.3s, background 0.3s;
}
.step-done    { border-color: #67c23a; background: #f0f9eb; }
.step-pending { border-color: #409eff; background: #ecf5ff; }

.step-badge {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.step-done .step-badge { background: #67c23a; }

.step-body { flex: 1; }
.step-title { font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 2px; }
.step-desc  { font-size: 12px; color: #606266; }
.step-tag   { flex-shrink: 0; }

.stats-row { margin-top: 10px; border-top: 1px solid #f0f0f0; padding-top: 8px; }
.clients-tip { font-size: 12px; color: #909399; }

/* ── 数据区 ──────────────────────────────────────────── */
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
.card-normal   { background: #f0f9eb; border-color: #b3e19d; }
.card-abnormal { background: #fef0f0; border-color: #fbc4c4; animation: pulse 1.2s ease-in-out infinite; }

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245,108,108,0); }
  50%       { box-shadow: 0 0 8px 3px rgba(245,108,108,0.4); }
}

.card-uid  { font-size: 12px; color: #909399; margin-bottom: 4px; font-weight: 600; }
.card-rate { font-size: 36px; font-weight: 700; line-height: 1; margin-bottom: 2px; }
.rate-ok     { color: #67c23a; }
.rate-danger { color: #f56c6c; }
.rate-unit { font-size: 14px; font-weight: 400; margin-left: 2px; }
.card-time   { font-size: 11px; color: #c0c4cc; margin-bottom: 6px; }
.card-status { margin-bottom: 8px; }

.mini-trend { display: flex; align-items: flex-end; gap: 2px; height: 40px; overflow: hidden; }
.trend-bar  { display: inline-block; width: 5px; border-radius: 2px 2px 0 0; transition: height 0.3s; }

.alert-item { padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.alert-item:last-child { border-bottom: none; }
.alert-top  { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.alert-uid  { font-size: 13px; font-weight: 600; }
.alert-time { font-size: 11px; color: #909399; margin-left: auto; }
.alert-body { display: flex; align-items: center; gap: 8px; }
.alert-rate { font-size: 16px; }
.alert-type { font-size: 12px; color: #f56c6c; }
</style>
