<template>
  <div class="page-container">
    <el-card>
      <el-form inline>
        <el-form-item label="职工">
          <el-select
            v-model="selectedEmployeeId"
            filterable
            clearable
            placeholder="请选择职工"
            style="width: 280px"
          >
            <el-option
              v-for="item in employeeOptions"
              :key="item.id"
              :label="`${item.name}（${item.job || '未知岗位'}）`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="MagicStick" :loading="loading" @click="handleGenerate">
            生成健康建议
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="adviceResult" class="result-card">
      <template #header>
        <div class="card-header">
          <span>健康建议结果</span>
          <el-tag type="success">采样 {{ adviceResult.todaySampleCount }} 条</el-tag>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="职工ID">{{ adviceResult.employeeId }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ adviceResult.employeeName }}</el-descriptions-item>
        <el-descriptions-item label="生成时间" :span="2">{{ adviceResult.generatedAt }}</el-descriptions-item>
      </el-descriptions>
      <el-divider />
      <el-input v-model="adviceResult.advice" type="textarea" :rows="12" readonly />
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import { employeeApi, healthAdviceApi } from '../api/index'

const loading = ref(false)
const employeeOptions = ref([])
const selectedEmployeeId = ref(null)
const adviceResult = ref(null)

const loadEmployeeOptions = async () => {
  try {
    const res = await employeeApi.list({ page: 1, size: 200 })
    employeeOptions.value = res.data.list || []
  } catch {
    employeeOptions.value = []
  }
}

const handleGenerate = async () => {
  if (!selectedEmployeeId.value) {
    ElMessage.warning('请先选择职工')
    return
  }
  loading.value = true
  try {
    const res = await healthAdviceApi.generate(selectedEmployeeId.value)
    adviceResult.value = res.data
    ElMessage.success('健康建议生成成功')
  } finally {
    loading.value = false
  }
}

onMounted(loadEmployeeOptions)
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card .card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
