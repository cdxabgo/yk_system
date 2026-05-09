<template>
  <div class="analytics-page">
    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background:#ecf5ff;color:#409EFF"><el-icon size="24"><Odometer /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.totalRecords || 0 }}</div>
          <div class="stat-label">今日检测总量</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#fef0f0;color:#f56c6c"><el-icon size="24"><WarningFilled /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value danger">{{ stats.abnormalCount || 0 }}</div>
          <div class="stat-label">今日异常次数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#fefce8;color:#e6a23c"><el-icon size="24"><TrendCharts /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value warning">{{ stats.abnormalRate || 0 }}%</div>
          <div class="stat-label">异常率</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#f0f9eb;color:#67c23a"><el-icon size="24"><UserFilled /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value success">{{ stats.employeeCount || 0 }}</div>
          <div class="stat-label">监测职工数</div>
        </div>
      </div>
    </div>

    <!-- 图表行1: 心率实时折线图 + 异常分布饼图 -->
    <div class="chart-row">
      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <span class="chart-title">职工心率实时走势</span>
            <el-select v-model="selectedEmployee" placeholder="选择职工" size="small" style="width:200px" @change="loadTimeseries">
              <el-option v-for="emp in employees" :key="emp.id" :label="emp.name" :value="emp.id" />
            </el-select>
          </div>
        </template>
        <div ref="lineChartRef" class="chart-body"></div>
      </el-card>

      <el-card class="chart-card narrow">
        <template #header>
          <div class="chart-header">
            <span class="chart-title">今日异常类型分布</span>
          </div>
        </template>
        <div ref="pieChartRef" class="chart-body"></div>
      </el-card>
    </div>

    <!-- 图表行2: 时段趋势对比 -->
    <div class="chart-row">
      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <span class="chart-title">分时段心率趋势对比（今日 vs 昨日）</span>
            <el-tag size="small" type="info">蓝色=今日 · 灰色=昨日</el-tag>
          </div>
        </template>
        <div ref="barChartRef" class="chart-body"></div>
      </el-card>
    </div>

    <!-- 图表行3: 异常详情 + 模型对比 -->
    <div class="chart-row">
      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <span class="chart-title">各类异常数量对比</span>
          </div>
        </template>
        <div ref="anomalyTypeChartRef" class="chart-body"></div>
      </el-card>
      <el-card class="chart-card narrow">
        <template #header>
          <div class="chart-header">
            <span class="chart-title">模型性能概览</span>
            <el-button size="small" :icon="Refresh" @click="loadAll">刷新</el-button>
          </div>
        </template>
        <div class="perf-panel">
          <div class="perf-row">
            <span class="perf-label">检测模式</span>
            <span class="perf-value">规则 + LightGBM 融合</span>
          </div>
          <el-divider />
          <div class="perf-row">
            <span class="perf-label">规则检测命中</span>
            <span class="perf-value">{{ stats.highRateCount + stats.lowRateCount + stats.extremeCount || 0 }} 次</span>
          </div>
          <div class="perf-row">
            <span class="perf-label">ML模型辅助</span>
            <span class="perf-value">{{ Math.max(0, (stats.abnormalCount || 0) - (stats.highRateCount + stats.lowRateCount + stats.extremeCount || 0)) }} 次</span>
          </div>
          <el-divider />
          <div class="perf-row">
            <span class="perf-label">高心率异常</span>
            <span class="perf-value danger">{{ stats.highRateCount || 0 }}</span>
          </div>
          <div class="perf-row">
            <span class="perf-label">低心率异常</span>
            <span class="perf-value warning">{{ stats.lowRateCount || 0 }}</span>
          </div>
          <div class="perf-row">
            <span class="perf-label">极值异常</span>
            <span class="perf-value danger">{{ stats.extremeCount || 0 }}</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Odometer, WarningFilled, TrendCharts, UserFilled, Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { heartRateApi, employeeApi } from '../api/index'

const stats = ref({})
const employees = ref([])
const selectedEmployee = ref(null)

