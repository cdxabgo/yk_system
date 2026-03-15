<template>
  <div class="detail-page">
    <!-- Top bar -->
    <div class="top-bar">
      <el-button :icon="ArrowLeft" plain @click="router.push('/dashboard')">返回看板</el-button>
      <span class="page-title">职工详情 — {{ empInfo?.name || `#${employeeId}` }}</span>
      <el-tag :type="sseOk ? 'success' : 'info'" size="small">
        {{ sseOk ? '📡 实时已连' : '📡 未连接' }}
      </el-tag>
    </div>

    <div class="detail-layout">
      <!-- ── Left panel: basic info + real-time chart ── -->
      <div class="left-panel">
        <!-- Basic info card -->
        <el-card class="info-card">
          <template #header>
            <div class="card-hd">
              <el-icon><User /></el-icon>
              <span class="hd-text">基本信息</span>
              <el-tag :type="currentStatusTag.type" effect="dark" class="ml-auto">
                {{ currentStatusTag.label }}
              </el-tag>
            </div>
          </template>
          <el-descriptions :column="2" border size="small" v-loading="empLoading">
            <el-descriptions-item label="姓名">{{ empInfo?.name || '—' }}</el-descriptions-item>
            <el-descriptions-item label="年龄">{{ empInfo?.age ?? '—' }}</el-descriptions-item>
            <el-descriptions-item label="岗位">{{ empInfo?.job || '—' }}</el-descriptions-item>
            <el-descriptions-item label="工龄">
              {{ empInfo?.workingYears != null ? empInfo.workingYears + ' 年' : '—' }}
            </el-descriptions-item>
            <el-descriptions-item label="联系方式" :span="2">
              {{ empInfo?.contactInformation || '—' }}
            </el-descriptions-item>
            <el-descriptions-item label="当前心率">
              <span :class="isCurrentAbnormal ? 'rate-danger' : 'rate-ok'">
                {{ currentHr !== null ? currentHr + ' bpm' : '—' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="设备ID">{{ currentDeviceId || '—' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- Real-time heart rate chart -->
        <el-card class="chart-card">
          <template #header>
            <div class="card-hd">
              <el-icon><DataLine /></el-icon>
              <span class="hd-text">实时心率曲线</span>
              <span class="chart-count">已收 {{ hrHistory.length }} 条</span>
            </div>
          </template>

          <div v-if="hrHistory.length === 0" class="empty-chart">
            <el-empty description="等待实时数据推送…" :image-size="60" />
          </div>
          <div v-else class="chart-wrap">
            <svg
              viewBox="0 0 800 140"
              preserveAspectRatio="none"
              style="width:100%;height:140px;display:block;overflow:visible"
            >
              <!-- Normal zone background -->
              <rect
                x="0" :y="hrY(150)" width="800" :height="hrY(60) - hrY(150)"
                fill="rgba(103,194,58,0.08)"
              />
              <!-- Upper threshold line (150 bpm) -->
              <line
                x1="0" :y1="hrY(150)" x2="800" :y2="hrY(150)"
                stroke="#e6a23c" stroke-width="1" stroke-dasharray="6,4" opacity="0.8"
              />
              <!-- Lower threshold line (60 bpm) -->
              <line
                x1="0" :y1="hrY(60)" x2="800" :y2="hrY(60)"
                stroke="#e6a23c" stroke-width="1" stroke-dasharray="6,4" opacity="0.8"
              />
              <!-- HR polyline -->
              <polyline
                v-if="chartPoints"
                :points="chartPoints"
                fill="none"
                stroke="#409eff"
                stroke-width="2.5"
                stroke-linejoin="round"
                stroke-linecap="round"
              />
              <!-- Data dots -->
              <circle
                v-for="(pt, i) in visibleDots"
                :key="i"
                :cx="pt.x"
                :cy="pt.y"
                r="3.5"
                :fill="pt.abnormal ? '#f56c6c' : '#409eff'"
                opacity="0.85"
              />
              <!-- Latest value label -->
              <text
                v-if="visibleDots.length"
                :x="Math.min(visibleDots[visibleDots.length-1].x + 8, 770)"
                :y="visibleDots[visibleDots.length-1].y - 5"
                font-size="13"
                :fill="isCurrentAbnormal ? '#f56c6c' : '#409eff'"
                font-weight="bold"
              >{{ currentHr }}</text>
              <!-- Threshold labels -->
              <text x="4" :y="hrY(150) - 3" font-size="10" fill="#e6a23c" opacity="0.9">150</text>
              <text x="4" :y="hrY(60) - 3"  font-size="10" fill="#e6a23c" opacity="0.9">60</text>
            </svg>
          </div>
        </el-card>
      </div>

      <!-- ── Right panel: alarm history ── -->
      <div class="right-panel">
        <!-- Historical alarm records from database -->
        <el-card class="alarm-card">
          <template #header>
            <div class="card-hd">
              <el-icon style="color:#f56c6c"><Warning /></el-icon>
              <span class="hd-text">历史告警记录</span>
              <el-badge v-if="alarmTotal > 0" :value="alarmTotal" type="danger" class="ml-auto" />
            </div>
          </template>

          <el-table
            :data="alarmList"
            border
            size="small"
            v-loading="alarmLoading"
            max-height="340"
          >
            <el-table-column label="时间" min-width="148">
              <template #default="{ row }">{{ formatDt(row.collectTime) }}</template>
            </el-table-column>
            <el-table-column prop="heartRate" label="心率(bpm)" width="90" align="center">
              <template #default="{ row }">
                <span style="color:#f56c6c;font-weight:700">{{ row.heartRate }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="deviceId" label="设备" min-width="80" />
          </el-table>

          <div class="alarm-pag">
            <el-pagination
              v-model:current-page="alarmPage"
              :page-size="15"
              layout="total, prev, pager, next"
              :total="alarmTotal"
              @current-change="loadAlarms"
              small
            />
          </div>
        </el-card>

        <!-- Live SSE alarm feed -->
        <el-card class="live-card" v-if="liveAlerts.length > 0">
          <template #header>
            <div class="card-hd">
              <el-icon style="color:#f56c6c"><BellFilled /></el-icon>
              <span class="hd-text">实时告警</span>
              <el-badge :value="liveAlerts.length" type="danger" class="ml-auto" />
            </div>
          </template>
          <el-scrollbar max-height="180px">
            <div
              v-for="(a, i) in [...liveAlerts].reverse()"
              :key="i"
              class="live-item"
            >
              <el-tag type="danger" size="small">异常</el-tag>
              <span class="live-time">{{ a.time }}</span>
              <span class="live-rate">{{ a.hr }} bpm</span>
            </div>
          </el-scrollbar>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, User, DataLine, Warning, BellFilled } from '@element-plus/icons-vue'
import { heartRateApi, employeeApi } from '../api/index'

const route      = useRoute()
const router     = useRouter()
const employeeId = route.params.id   // String

// ─── Employee basic info ──────────────────────────────────
const empInfo   = ref(null)
const empLoading = ref(false)

async function loadEmpInfo() {
  empLoading.value = true
  try {
    const res = await employeeApi.getById(employeeId)
    empInfo.value = res.data
  } catch (_) { /* non-critical */ } finally {
    empLoading.value = false
  }
}

// ─── Alarm history (from database) ───────────────────────
const alarmList    = ref([])
const alarmTotal   = ref(0)
const alarmLoading = ref(false)
const alarmPage    = ref(1)

async function loadAlarms() {
  alarmLoading.value = true
  try {
    const res = await heartRateApi.list({
      employeeId,
      isAbnormal: 1,
      page: alarmPage.value,
      size: 15
    })
    alarmList.value  = res.data.list
    alarmTotal.value = Number(res.data.total)
  } finally {
    alarmLoading.value = false
  }
}

// ─── Real-time heart rate chart (SSE) ────────────────────
const HR_MIN   = 30
const HR_MAX   = 210
const HR_RANGE = HR_MAX - HR_MIN
const CHART_W  = 800
const CHART_H  = 140
const CHART_PAD = 8

const SSE_RECONNECT_DELAY_MS = 3000   // Delay before SSE reconnect attempt
const MAX_HR_HISTORY_LENGTH  = 60     // Rolling window of heart rate readings for chart
const MAX_LIVE_ALERTS        = 50     // Maximum stored live alert entries

function hrY(hr) {
  const clamped = Math.max(HR_MIN, Math.min(HR_MAX, hr))
  return CHART_H - CHART_PAD - ((clamped - HR_MIN) / HR_RANGE) * (CHART_H - 2 * CHART_PAD)
}

const sseOk         = ref(false)
const hrHistory     = ref([])        // { hr: Number, isAbnormal: Boolean }
const currentDeviceId = ref(null)
const liveAlerts    = ref([])        // { time, hr } – real-time feed from SSE

const currentHr = computed(() => {
  if (!hrHistory.value.length) return null
  return hrHistory.value[hrHistory.value.length - 1].hr
})

const isCurrentAbnormal = computed(() => {
  if (!hrHistory.value.length) return false
  return hrHistory.value[hrHistory.value.length - 1].isAbnormal
})

const currentStatusTag = computed(() => {
  if (!hrHistory.value.length) return { type: 'info', label: '— 等待数据' }
  return isCurrentAbnormal.value
    ? { type: 'danger',  label: '⚠ 异常' }
    : { type: 'success', label: '✓ 正常' }
})

// Show at most 60 dots to avoid cluttering the SVG
const visibleDots = computed(() => {
  const pts = hrHistory.value
  return pts.map((p, i) => ({
    x: (i / Math.max(pts.length - 1, 1)) * CHART_W,
    y: hrY(p.hr),
    abnormal: p.isAbnormal
  }))
})

const chartPoints = computed(() => {
  if (visibleDots.value.length < 2) return ''
  return visibleDots.value.map(d => `${d.x.toFixed(1)},${d.y.toFixed(1)}`).join(' ')
})

// ─── SSE ─────────────────────────────────────────────────
let eventSource = null

function connectSse() {
  if (eventSource) return
  eventSource = new EventSource('/api/realtime/stream')

  eventSource.addEventListener('connected', () => { sseOk.value = true })

  eventSource.addEventListener('heartrate', (e) => {
    try {
      const d = JSON.parse(e.data)
      if (String(d.userId) !== String(employeeId)) return

      const hr = d.heartRate != null ? Number(d.heartRate) : null
      if (hr === null) return

      const isAbnormal = !!d.isAbnormal
      hrHistory.value.push({ hr, isAbnormal })
      if (hrHistory.value.length > MAX_HR_HISTORY_LENGTH) hrHistory.value.shift()

      if (d.deviceId) currentDeviceId.value = d.deviceId

      if (isAbnormal) {
        liveAlerts.value.push({ time: new Date().toLocaleTimeString('zh-CN'), hr })
        if (liveAlerts.value.length > MAX_LIVE_ALERTS) liveAlerts.value.shift()
      }
    } catch (_) {}
  })

  eventSource.onerror = () => {
    sseOk.value = false
    eventSource.close()
    eventSource = null
    setTimeout(connectSse, SSE_RECONNECT_DELAY_MS)
  }
}

// ─── Utilities ────────────────────────────────────────────
function formatDt(dt) {
  if (!dt) return '—'
  return String(dt).replace('T', ' ').slice(0, 19)
}

async function loadRecentHistory() {
  try {
    const res = await heartRateApi.list({ employeeId, page: 1, size: 30 })
    const records = (res.data.list || []).reverse()   // oldest first
    hrHistory.value = records.map(r => ({ hr: r.heartRate, isAbnormal: r.isAbnormal === 1 }))
    if (records.length) currentDeviceId.value = records[records.length - 1].deviceId
  } catch (_) {}
}

// ─── Lifecycle ────────────────────────────────────────────
onMounted(() => {
  loadEmpInfo()
  loadAlarms()
  loadRecentHistory()
  connectSse()
})

onUnmounted(() => {
  if (eventSource) { eventSource.close(); eventSource = null }
})
</script>

<style scoped>
.detail-page { display: flex; flex-direction: column; gap: 14px; }

/* ── Top bar ──────────────────────────────────────────── */
.top-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
}
.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
  flex: 1;
}
.ml-auto { margin-left: auto; }

/* ── Two-column layout ───────────────────────────────── */
.detail-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.left-panel  { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 14px; }
.right-panel { width: 340px; flex-shrink: 0; display: flex; flex-direction: column; gap: 14px; }

/* ── Card header row ────────────────────────────────── */
.card-hd {
  display: flex;
  align-items: center;
  gap: 6px;
}
.hd-text { font-size: 15px; font-weight: 600; color: #303133; }
.chart-count { font-size: 12px; color: #909399; margin-left: auto; }

/* ── Heart rate values ─────────────────────────────── */
.rate-ok     { color: #67c23a; font-weight: 700; }
.rate-danger { color: #f56c6c; font-weight: 700; }

/* ── Chart ──────────────────────────────────────────── */
.empty-chart { padding: 30px 0; }
.chart-wrap  { padding: 4px 0; }

/* ── Alarm pagination ───────────────────────────────── */
.alarm-pag { margin-top: 10px; display: flex; justify-content: flex-end; }

/* ── Live alert feed ────────────────────────────────── */
.live-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}
.live-item:last-child { border-bottom: none; }
.live-time { color: #909399; font-size: 12px; }
.live-rate { font-weight: 700; color: #f56c6c; margin-left: auto; }
</style>
