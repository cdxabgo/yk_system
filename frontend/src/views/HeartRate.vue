<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="职工ID">
          <el-input v-model.number="searchForm.employeeId" placeholder="职工ID" clearable style="width:120px" />
        </el-form-item>
        <el-form-item label="异常状态">
          <el-select v-model="searchForm.isAbnormal" clearable placeholder="全部" style="width:110px">
            <el-option label="正常" :value="0" />
            <el-option label="异常" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker v-model="searchForm.startTime" type="datetime" placeholder="开始时间"
            value-format="YYYY-MM-DD HH:mm:ss" style="width:190px" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker v-model="searchForm.endTime" type="datetime" placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss" style="width:190px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadList">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">心率记录列表</span>
          <el-button type="primary" :icon="Plus" @click="openAdd">新增记录</el-button>
        </div>
      </template>

      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="id" label="记录ID" width="80" align="center" />
        <el-table-column prop="employeeId" label="职工ID" width="80" align="center" />
        <el-table-column prop="employeeName" label="职工姓名" width="100" />
        <el-table-column prop="job" label="岗位" width="100" />
        <el-table-column prop="heartRate" label="心率(次/分)" width="110" align="center">
          <template #default="{ row }">
            <span :class="row.isAbnormal ? 'rate-abnormal' : 'rate-normal'">{{ row.heartRate }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="collectTime" label="采集时间" width="170" />
        <el-table-column prop="isAbnormal" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.isAbnormal ? 'danger' : 'success'">
              {{ row.isAbnormal ? '异常' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="deviceId" label="设备ID" width="110" />
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          :total="pagination.total"
          @change="loadList"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新增心率记录" width="480px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="职工ID" prop="employeeId">
          <el-input-number v-model="form.employeeId" :min="1" style="width:100%" placeholder="请输入职工ID" />
        </el-form-item>
        <el-form-item label="心率值" prop="heartRate">
          <el-input-number v-model="form.heartRate" :min="30" :max="220" style="width:100%" />
        </el-form-item>
        <el-form-item label="采集时间" prop="collectTime">
          <el-date-picker v-model="form.collectTime" type="datetime" placeholder="请选择采集时间"
            value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="是否异常" prop="isAbnormal">
          <el-radio-group v-model="form.isAbnormal">
            <el-radio :label="0">正常</el-radio>
            <el-radio :label="1">异常</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="设备ID">
          <el-input v-model="form.deviceId" placeholder="如：HB-001（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Delete } from '@element-plus/icons-vue'
import { heartRateApi } from '../api/index'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const formRef = ref(null)

const searchForm = reactive({
  employeeId: null, isAbnormal: null, startTime: '', endTime: ''
})
const pagination = reactive({ page: 1, size: 10, total: 0 })
const form = reactive({
  employeeId: null, heartRate: 75, collectTime: '', isAbnormal: 0, deviceId: ''
})

const rules = {
  employeeId: [{ required: true, message: '请输入职工ID', trigger: 'blur' }],
  heartRate: [{ required: true, message: '请输入心率值', trigger: 'blur' }],
  collectTime: [{ required: true, message: '请选择采集时间', trigger: 'change' }]
}

const loadList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    if (searchForm.employeeId) params.employeeId = searchForm.employeeId
    if (searchForm.isAbnormal !== null && searchForm.isAbnormal !== '') params.isAbnormal = searchForm.isAbnormal
    if (searchForm.startTime) params.startTime = searchForm.startTime
    if (searchForm.endTime) params.endTime = searchForm.endTime

    const res = await heartRateApi.list(params)
    tableData.value = res.data.list || []
    pagination.total = Number(res.data.total) || 0
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  Object.assign(searchForm, { employeeId: null, isAbnormal: null, startTime: '', endTime: '' })
  pagination.page = 1
  loadList()
}

const openAdd = () => {
  Object.assign(form, { employeeId: null, heartRate: 75, collectTime: '', isAbnormal: 0, deviceId: '' })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      await heartRateApi.add(form)
      ElMessage.success('新增成功')
      dialogVisible.value = false
      loadList()
    } finally {
      submitLoading.value = false
    }
  })
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除该心率记录吗？`, '警告', { type: 'warning' })
  await heartRateApi.delete(row.id)
  ElMessage.success('删除成功')
  loadList()
}

onMounted(loadList)
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.search-card :deep(.el-card__body) { padding: 16px 20px 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--yk-text);
  letter-spacing: 0.6px;
}
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
.rate-abnormal { color: var(--yk-danger); font-weight: bold; font-size: 15px; }
.rate-normal { color: var(--yk-success); font-weight: bold; font-size: 15px; }
</style>
