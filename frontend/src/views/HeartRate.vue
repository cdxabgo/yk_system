<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>心率信息管理</span>
          <el-button type="primary" @click="openAdd">录入心率</el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="query" class="search-form">
        <el-form-item label="职工ID">
          <el-input v-model="query.empId" placeholder="请输入职工ID" clearable style="width:120px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="请选择状态" clearable>
            <el-option label="正常" value="正常" />
            <el-option label="异常" value="异常" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker v-model="query.startTime" type="datetime" placeholder="开始时间"
            value-format="YYYY-MM-DD HH:mm:ss" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker v-model="query.endTime" type="datetime" placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="empNo" label="工号" width="100" />
        <el-table-column prop="empName" label="姓名" width="100" />
        <el-table-column prop="department" label="部门" />
        <el-table-column prop="heartRate" label="心率(次/分)" width="120">
          <template #default="{ row }">
            <span :class="row.status === '异常' ? 'text-danger' : 'text-normal'">
              {{ row.heartRate }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="measureTime" label="测量时间" width="170" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === '异常' ? 'danger' : 'success'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
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

    <!-- 录入心率弹窗 -->
    <el-dialog v-model="dialogVisible" title="录入心率" width="450px" destroy-on-close>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="职工ID" prop="empId">
          <el-input-number v-model="form.empId" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="心率值" prop="heartRate">
          <el-input-number v-model="form.heartRate" :min="20" :max="300" style="width:100%" />
          <span class="unit">次/分钟</span>
        </el-form-item>
        <el-form-item label="测量时间" prop="measureTime">
          <el-date-picker v-model="form.measureTime" type="datetime" placeholder="请选择测量时间"
            value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio label="正常">正常</el-radio>
            <el-radio label="异常">异常</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { heartRateApi } from '../api/index'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const dialogVisible = ref(false)
const formRef = ref(null)

const query = reactive({ empId: '', status: '', startTime: '', endTime: '' })
const form = reactive({ empId: null, heartRate: 75, measureTime: '', status: '正常' })

const rules = {
  empId: [{ required: true, message: '请输入职工ID', trigger: 'blur' }],
  heartRate: [{ required: true, message: '请输入心率值', trigger: 'blur' }],
  measureTime: [{ required: true, message: '请选择测量时间', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (query.empId) params.empId = query.empId
    if (query.status) params.status = query.status
    if (query.startTime) params.startTime = query.startTime
    if (query.endTime) params.endTime = query.endTime
    const res = await heartRateApi.list(params)
    tableData.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { empId: '', status: '', startTime: '', endTime: '' })
  page.value = 1
  loadData()
}

function openAdd() {
  Object.assign(form, { empId: null, heartRate: 75, measureTime: '', status: '正常' })
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  await heartRateApi.add(form)
  ElMessage.success('录入成功')
  dialogVisible.value = false
  loadData()
}

async function handleDelete(id) {
  await ElMessageBox.confirm('确定删除该心率记录吗？', '提示', { type: 'warning' })
  await heartRateApi.delete(id)
  ElMessage.success('删除成功')
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
.unit { margin-left: 8px; color: #909399; }
</style>
