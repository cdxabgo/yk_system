<template>
  <div class="realtime-container">
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

      <div class="stats-row" v-if="polling || totalPolls > 0">
        <span class="clients-tip">
          🗄️ 已轮询 {{ totalPolls }} 次 &nbsp;|&nbsp;
          最后更新: {{ lastPollTime || '—' }}
          &nbsp;|&nbsp; 共 {{ Object.keys(userCards).length }} 位职工
        </span>
      </div>
    </el-card>

    <div class="main-content">
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
                <span class="alert-rate">{{ alert.heartRate !== null ? alert.heartRate : '--' }} bpm</span>
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

const HR_EXTREME_HIGH = 200
const HR_EXTREME_LOW  = 30
const HR_HIGH         = 150
const HR_LOW          = 60

const polling     = ref(false)
const totalPolls  = ref(0)
const lastPollTime = ref('')

const userCards = reactive({})
const alerts    = ref([])

let pollTimer = null

function parseDataTime(str) {
  if (!str) return new Date()
  const isoStr = String(str).replace(' ', 'T')
  const d = new Date(isoStr)
  return isNaN(d.getTime()) ? new Date() : d
}

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

async function poll() {
  try {
    const res = await heartRateApi.latest()
    if (res.data) {
      handleLatestData(res.data)
    }
  } catch (_) {
    // 网络错误时静默跳过
  }
}

function startPolling() {
  if (polling.value) return
  polling.value = true
  poll()
  pollTimer = setInterval(poll, 10000)
  ElMessage.success('已启动数据库轮询监测（每10秒）')
}

function stopPolling() {
  polling.value = false
  clearPollTimer()
  ElMessage.info('轮询已停止')
}

function clearPollTimer() {
  if (!pollTimer) return
  clearInterval(pollTimer)
  pollTimer = null
}

function togglePolling() {
  if (polling.value) {
    stopPolling()
  } else {
    startPolling()
  }
}

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

onMounted(() => {
  startPolling()
})

onUnmounted(() => {
  clearPollTimer()
})
</script>

<style scoped>
.realtime-container { display: flex; flex-direction: column; gap: 16px; }

.guide-card :deep(.el-card__body) { padding: 16px 20px; }

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
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid var(--yk-border-light);
  background: #fafbfc;
  transition: border-color 0.3s, background 0.3s;
}
.step-done    { border-color: #c8e6c9; background: #f1f8f4; }
.step-pending { border-color: #a0cfff; background: #f0f7ff; }

.step-badge {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #ecf5ff;
  color: #409EFF;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid #a0cfff;
}
.step-done .step-badge {
  background: #e8f5e9;
  color: #67c23a;
  border-color: #c8e6c9;
}

.step-body { flex: 1; }
.step-title { font-size: 14px; font-weight: 600; color: var(--yk-text-primary); margin-bottom: 2px; }
.step-desc  { font-size: 12px; color: var(--yk-text-muted); }
.step-tag   { flex-shrink: 0; }

.stats-row { margin-top: 12px; border-top: 1px solid var(--yk-border-light); padding-top: 10px; }
.clients-tip { font-size: 12px; color: var(--yk-text-muted); }

.main-content { display: flex; gap: 16px; align-items: flex-start; }
.cards-section { flex: 1; min-width: 0; }
.alerts-section { width: 320px; flex-shrink: 0; }
.section-card { height: 100%; }

.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--yk-text-primary);
}

.empty-hint { padding: 30px 0; }

.user-cards { display: flex; flex-wrap: wrap; gap: 12px; }

.user-card {
  border-radius: 12px;
  padding: 16px 18px;
  min-width: 150px;
  border: 1px solid transparent;
  transition: border-color 0.3s, box-shadow 0.3s;
  cursor: default;
  background: #fafbfc;
}
.card-normal   { border-color: #c8e6c9; }
.card-abnormal {
  border-color: #fca5a5;
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0); }
  50%       { box-shadow: 0 0 10px 3px rgba(245, 108, 108, 0.2); }
}

.card-uid  { font-size: 12px; color: var(--yk-text-muted); margin-bottom: 6px; font-weight: 600; }
.card-rate { font-size: 34px; font-weight: 700; line-height: 1; margin-bottom: 4px; }
.rate-ok     { color: #67c23a; }
.rate-danger { color: #f56c6c; }
.rate-unit { font-size: 13px; font-weight: 400; margin-left: 2px; }
.card-time   { font-size: 11px; color: var(--yk-text-muted); margin-bottom: 8px; }
.card-status { margin-bottom: 8px; }

.mini-trend { display: flex; align-items: flex-end; gap: 2px; height: 40px; overflow: hidden; }
.trend-bar  { display: inline-block; width: 5px; border-radius: 2px 2px 0 0; transition: height 0.3s; }

.alert-item { padding: 10px 0; border-bottom: 1px solid var(--yk-border-light); }
.alert-item:last-child { border-bottom: none; }
.alert-top  { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.alert-uid  { font-size: 13px; font-weight: 600; color: var(--yk-text-primary); }
.alert-time { font-size: 11px; color: var(--yk-text-muted); margin-left: auto; }
.alert-body { display: flex; align-items: center; gap: 8px; }
.alert-rate { font-size: 16px; color: #f56c6c; font-weight: 700; }
.alert-type { font-size: 12px; color: var(--yk-warning); }

@media (max-width: 980px) {
  .main-content { flex-direction: column; }
  .alerts-section { width: 100%; }
}
</style>
