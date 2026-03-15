<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>班中职工查询（联查职工信息、心率、异常心率）</span>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="query" class="search-form">
        <el-form-item label="班次日期">
          <el-date-picker v-model="query.shiftDate" type="date" placeholder="请选择日期"
            value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="班次类型">
          <el-select v-model="query.shiftType" placeholder="请选择班次" clearable>
            <el-option label="早班" value="早班" />
            <el-option label="中班" value="中班" />
            <el-option label="晚班" value="晚班" />
          </el-select>
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="query.empName" placeholder="请输入姓名" clearable />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="query.department" placeholder="请输入部门" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column prop="shiftDate" label="班次日期" width="110" />
        <el-table-column prop="shiftType" label="班次类型" width="90">
          <template #default="{ row }">
            <el-tag :type="shiftTagType(row.shiftType)">{{ row.shiftType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="empNo" label="工号" width="90" />
        <el-table-column prop="empName" label="姓名" width="90" />
        <el-table-column prop="gender" label="性别" width="65" />
        <el-table-column prop="age" label="年龄" width="65" />
        <el-table-column prop="department" label="部门" width="100" />
        <el-table-column prop="position" label="职位" width="100" />
        <el-table-column label="最新心率" width="120">
          <template #default="{ row }">
            <span v-if="row.latestHeartRate" :class="row.heartRateStatus === '异常' ? 'text-danger' : 'text-normal'">
              {{ row.latestHeartRate }} 次/分
            </span>
            <span v-else class="text-muted">暂无数据</span>
          </template>
        </el-table-column>
        <el-table-column label="心率状态" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.heartRateStatus" :type="row.heartRateStatus === '异常' ? 'danger' : 'success'">
              {{ row.heartRateStatus }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="异常次数" width="90">
          <template #default="{ row }">
            <el-badge v-if="row.abnormalCount > 0" :value="row.abnormalCount" type="danger">
              <el-icon color="#f56c6c"><Warning /></el-icon>
            </el-badge>
            <span v-else>0</span>
          </template>
        </el-table-column>
        <el-table-column label="最新告警等级" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.latestAlertLevel" :type="row.latestAlertLevel === '危险' ? 'danger' : 'warning'">
              {{ row.latestAlertLevel }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="处理状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.latestHandleStatus" :type="row.latestHandleStatus === '已处理' ? 'success' : 'info'">
              {{ row.latestHandleStatus }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="startTime" label="上班时间" width="170" />
      </el-table>

      <!-- 分页 -->
      <el-pagination
        class="pagination"
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadData"
        @size-change="loadData"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Warning } from '@element-plus/icons-vue'
import { dutyApi } from '../api/index'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)

const query = reactive({ shiftDate: '', shiftType: '', empName: '', department: '' })

const shiftTagType = (shiftType) => {
  if (shiftType === '早班') return 'success'
  if (shiftType === '中班') return 'warning'
  return 'info'
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (query.shiftDate) params.shiftDate = query.shiftDate
    if (query.shiftType) params.shiftType = query.shiftType
    if (query.empName) params.empName = query.empName
    if (query.department) params.department = query.department
    const res = await dutyApi.query(params)
    tableData.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { shiftDate: '', shiftType: '', empName: '', department: '' })
  page.value = 1
  loadData()
}

loadData()
</script>

<style scoped>
.page-container { padding: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.search-form { margin-bottom: 10px; }
.pagination { margin-top: 15px; display: flex; justify-content: flex-end; }
.text-danger { color: #f56c6c; font-weight: bold; }
.text-normal { color: #67c23a; }
.text-muted { color: #909399; }
</style>
