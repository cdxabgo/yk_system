<template>
  <!-- 登录页面不显示导航栏 -->
  <router-view v-if="isLoginPage" />

  <!-- 主布局 -->
  <el-container v-else class="layout-container">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon size="20" style="margin-right:6px"><Monitor /></el-icon>
        <span>井下心率监测系统</span>
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
        <span class="header-title">井下职工心率实时监测系统</span>
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
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Microsoft YaHei', sans-serif; }

.layout-container { height: 100vh; }

.sidebar {
  background-color: #304156;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #263445;
  color: #fff;
  font-size: 15px;
  font-weight: bold;
  padding: 0 10px;
  flex-shrink: 0;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
  padding: 0 20px;
}

.header-title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.header-right {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

.username { margin: 0 6px; }

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

.el-menu { border-right: none; }
</style>