const lineChartRef = ref(null)
const pieChartRef = ref(null)
const barChartRef = ref(null)
const anomalyTypeChartRef = ref(null)

let lineChart = null, pieChart = null, barChart = null, anomalyTypeChart = null
let resizeHandler = null

const COLORS = {
  primary: '#409EFF',
  danger: '#f56c6c',
  warning: '#e6a23c',
  success: '#67c23a',
  gray: '#909399'
}

function initCharts() {
  if (lineChartRef.value) lineChart = echarts.init(lineChartRef.value)
  if (pieChartRef.value) pieChart = echarts.init(pieChartRef.value)
  if (barChartRef.value) barChart = echarts.init(barChartRef.value)
  if (anomalyTypeChartRef.value) anomalyTypeChart = echarts.init(anomalyTypeChartRef.value)
  resizeHandler = () => {
    lineChart?.resize()
    pieChart?.resize()
    barChart?.resize()
    anomalyTypeChart?.resize()
  }
  window.addEventListener('resize', resizeHandler)
}

async function loadEmployees() {
  try {
    const res = await employeeApi.list({ page: 1, size: 200 })
    employees.value = res.data.list || []
    if (employees.value.length > 0) {
      selectedEmployee.value = employees.value[0].id
      loadTimeseries()
    }
  } catch (_) {}
}

async function loadStats() {
  try {
    const res = await heartRateApi.todayStats()
    if (res.data) {
      stats.value = res.data
      updatePieChart()
      updateAnomalyTypeChart()
    }
  } catch (_) {}
}

async function loadTimeseries() {
  if (!selectedEmployee.value) return
  try {
    const res = await heartRateApi.timeseries({ employeeId: selectedEmployee.value })
    const list = res.data || []
    updateLineChart(list)
  } catch (_) {}
}

async function loadHourlyTrend() {
  try {
    const res = await heartRateApi.hourlyTrend()
    updateBarChart(res.data)
  } catch (_) {}
}

function updateLineChart(data) {
  if (!lineChart) return
  const times = data.map(d => {
    const t = d.collectTime || d.measure_time
    return t ? String(t).substring(11, 16) : ''
  })
  const rates = data.map(d => d.heartRate)

  lineChart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: p => `${p[0].axisValue}<br/>心率: <b>${p[0].value}</b> bpm`
    },
    grid: { top: 10, right: 20, bottom: 30, left: 50 },
    xAxis: {
      type: 'category', data: times,
      axisLabel: { fontSize: 11, interval: Math.max(1, Math.floor(times.length / 15)) }
    },
    yAxis: {
      type: 'value', name: 'bpm', min: 0, max: 220,
      axisLabel: { fontSize: 11 }
    },
    series: [{
      type: 'line', data: rates, smooth: true,
      lineStyle: { color: COLORS.primary, width: 2 },
      itemStyle: { color: COLORS.primary },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(64,158,255,0.25)' },
        { offset: 1, color: 'rgba(64,158,255,0.02)' }
      ]) },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { type: 'dashed', color: COLORS.danger, width: 1 },
        data: [{ yAxis: 150, label: { formatter: '150', fontSize: 10 } }]
      }
    }]
  }, true)
}

function updatePieChart() {
  if (!pieChart) return
  const s = stats.value
  const pieData = [
    { value: Math.max(0, (s.totalRecords || 0) - (s.abnormalCount || 0)), name: '正常', itemStyle: { color: COLORS.success } },
    { value: s.highRateCount || 0, name: '高心率', itemStyle: { color: COLORS.danger } },
    { value: s.lowRateCount || 0, name: '低心率', itemStyle: { color: COLORS.warning } },
    { value: s.extremeCount || 0, name: '极值', itemStyle: { color: '#ff4d4f' } }
  ].filter(d => d.value > 0)

  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 条 ({d}%)' },
    legend: { bottom: 10, textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['50%', '45%'],
      data: pieData,
      label: { formatter: '{b}\n{d}%', fontSize: 11 },
      emphasis: { label: { fontSize: 16, fontWeight: 'bold' } }
    }]
  }, true)
}

