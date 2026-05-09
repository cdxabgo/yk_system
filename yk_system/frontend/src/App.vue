<template>
  <!-- 登录页面不显示导航栏 -->
  <router-view v-if="isLoginPage" />

  <!-- 主布局 -->
  <el-container v-else class="layout-container">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <div class="logo-badge">
          <el-icon size="22"><Monitor /></el-icon>
        </div>
        <div class="logo-text">
          <span>井下心率监测</span>
          <small>Subsurface Pulse Command</small>
        </div>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#ffffff"
        text-color="#606266"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/employee">
          <el-icon><User /></el-icon>
          <span>职工管理</span>
        </el-menu-item>
        <el-menu-item index="/disease">
          <el-icon><FirstAidKit /></el-icon>
          <span>疾病管理</span>
        </el-menu-item>
        <el-menu-item index="/heartRate">
          <el-icon><Odometer /></el-icon>
          <span>心率管理</span>
        </el-menu-item>
        <el-menu-item index="/realtime">
          <el-icon><Cpu /></el-icon>
          <span>实时心率监测</span>
        </el-menu-item>
        <el-menu-item index="/dashboard">
          <el-icon><TrendCharts /></el-icon>
          <span>监控看板</span>
        </el-menu-item>
        <el-menu-item index="/monitor">
          <el-icon><DataAnalysis /></el-icon>
          <span>班中职工监控</span>
        </el-menu-item>
        <el-menu-item index="/analytics">
          <el-icon><PieChart /></el-icon>
          <span>数据分析看板</span>
        </el-menu-item>
        <el-menu-item index="/healthAdvice">
          <el-icon><Document /></el-icon>
          <span>健康建议生成</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <span class="header-title">井下职工心率实时监测系统</span>
          <span class="header-subtitle">Shift Pulse Observatory · Safety Insight Grid</span>
        </div>
        <div class="header-right">
          <el-icon style="margin-right:4px"><Avatar /></el-icon>
          <span class="username">{{ userInfo?.realName || userInfo?.username }}</span>
          <el-divider direction="vertical" />
          <el-button link type="primary" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Monitor, DataAnalysis, FirstAidKit, Odometer, Avatar, Cpu, TrendCharts, Document, PieChart } from '@element-plus/icons-vue'
import { authApi } from './api/index'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)
const isLoginPage = computed(() => route.path === '/login')

const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await authApi.logout()
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 取消退出
  }
}
</script>

<style>
:root {
  --yk-primary: #409EFF;
  --yk-primary-light: #66b1ff;
  --yk-primary-lighter: #a0cfff;
  --yk-success: #67c23a;
  --yk-success-light: #85ce61;
  --yk-warning: #e6a23c;
  --yk-warning-light: #ebb563;
  --yk-danger: #f56c6c;
  --yk-danger-light: #f89898;
  --yk-info: #909399;
  --yk-bg: #f0f2f5;
  --yk-bg-light: #f5f7fa;
  --yk-bg-white: #ffffff;
  --yk-text-primary: #303133;
  --yk-text-regular: #606266;
  --yk-text-muted: #909399;
  --yk-text-placeholder: #c0c4cc;
  --yk-border: #e4e7ed;
  --yk-border-light: #ebeef5;
  --yk-border-lighter: #f2f6fc;
  --yk-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.06);
  --yk-shadow-light: 0 1px 4px 0 rgba(0, 0, 0, 0.04);
  --yk-radius: 8px;
  --yk-radius-lg: 12px;
  --yk-font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', system-ui, -apple-system, sans-serif;

  --el-color-primary: var(--yk-primary);
  --el-color-primary-light-3: var(--yk-primary-light);
  --el-color-primary-light-5: var(--yk-primary-lighter);
  --el-color-success: var(--yk-success);
  --el-color-success-light-3: var(--yk-success-light);
  --el-color-warning: var(--yk-warning);
  --el-color-warning-light-3: var(--yk-warning-light);
  --el-color-danger: var(--yk-danger);
  --el-color-danger-light-3: var(--yk-danger-light);
  --el-color-info: var(--yk-info);
  --el-text-color-primary: var(--yk-text-primary);
  --el-text-color-regular: var(--yk-text-regular);
  --el-text-color-secondary: var(--yk-text-muted);
  --el-text-color-placeholder: var(--yk-text-placeholder);
  --el-border-color: var(--yk-border);
  --el-border-color-light: var(--yk-border-light);
  --el-border-color-lighter: var(--yk-border-lighter);
  --el-fill-color-blank: #ffffff;
  --el-fill-color-light: #f5f7fa;
  --el-fill-color: #f0f2f5;
  --el-bg-color: #ffffff;
  --el-bg-color-overlay: #ffffff;
  --el-border-radius-base: var(--yk-radius);
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: var(--yk-font-family);
  background: var(--yk-bg);
  color: var(--yk-text-primary);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
}

.layout-container { height: 100vh; }

/* ── Sidebar ────────────────────────────────── */
.sidebar {
  background: var(--yk-bg-white);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--yk-border);
  box-shadow: 1px 0 6px rgba(0, 0, 0, 0.03);
}

.logo {
  height: 72px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  background: #fafbfc;
  color: var(--yk-text-primary);
  flex-shrink: 0;
  border-bottom: 1px solid var(--yk-border);
}

.logo-badge {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #409EFF, #66b1ff);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.25);
}

