<template>
  <div class="dashboard-page">
    <!-- Control bar -->
    <el-card class="ctrl-bar" shadow="never">
      <div class="bar-row">
        <span class="bar-title">
          <el-icon style="vertical-align:middle;margin-right:8px"><TrendCharts /></el-icon>
          班中监控看板
        </span>
        <div class="bar-right">
          <el-tag :type="sseOk ? 'success' : 'info'" size="small">
            {{ sseOk ? '📡 实时已连' : '📡 未连接' }}
          </el-tag>
          <el-tag size="small" type="info">共 {{ cards.length }} 人</el-tag>
          <el-button size="small" :icon="Refresh" @click="loadData" :loading="loading">刷新</el-button>
        </div>
      </div>
      <div class="legend">
        <span class="leg leg-cyan">■ 心率正常</span>
        <span class="leg leg-yellow">■ 单次异常</span>
        <span class="leg leg-red">■ 持续异常(&gt;5min)</span>
        <span class="leg leg-gray">■ 10分钟无数据</span>
      </div>
    </el-card>

    <!-- Employee card grid -->
    <div class="card-grid" v-loading="loading">
      <div v-if="!loading && cards.length === 0" style="grid-column:1/-1">
        <el-empty description="暂无员工数据" />
      </div>
      <div
        v-for="c in cards"
        :key="c.employeeId"
        :class="['emp-card', cardClass(c)]"
        @click="go(c.employeeId)"
        role="button"
        :title="`点击查看 ${c.name} 的详情`"
      >
        <!-- Device online/offline label -->
        <el-tag
          :type="isOnline(c) ? 'success' : 'danger'"
          size="small"
          effect="dark"
          class="dev-tag"
        >{{ isOnline(c) ? '● 在线' : '○ 离线' }}</el-tag>

        <div class="emp-name">{{ c.name }}</div>
        <div class="emp-job">{{ c.job || '—' }}</div>

        <div class="emp-bpm" :class="bpmColorClass(c)">
          {{ latestHr(c) !== null ? latestHr(c) : '--' }}<span class="bpm-unit">bpm</span>
        </div>

        <div class="emp-stag">
          <el-tag :type="statusTag(c).type" size="small" effect="light">{{ statusTag(c).label }}</el-tag>
        </div>

        <div class="emp-time">{{ lastTimeStr(c) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { TrendCharts, Refresh } from '@element-plus/icons-vue'
import { heartRateApi } from '../api/index'

const router = useRouter()

// ─── Constants ────────────────────────────────────────────
const REFRESH_INTERVAL_MS     = 60000   // Full data refresh from server
const STATUS_UPDATE_INTERVAL_MS = 30000  // Local status re-evaluation (gray/red transitions)
const SSE_RECONNECT_DELAY_MS  = 3000    // Delay before SSE reconnect attempt
const DEVICE_ONLINE_THRESHOLD_MS = 5 * 60 * 1000   // 5 min → device considered offline
const GRAY_THRESHOLD_MS         = 10 * 60 * 1000   // 10 min → gray card
const RED_STREAK_THRESHOLD_MS   = 5 * 60 * 1000    // 5 min → continuous anomaly (red)

// ─── State ────────────────────────────────────────────────
const loading = ref(false)
const cards   = ref([])   // EmployeeMonitorVO[]
const sseOk   = ref(false)

/**
 * SSE real-time overlay keyed by String(employeeId).
 * { hr, isAbnormal, lastSseMs, streakStartMs }
 */
const sseOverlay = reactive({})

let eventSource   = null
let refreshTimer  = null
let clockTimer    = null

// ─── Data loading ─────────────────────────────────────────
async function loadData() {
  loading.value = true
  try {
    const res = await heartRateApi.monitor({ page: 1, size: 100 })
    cards.value = res.data.list

    // Seed sseOverlay with backend streak info on first load
    cards.value.forEach(c => {
      const id = String(c.employeeId)
      if (!sseOverlay[id]) {
        sseOverlay[id] = {
          hr: null,
          isAbnormal: null,
          lastSseMs: null,
          streakStartMs: c.streakStartTime ? parseTs(c.streakStartTime) : null
        }
      }
    })
  } finally {
    loading.value = false
  }
}

// ─── SSE connection ───────────────────────────────────────
function connectSse() {
  if (eventSource) return
  eventSource = new EventSource('/api/realtime/stream')

  eventSource.addEventListener('connected', () => { sseOk.value = true })

  eventSource.addEventListener('heartrate', (e) => {
    try { applySSE(JSON.parse(e.data)) } catch (_) {}
  })

  eventSource.onerror = () => {
    sseOk.value = false
    eventSource.close()
    eventSource = null
    setTimeout(connectSse, SSE_RECONNECT_DELAY_MS)
  }
}

function disconnectSse() {
  if (eventSource) { eventSource.close(); eventSource = null }
  sseOk.value = false
}

function applySSE(data) {
  const uid = String(data.userId ?? '')
  if (!uid) return
  const now = Date.now()
  const isAbnormal = !!data.isAbnormal

  if (!sseOverlay[uid]) {
    sseOverlay[uid] = { hr: null, isAbnormal: null, lastSseMs: null, streakStartMs: null }
  }
  const ov = sseOverlay[uid]
  ov.hr = data.heartRate != null ? Number(data.heartRate) : null
  ov.isAbnormal = isAbnormal
  ov.lastSseMs  = now

  if (isAbnormal) {
    if (!ov.streakStartMs) ov.streakStartMs = now
  } else {
    ov.streakStartMs = null
  }
}

// ─── Status helpers ───────────────────────────────────────
function parseTs(str) {
  if (!str) return null
  const d = new Date(String(str).replace(' ', 'T'))
  return isNaN(d.getTime()) ? null : d.getTime()
}

function latestHr(c) {
  const ov = sseOverlay[String(c.employeeId)]
  return (ov?.hr !== null && ov?.hr !== undefined) ? ov.hr : c.latestHeartRate
}

function lastMs(c) {
  const ov = sseOverlay[String(c.employeeId)]
  return ov?.lastSseMs ?? parseTs(c.latestCollectTime)
}

function latestAbnormal(c) {
  const ov = sseOverlay[String(c.employeeId)]
  return (ov?.isAbnormal !== null && ov?.isAbnormal !== undefined)
    ? ov.isAbnormal
    : c.latestIsAbnormal === 1
}

function getStatus(c) {
  const now = Date.now()
  const last = lastMs(c)
  if (!last || now - last > GRAY_THRESHOLD_MS) return 'gray'
  if (!latestAbnormal(c)) return 'cyan'
  const ov = sseOverlay[String(c.employeeId)]
  const streakStart = ov?.streakStartMs ?? parseTs(c.streakStartTime)
  if (streakStart && now - streakStart >= RED_STREAK_THRESHOLD_MS) return 'red'
  return 'yellow'
}

function cardClass(c) { return 'card-' + getStatus(c) }

function bpmColorClass(c) {
  const s = getStatus(c)
  if (s === 'cyan')   return 'bpm-normal'
  if (s === 'yellow' || s === 'red') return 'bpm-danger'
  return 'bpm-none'
}

const STATUS_TAG_MAP = {
  cyan:   { type: 'success', label: '✓ 正常' },
  yellow: { type: 'warning', label: '⚠ 单次异常' },
  red:    { type: 'danger',  label: '🔴 持续异常' },
  gray:   { type: 'info',    label: '— 无数据' }
}
function statusTag(c) { return STATUS_TAG_MAP[getStatus(c)] }

function isOnline(c) {
  const last = lastMs(c)
  return !!(last && Date.now() - last < DEVICE_ONLINE_THRESHOLD_MS)
}

function lastTimeStr(c) {
  const last = lastMs(c)
  if (!last) return '暂无数据'
  return new Date(last).toLocaleTimeString('zh-CN')
}

function go(employeeId) {
  router.push(`/employee-detail/${employeeId}`)
}

// ─── Lifecycle ────────────────────────────────────────────
onMounted(() => {
  loadData()
  connectSse()
  // Full data refresh every 60 s (fallback)
  refreshTimer = setInterval(loadData, REFRESH_INTERVAL_MS)
  // Trigger reactivity for timed status transitions (gray / red) every 30 s
  clockTimer = setInterval(() => { cards.value = [...cards.value] }, STATUS_UPDATE_INTERVAL_MS)
})

onUnmounted(() => {
  disconnectSse()
  if (refreshTimer) clearInterval(refreshTimer)
  if (clockTimer)   clearInterval(clockTimer)
})
</script>

<style scoped>
.dashboard-page { display: flex; flex-direction: column; gap: 16px; }

/* ── Control bar ─────────────────────────────────────── */
.ctrl-bar :deep(.el-card__body) { padding: 12px 20px; }
.bar-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.bar-title { font-size: 18px; font-weight: 700; color: #303133; display: flex; align-items: center; }
.bar-right  { display: flex; align-items: center; gap: 8px; }
.legend     { display: flex; gap: 20px; flex-wrap: wrap; }
.leg        { font-size: 13px; font-weight: 600; }
.leg-cyan   { color: #00bcd4; }
.leg-yellow { color: #e6a23c; }
.leg-red    { color: #f56c6c; }
.leg-gray   { color: #909399; }

/* ── Card grid ───────────────────────────────────────── */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(156px, 1fr));
  gap: 12px;
}

/* ── Employee card ───────────────────────────────────── */
.emp-card {
  position: relative;
  border-radius: 10px;
  border: 2px solid #e4e7ed;
  padding: 12px 14px 10px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  background: #fff;
  min-height: 148px;
  user-select: none;
}
.emp-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.13);
}

/* Status colour variants */
.card-cyan   { background: #e0f7fa; border-color: #00bcd4; }
.card-yellow { background: #fff8e1; border-color: #e6a23c; }
.card-red    { background: #fef0f0; border-color: #f56c6c; animation: pulse-red 1.5s ease-in-out infinite; }
.card-gray   { background: #f5f7fa; border-color: #c0c4cc; }

@keyframes pulse-red {
  0%,100% { box-shadow: 0 0 0 0 rgba(245,108,108,0); }
  50%      { box-shadow: 0 0 10px 4px rgba(245,108,108,0.35); }
}

/* Device label – top-right corner */
.dev-tag { position: absolute; top: 8px; right: 8px; }

.emp-name { font-size: 15px; font-weight: 700; color: #303133; margin-top: 4px; margin-bottom: 2px; padding-right: 52px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.emp-job  { font-size: 12px; color: #606266; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.emp-bpm  { font-size: 32px; font-weight: 700; line-height: 1.1; margin-bottom: 4px; }
.bpm-normal { color: #00bcd4; }
.bpm-danger { color: #f56c6c; }
.bpm-none   { color: #c0c4cc; }
.bpm-unit   { font-size: 13px; font-weight: 400; margin-left: 2px; }
.emp-stag   { margin-bottom: 4px; }
.emp-time   { font-size: 11px; color: #909399; }
</style>
