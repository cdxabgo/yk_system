<template>
  <div class="login-page">
    <div class="login-shell">
      <div class="login-hero">
        <div class="hero-badge">Subsurface Pulse Command</div>
        <h1>井下职工心率监测系统</h1>
        <p>
          将井下安全数据转译为清晰的生命脉冲视图，实时掌握每一班次的身体状态。
        </p>
        <div class="hero-metrics">
          <div class="metric-card">
            <span class="metric-label">实时监测</span>
            <span class="metric-value">10s</span>
            <span class="metric-desc">轮询刷新</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">异常洞察</span>
            <span class="metric-value">5min</span>
            <span class="metric-desc">持续告警</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">数据覆盖</span>
            <span class="metric-value">100%</span>
            <span class="metric-desc">班中同步</span>
          </div>
        </div>
        <div class="pulse-line">
          <span v-for="n in 12" :key="n" class="pulse-bar" />
        </div>
      </div>
      <div class="login-card">
        <div class="login-header">
          <el-icon size="38" color="var(--yk-accent)"><Monitor /></el-icon>
          <div>
            <h2>欢迎进入监测中心</h2>
            <p>Heart Rate Monitoring Gateway</p>
          </div>
        </div>
        <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
              clearable
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
            >
              进入监测舱
            </el-button>
          </el-form-item>
        </el-form>
        <div class="login-tip">默认账号：admin / admin123</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Monitor } from '@element-plus/icons-vue'
import { authApi } from '../api/index'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await authApi.login(form)
      const { token, username, realName } = res.data
      localStorage.setItem('token', token)
      localStorage.setItem('userInfo', JSON.stringify({ username, realName }))
      ElMessage.success('登录成功')
      router.push('/employee')
    } catch {
      // 错误由拦截器处理
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
}

.login-shell {
  width: min(1120px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 48px;
  align-items: center;
}

.login-hero {
  color: var(--yk-text);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-badge {
  align-self: flex-start;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(93, 227, 255, 0.12);
  border: 1px solid rgba(93, 227, 255, 0.35);
  font-size: 12px;
  letter-spacing: 1.4px;
  text-transform: uppercase;
  color: var(--yk-accent);
}

.login-hero h1 {
  font-family: var(--yk-font-display);
  font-size: 36px;
  letter-spacing: 2px;
}

.login-hero p {
  font-size: 15px;
  color: var(--yk-muted);
  max-width: 520px;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  background: rgba(12, 20, 29, 0.7);
  border: 1px solid var(--yk-border);
  border-radius: 16px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--yk-muted);
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--yk-accent);
}

.metric-desc {
  font-size: 12px;
  color: var(--yk-muted);
}

.pulse-line {
  display: flex;
  gap: 6px;
  align-items: flex-end;
  height: 46px;
}

.pulse-bar {
  width: 8px;
  border-radius: 6px;
  background: linear-gradient(180deg, rgba(93, 227, 255, 0.8), rgba(93, 227, 255, 0.1));
  animation: pulse-bounce 1.8s ease-in-out infinite;
}

.pulse-bar:nth-child(4n + 1) { animation-delay: 0.2s; height: 20px; }
.pulse-bar:nth-child(4n + 2) { animation-delay: 0.6s; height: 34px; }
.pulse-bar:nth-child(4n + 3) { animation-delay: 1s; height: 26px; }
.pulse-bar:nth-child(4n) { animation-delay: 1.4s; height: 40px; }

.login-card {
  background: var(--yk-surface-strong);
  border-radius: 20px;
  padding: 36px 38px;
  border: 1px solid var(--yk-border);
  box-shadow: var(--yk-shadow);
  backdrop-filter: blur(12px);
}

.login-header {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 30px;
}

.login-header h2 {
  font-size: 20px;
  color: var(--yk-text);
  margin-bottom: 4px;
}

.login-header p {
  font-size: 12px;
  color: var(--yk-muted);
}

.login-btn {
  width: 100%;
  height: 46px;
  font-size: 15px;
  letter-spacing: 2px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--yk-accent), var(--yk-accent-strong));
  color: var(--yk-ink);
  border: none;
  font-weight: 700;
}

.login-tip {
  text-align: center;
  font-size: 12px;
  color: var(--yk-muted);
  margin-top: 12px;
}

@keyframes pulse-bounce {
  0%, 100% { opacity: 0.4; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(-6px); }
}

@media (max-width: 960px) {
  .login-shell {
    grid-template-columns: 1fr;
  }
  .hero-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
