<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <span>职工健康监测系统</span>
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
          <el-icon><Monitor /></el-icon>
          <span>心率管理</span>
        </el-menu-item>
        <el-menu-item index="/duty">
          <el-icon><DataAnalysis /></el-icon>
          <span>班中职工查询</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <span class="header-title">职工健康监测管理平台</span>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { User, Monitor, DataAnalysis, FirstAidKit } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Microsoft YaHei', sans-serif; }

.layout-container { height: 100vh; }

.sidebar {
  background-color: #304156;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #263445;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  padding: 0 10px;
  text-align: center;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
}

.header-title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

.el-menu { border-right: none; }
</style>