.logo-text span {
  display: block;
  font-size: 17px;
  font-weight: 600;
  color: var(--yk-text-primary);
  letter-spacing: 0.5px;
}

.logo-text small {
  display: block;
  font-size: 11px;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--yk-text-muted);
  margin-top: 2px;
}

.header {
  background: var(--yk-bg-white);
  border-bottom: 1px solid var(--yk-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: var(--yk-shadow-light);
}

.header-left { display: flex; flex-direction: column; gap: 2px; }

.header-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--yk-text-primary);
}

.header-subtitle {
  font-size: 11px;
  letter-spacing: 0.8px;
  color: var(--yk-text-muted);
  text-transform: uppercase;
}

.header-right {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: var(--yk-text-regular);
  gap: 4px;
}

.username { margin: 0 6px; }

.main-content {
  background: var(--yk-bg);
  padding: 20px 24px;
  overflow-y: auto;
}

/* ── Menu ───────────────────────────────────── */
.el-menu {
  border-right: none;
  background: transparent;
  padding: 8px 8px 12px;
}

.sidebar .el-menu-item {
  border-radius: 8px;
  margin: 3px 6px;
  height: 42px;
  color: var(--yk-text-regular);
  transition: all 0.2s ease;
  font-size: 14px;
}

.sidebar .el-menu-item:hover {
  background: #ecf5ff;
  color: var(--yk-primary);
}

.sidebar .el-menu-item.is-active {
  background: #ecf5ff;
  color: var(--yk-primary);
  font-weight: 500;
}

/* ── Cards ──────────────────────────────────── */
.el-card {
  background: var(--yk-bg-white);
  border: 1px solid var(--yk-border);
  border-radius: var(--yk-radius-lg);
  box-shadow: var(--yk-shadow-light);
  color: var(--yk-text-primary);
}

.el-card__header {
  border-bottom: 1px solid var(--yk-border-light);
  background: transparent;
  padding: 14px 20px;
}

.el-card__body {
  padding: 20px;
}

/* ── Table ──────────────────────────────────── */
.el-table {
  background: transparent;
  color: var(--yk-text-primary);
}

.el-table th.el-table__cell {
  background: #fafbfc;
  color: var(--yk-text-primary);
  font-weight: 500;
}

.el-table td.el-table__cell {
  background: #ffffff;
  color: var(--yk-text-regular);
}

.el-table--border .el-table__cell,
.el-table--border::before,
.el-table__inner-wrapper::before {
  border-color: var(--yk-border);
}

.el-table__body tr:hover > td.el-table__cell {
  background: #f5f7fa;
}

.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background: #fafbfc;
}

/* ── Inputs ─────────────────────────────────── */
.el-input__wrapper,
.el-textarea__inner,
.el-select__wrapper {
  background: #ffffff;
  box-shadow: 0 0 0 1px var(--yk-border) inset;
  color: var(--yk-text-primary);
  border-radius: var(--yk-radius);
}

.el-input__inner,
.el-textarea__inner,
.el-select__selected-item,
.el-select__placeholder {
  color: var(--yk-text-primary);
}

.el-input__wrapper.is-focus,
.el-textarea__inner:focus,
.el-select__wrapper.is-focused {
  box-shadow: 0 0 0 1px var(--yk-primary) inset;
}

.el-input__wrapper:hover,
.el-textarea__inner:hover,
.el-select__wrapper:hover {
  box-shadow: 0 0 0 1px var(--yk-text-placeholder) inset;
}

/* ── Dialog ─────────────────────────────────── */
.el-dialog {
  background: var(--yk-bg-white);
  border: none;
  border-radius: var(--yk-radius-lg);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12);
}

.el-dialog__header {
  border-bottom: 1px solid var(--yk-border-light);
  padding: 18px 24px;
}

.el-dialog__body {
  padding: 24px;
}

.el-dialog__footer {
  border-top: 1px solid var(--yk-border-light);
  padding: 14px 24px;
}

/* ── Pagination ─────────────────────────────── */
.el-pagination .el-pager li:not(.is-disabled).is-active {
  background-color: var(--yk-primary);
}

/* ── Buttons ────────────────────────────────── */
.el-button--primary {
  --el-button-bg-color: var(--yk-primary);
  --el-button-border-color: var(--yk-primary);
  --el-button-hover-bg-color: var(--yk-primary-light);
  --el-button-hover-border-color: var(--yk-primary-light);
  --el-button-active-bg-color: var(--yk-primary);
  --el-button-active-border-color: var(--yk-primary);
}

.el-button {
  border-radius: var(--yk-radius);
  font-weight: 400;
}

/* ── Tags ───────────────────────────────────── */
.el-tag {
  border-radius: 4px;
}

/* ── Divider ────────────────────────────────── */
.el-divider--vertical { border-color: var(--yk-border); }

/* ── Scrollbar ──────────────────────────────── */
.el-scrollbar__bar.is-vertical .el-scrollbar__thumb {
  background-color: rgba(144, 147, 153, 0.3);
}
.el-scrollbar__bar.is-vertical .el-scrollbar__thumb:hover {
  background-color: rgba(144, 147, 153, 0.5);
}

/* ── Common page layout ─────────────────────── */
.page-container { display: flex; flex-direction: column; gap: 16px; }

/* ── Menu item group ────────────────────────── */
.el-menu-item i { font-size: 16px; }
</style>
