<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="职工姓名">
          <el-input v-model="searchForm.name" placeholder="请输入姓名" clearable />
        </el-form-item>
        <el-form-item label="岗位">
          <el-input v-model="searchForm.job" placeholder="请输入岗位" clearable />
        </el-form-item>
        <el-form-item label="最新心率状态">
          <el-select v-model="searchForm.isAbnormal" clearable placeholder="全部" style="width:110px">
            <el-option label="正常" :value="0" />
            <el-option label="异常" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadList">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon style="vertical-align:middle;margin-right:6px"><DataAnalysis /></el-icon>
            班中职工心率监控
          </span>
          <el-button :icon="Refresh" @click="loadList">刷新</el-button>
        </div>
      </template>

      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="employeeId" label="职工ID" width="80" align="center" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="age" label="年龄" width="65" align="center" />
        <el-table-column prop="job" label="岗位" width="110" />
        <el-table-column prop="workingYears" label="工龄(年)" width="80" align="center" />
        <el-table-column prop="contactInformation" label="联系方式" width="140" />
        <el-table-column prop="latestHeartRate" label="最新心率" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.latestHeartRate !== null" :class="row.latestIsAbnormal ? 'rate-abnormal' : 'rate-normal'">
              {{ row.latestHeartRate }} 次/分
            </span>
            <span v-else class="rate-none">暂无数据</span>
          </template>
        </el-table-column>
        <el-table-column prop="latestCollectTime" label="采集时间" width="170" />
        <el-table-column prop="latestIsAbnormal" label="当前状态" width="90" align="center">
          <template #default="{ row }">
            <template v-if="row.latestHeartRate !== null">
              <el-tag :type="row.latestIsAbnormal ? 'danger' : 'success'">
                {{ row.latestIsAbnormal ? '⚠ 异常' : '✓ 正常' }}
              </el-tag>
            </template>
            <el-tag v-else type="info">无记录</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="心率统计" width="140" align="center">
          <template #default="{ row }">
            <span>共 {{ row.totalRecords }} 条</span>
            <el-tag v-if="row.abnormalCount > 0" type="danger" size="small" style="margin-left:4px">
              异常 {{ row.abnormalCount }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="已知疾病" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.diseaseCount > 0" type="warning">{{ row.diseaseCount }} 种</el-tag>
            <span v-else>无</span>
          </template>
        </el-table-column>
        <el-table-column prop="latestDeviceId" label="设备ID" width="100" />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, DataAnalysis, Refresh } from '@element-plus/icons-vue'
import { heartRateApi } from '../api/index'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ name: '', job: '', isAbnormal: null })
const pagination = reactive({ page: 1, size: 10, total: 0 })

const loadList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    if (searchForm.name) params.name = searchForm.name
    if (searchForm.job) params.job = searchForm.job
    if (searchForm.isAbnormal !== null && searchForm.isAbnormal !== '') params.isAbnormal = searchForm.isAbnormal
    const res = await heartRateApi.monitor(params)
    tableData.value = res.data.list
    pagination.total = Number(res.data.total)
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  Object.assign(searchForm, { name: '', job: '', isAbnormal: null })
  pagination.page = 1
  loadList()
}

onMounted(loadList)
</script>

<style scoped>
.search-card :deep(.el-card__body) { padding: 16px 20px 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--yk-text-primary);
}
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
.rate-abnormal { color: var(--yk-danger); font-weight: 700; font-size: 14px; }
.rate-normal { color: var(--yk-success); font-weight: 700; font-size: 14px; }
.rate-none { color: var(--yk-text-muted); font-size: 13px; }
</style>
