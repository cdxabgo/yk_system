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
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { TrendCharts, Refresh } from '@element-plus/icons-vue'
import { heartRateApi } from '../api/index'

const router = useRouter()

// ─── Constants ────────────────────────────────────────────
const POLL_INTERVAL_MS          = 10000   // DB poll every 10 s
const STATUS_UPDATE_INTERVAL_MS = 30000   // Local status re-evaluation every 30 s
const DEVICE_ONLINE_THRESHOLD_MS = 5 * 60 * 1000   // 5 min → device considered offline
const GRAY_THRESHOLD_MS          = 10 * 60 * 1000  // 10 min → gray card
const RED_STREAK_THRESHOLD_MS    = 5 * 60 * 1000   // 5 min → continuous anomaly (red)

// ─── State ────────────────────────────────────────────────
const loading = ref(false)
const cards   = ref([])   // EmployeeMonitorVO[]

let pollTimer  = null
let clockTimer = null

// ─── Data loading ─────────────────────────────────────────
async function loadData() {
  loading.value = true
  try {
    const res = await heartRateApi.monitor({ page: 1, size: 100 })
    cards.value = res.data.list
  } finally {
    loading.value = false
  }
}

// ─── Status helpers ───────────────────────────────────────
function parseTs(str) {
  if (!str) return null
  const d = new Date(String(str).replace(' ', 'T'))
  return isNaN(d.getTime()) ? null : d.getTime()
}

function lastMs(c) {
  return parseTs(c.latestCollectTime)
}

function latestHr(c) {
  return c.latestHeartRate
}

function latestAbnormal(c) {
  return c.latestIsAbnormal === 1
}

function getStatus(c) {
  const now  = Date.now()
  const last = lastMs(c)
  if (!last || now - last > GRAY_THRESHOLD_MS) return 'gray'
  if (!latestAbnormal(c)) return 'cyan'
  const streakStart = parseTs(c.streakStartTime)
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
  // Poll DB every 10 s for fresh data
  pollTimer  = setInterval(loadData, POLL_INTERVAL_MS)
  // Trigger reactivity for timed status transitions (gray / red) every 30 s
  clockTimer = setInterval(() => { cards.value = [...cards.value] }, STATUS_UPDATE_INTERVAL_MS)
})

onUnmounted(() => {
  if (pollTimer)  clearInterval(pollTimer)
  if (clockTimer) clearInterval(clockTimer)
})
</script>

<style scoped>
.dashboard-page { display: flex; flex-direction: column; gap: 18px; }

/* ── Control bar ─────────────────────────────────────── */
.ctrl-bar :deep(.el-card__body) { padding: 14px 22px; }
.bar-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.bar-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--yk-text);
  display: flex;
  align-items: center;
  font-family: var(--yk-font-display);
  letter-spacing: 1px;
}
.bar-right  { display: flex; align-items: center; gap: 10px; }
.legend     { display: flex; gap: 20px; flex-wrap: wrap; }
.leg        { font-size: 12px; font-weight: 600; letter-spacing: 0.8px; }
.leg-cyan   { color: var(--yk-accent); }
.leg-yellow { color: var(--yk-warning); }
.leg-red    { color: var(--yk-danger); }
.leg-gray   { color: var(--yk-muted); }

/* ── Card grid ───────────────────────────────────────── */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(168px, 1fr));
  gap: 14px;
}

/* ── Employee card ───────────────────────────────────── */
.emp-card {
  position: relative;
  border-radius: 14px;
  border: 1px solid var(--yk-border);
  padding: 14px 16px 12px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  background: rgba(11, 18, 26, 0.72);
  min-height: 156px;
  user-select: none;
  box-shadow: inset 0 0 0 1px rgba(93, 227, 255, 0.05);
}
.emp-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 22px rgba(3, 8, 15, 0.45);
  border-color: rgba(93, 227, 255, 0.4);
}

/* Status colour variants */
.card-cyan {
  background: linear-gradient(145deg, rgba(12, 26, 34, 0.9), rgba(7, 16, 24, 0.65));
  border-color: rgba(93, 227, 255, 0.5);
}
.card-yellow {
  background: linear-gradient(145deg, rgba(36, 27, 12, 0.92), rgba(20, 14, 8, 0.75));
  border-color: rgba(255, 179, 71, 0.45);
}
.card-red {
  background: linear-gradient(145deg, rgba(40, 13, 18, 0.95), rgba(24, 9, 12, 0.75));
  border-color: rgba(255, 107, 107, 0.65);
  animation: pulse-red 1.6s ease-in-out infinite;
}
.card-gray {
  background: linear-gradient(145deg, rgba(20, 24, 30, 0.9), rgba(12, 15, 20, 0.75));
  border-color: rgba(159, 178, 200, 0.35);
}

@keyframes pulse-red {
  0%,100% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0); }
  50%      { box-shadow: 0 0 12px 4px rgba(255, 107, 107, 0.35); }
}

/* Device label – top-right corner */
.dev-tag { position: absolute; top: 10px; right: 10px; }

.emp-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--yk-text);
  margin-top: 6px;
  margin-bottom: 2px;
  padding-right: 52px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.emp-job  {
  font-size: 12px;
  color: var(--yk-muted);
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.emp-bpm  { font-size: 32px; font-weight: 700; line-height: 1.1; margin-bottom: 4px; }
.bpm-normal { color: var(--yk-accent); }
.bpm-danger { color: var(--yk-danger); }
.bpm-none   { color: var(--yk-muted); }
.bpm-unit   { font-size: 12px; font-weight: 400; margin-left: 2px; }
.emp-stag   { margin-bottom: 6px; }
.emp-time   { font-size: 11px; color: var(--yk-muted); }
</style>