function updateBarChart(data) {
  if (!barChart) return
  const today = data?.today || []
  const yesterday = data?.yesterday || []

  const hours = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0') + ':00')
  const todayMap = {}, yesterdayMap = {}
  today.forEach(d => { todayMap[d.hour] = d.avgHeartRate })
  yesterday.forEach(d => { yesterdayMap[d.hour] = d.avgHeartRate })

  barChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['今日', '昨日'], bottom: 0, textStyle: { fontSize: 12 } },
    grid: { top: 10, right: 20, bottom: 35, left: 50 },
    xAxis: {
      type: 'category', data: hours,
      axisLabel: { fontSize: 10, interval: 2 }
    },
    yAxis: { type: 'value', name: 'bpm', min: 0, max: 200, axisLabel: { fontSize: 11 } },
    series: [
      {
        name: '今日', type: 'bar',
        data: hours.map(h => todayMap[parseInt(h)] ?? null),
        itemStyle: { color: COLORS.primary, borderRadius: [3, 3, 0, 0] },
        barMaxWidth: 14
      },
      {
        name: '昨日', type: 'bar',
        data: hours.map(h => yesterdayMap[parseInt(h)] ?? null),
        itemStyle: { color: '#c0c4cc', borderRadius: [3, 3, 0, 0] },
        barMaxWidth: 14
      }
    ]
  }, true)
}

function updateAnomalyTypeChart() {
  if (!anomalyTypeChart) return
  const s = stats.value
  anomalyTypeChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { top: 10, right: 20, bottom: 30, left: 50 },
    xAxis: {
      type: 'category',
      data: ['高心率', '低心率', '极值'],
      axisLabel: { fontSize: 12 }
    },
    yAxis: { type: 'value', name: '次', axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar',
      data: [
        { value: s.highRateCount || 0, itemStyle: { color: COLORS.danger } },
        { value: s.lowRateCount || 0, itemStyle: { color: COLORS.warning } },
        { value: s.extremeCount || 0, itemStyle: { color: '#ff4d4f' } }
      ],
      barMaxWidth: 40,
      label: { show: true, position: 'top', fontSize: 14, fontWeight: 'bold' }
    }]
  }, true)
}

async function loadAll() {
  await Promise.all([loadStats(), loadTimeseries(), loadHourlyTrend()])
}

onMounted(async () => {
  await loadEmployees()
  await nextTick()
  initCharts()
  await loadAll()
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeHandler)
  lineChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
  anomalyTypeChart?.dispose()
})
</script>

<style scoped>
.analytics-page { display: flex; flex-direction: column; gap: 18px; }

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  border: 1px solid var(--yk-border);
}

.stat-icon {
  width: 52px; height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-value {
  font-size: 28px; font-weight: 700;
  color: var(--yk-text-primary);
  line-height: 1.1;
}
.stat-value.danger  { color: #f56c6c; }
.stat-value.warning { color: #e6a23c; }
.stat-value.success { color: #67c23a; }

.stat-label {
  font-size: 13px; color: var(--yk-text-muted);
  margin-top: 2px;
}

.chart-row {
  display: flex;
  gap: 16px;
}
.chart-card { flex: 1; min-width: 0; }
.chart-card.narrow { flex: 0 0 380px; }

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chart-title { font-size: 15px; font-weight: 600; color: var(--yk-text-primary); }

.chart-body { height: 320px; }

.perf-panel { padding: 8px 0; }
.perf-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
}
.perf-label { font-size: 13px; color: var(--yk-text-muted); }
.perf-value { font-size: 14px; font-weight: 600; color: var(--yk-text-primary); }
.perf-value.danger  { color: #f56c6c; }
.perf-value.warning { color: #e6a23c; }

@media (max-width: 1200px) {
  .stat-cards { grid-template-columns: repeat(2, 1fr); }
  .chart-row { flex-direction: column; }
  .chart-card.narrow { flex: 1; }
}
@media (max-width: 640px) {
  .stat-cards { grid-template-columns: 1fr; }
}
</style>
