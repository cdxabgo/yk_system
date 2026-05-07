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
        background-color="#304156"
        text-color="#bfcbd9"
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
import { User, Monitor, DataAnalysis, FirstAidKit, Odometer, Avatar, Cpu, TrendCharts, Document } from '@element-plus/icons-vue'
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
  --yk-bg: #070b11;
  --yk-bg-deep: #05080d;
  --yk-surface: rgba(16, 25, 36, 0.78);
  --yk-surface-strong: rgba(18, 28, 40, 0.92);
  --yk-border: rgba(130, 170, 190, 0.18);
  --yk-border-strong: rgba(130, 170, 190, 0.35);
  --yk-accent: #5de3ff;
  --yk-accent-soft: rgba(93, 227, 255, 0.16);
  --yk-warning: #ffb347;
  --yk-danger: #ff6b6b;
  --yk-success: #52e6a7;
  --yk-text: #e6f0ff;
  --yk-muted: #9fb2c8;
  --yk-font-display: 'ZCOOL XiaoWei', serif;
  --yk-font-body: 'Noto Sans SC', sans-serif;
  --yk-shadow: 0 18px 40px rgba(3, 8, 15, 0.45);

  --el-color-primary: var(--yk-accent);
  --el-color-success: var(--yk-success);
  --el-color-warning: var(--yk-warning);
  --el-color-danger: var(--yk-danger);
  --el-border-color: var(--yk-border);
  --el-text-color-primary: var(--yk-text);
  --el-text-color-regular: var(--yk-muted);
  --el-fill-color-blank: transparent;
  --el-fill-color-light: rgba(255, 255, 255, 0.04);
  --el-fill-color: rgba(255, 255, 255, 0.06);
  --el-bg-color: transparent;
  --el-bg-color-overlay: var(--yk-surface-strong);
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: var(--yk-font-body);
  background: radial-gradient(circle at 10% 20%, rgba(93, 227, 255, 0.08), transparent 45%),
    radial-gradient(circle at 90% 10%, rgba(255, 179, 71, 0.12), transparent 40%),
    linear-gradient(180deg, #070b11 0%, #0b121a 65%, #0c141f 100%);
  color: var(--yk-text);
  min-height: 100vh;
  position: relative;
}

body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: repeating-linear-gradient(
      0deg,
      rgba(255, 255, 255, 0.04) 0,
      rgba(255, 255, 255, 0.04) 1px,
      transparent 1px,
      transparent 120px
    ),
    repeating-linear-gradient(
      90deg,
      rgba(255, 255, 255, 0.03) 0,
      rgba(255, 255, 255, 0.03) 1px,
      transparent 1px,
      transparent 120px
    );
  opacity: 0.35;
  pointer-events: none;
  z-index: 0;
}

body::after {
  content: '';
  position: fixed;
  inset: 0;
  background: radial-gradient(circle at 70% 60%, rgba(93, 227, 255, 0.08), transparent 55%);
  opacity: 0.6;
  pointer-events: none;
  z-index: 0;
}

#app {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.layout-container { height: 100vh; color: var(--yk-text); }

.sidebar {
  background: linear-gradient(180deg, #0b131c 0%, #0b1118 55%, #090d13 100%);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--yk-border);
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.04);
}

.logo {
  height: 72px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  background: rgba(12, 19, 27, 0.95);
  color: var(--yk-text);
  flex-shrink: 0;
  border-bottom: 1px solid var(--yk-border);
}

.logo-badge {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(93, 227, 255, 0.25), rgba(255, 179, 71, 0.1));
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--yk-accent);
  box-shadow: inset 0 0 0 1px rgba(93, 227, 255, 0.35);
}

.logo-text span {
  display: block;
  font-family: var(--yk-font-display);
  font-size: 18px;
  letter-spacing: 1px;
}

.logo-text small {
  display: block;
  font-size: 11px;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: var(--yk-muted);
  margin-top: 2px;
}

.header {
  background: var(--yk-surface-strong);
  border-bottom: 1px solid var(--yk-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: var(--yk-shadow);
  backdrop-filter: blur(10px);
}

.header-left { display: flex; flex-direction: column; gap: 2px; }

.header-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--yk-text);
  font-family: var(--yk-font-display);
}

.header-subtitle {
  font-size: 12px;
  letter-spacing: 1px;
  color: var(--yk-muted);
  text-transform: uppercase;
}

.header-right {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: var(--yk-text);
  gap: 4px;
}

.username { margin: 0 6px; }

.main-content {
  background: transparent;
  padding: 24px 26px;
  overflow-y: auto;
}

.el-menu {
  border-right: none;
  background: transparent;
  padding: 12px 10px 16px;
}

.sidebar .el-menu-item {
  border-radius: 12px;
  margin: 6px 8px;
  height: 44px;
  color: var(--yk-muted);
  transition: all 0.2s ease;
}

.sidebar .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--yk-text);
}

.sidebar .el-menu-item.is-active {
  background: var(--yk-accent-soft);
  color: var(--yk-text);
  box-shadow: inset 0 0 0 1px rgba(93, 227, 255, 0.35);
}

.el-card {
  background: var(--yk-surface);
  border: 1px solid var(--yk-border);
  box-shadow: var(--yk-shadow);
  backdrop-filter: blur(8px);
  color: var(--yk-text);
}

.el-card__header {
  border-bottom: 1px solid var(--yk-border);
  background: rgba(255, 255, 255, 0.02);
}

.el-table {
  background: transparent;
  color: var(--yk-text);
}

.el-table th.el-table__cell {
  background: rgba(255, 255, 255, 0.04);
  color: var(--yk-text);
}

.el-table td.el-table__cell {
  background: transparent;
  color: var(--yk-text);
}

.el-table--border .el-table__cell,
.el-table--border::before,
.el-table__inner-wrapper::before {
  border-color: var(--yk-border);
}

.el-table__body tr:hover > td.el-table__cell {
  background: rgba(93, 227, 255, 0.05);
}

.el-input__wrapper,
.el-textarea__inner,
.el-select__wrapper {
  background: rgba(255, 255, 255, 0.05);
  box-shadow: inset 0 0 0 1px rgba(130, 170, 190, 0.25);
  color: var(--yk-text);
}

.el-input__inner,
.el-textarea__inner,
.el-select__selected-item,
.el-select__placeholder {
  color: var(--yk-text);
}

.el-input__wrapper.is-focus,
.el-textarea__inner:focus,
.el-select__wrapper.is-focused {
  box-shadow: 0 0 0 1px rgba(93, 227, 255, 0.6);
}

.el-dialog {
  background: var(--yk-surface-strong);
  border: 1px solid var(--yk-border);
  box-shadow: var(--yk-shadow);
}

.el-dialog__header {
  border-bottom: 1px solid var(--yk-border);
}

.el-divider--vertical { border-color: var(--yk-border); }

.page-container { display: flex; flex-direction: column; gap: 16px; }

.pagination .el-pagination {
  --el-pagination-button-color: var(--yk-text);
}

.el-scrollbar__bar { opacity: 0.5; }
</style>
