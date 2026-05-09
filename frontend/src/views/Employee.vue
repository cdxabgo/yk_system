<template>
  <div class="page-container">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="姓名">
          <el-input v-model="searchForm.name" placeholder="请输入姓名" clearable />
        </el-form-item>
        <el-form-item label="岗位">
          <el-input v-model="searchForm.job" placeholder="请输入岗位" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadList">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">职工信息列表</span>
          <el-button type="primary" :icon="Plus" @click="openAdd">新增职工</el-button>
        </div>
      </template>

      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="age" label="年龄" width="70" align="center" />
        <el-table-column prop="job" label="岗位" />
        <el-table-column prop="workingYears" label="工龄(年)" width="90" align="center" />
        <el-table-column prop="contactInformation" label="联系方式" />
        <el-table-column prop="createTime" label="录入时间" width="170" />
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
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

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入职工姓名" />
        </el-form-item>
        <el-form-item label="年龄" prop="age">
          <el-input-number v-model="form.age" :min="18" :max="80" style="width:100%" />
        </el-form-item>
        <el-form-item label="岗位" prop="job">
          <el-input v-model="form.job" placeholder="请输入岗位" />
        </el-form-item>
        <el-form-item label="工龄(年)" prop="workingYears">
          <el-input-number v-model="form.workingYears" :min="0" :max="50" style="width:100%" />
        </el-form-item>
        <el-form-item label="联系方式" prop="contactInformation">
          <el-input v-model="form.contactInformation" placeholder="请输入手机号/邮箱" />
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
import { Search, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { employeeApi } from '../api/index'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增职工')
const formRef = ref(null)

const searchForm = reactive({ name: '', job: '' })
const pagination = reactive({ page: 1, size: 10, total: 0 })
const form = reactive({
  id: null, name: '', age: 30, job: '', workingYears: 0, contactInformation: ''
})

const rules = {
  name: [{ required: true, message: '请输入职工姓名', trigger: 'blur' }]
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await employeeApi.list({
      page: pagination.page,
      size: pagination.size,
      name: searchForm.name || undefined,
      job: searchForm.job || undefined
    })
    tableData.value = res.data.list || []
    pagination.total = Number(res.data.total) || 0
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.name = ''
  searchForm.job = ''
  pagination.page = 1
  loadList()
}

const openAdd = () => {
  dialogTitle.value = '新增职工'
  Object.assign(form, { id: null, name: '', age: 30, job: '', workingYears: 0, contactInformation: '' })
  dialogVisible.value = true
}

const openEdit = (row) => {
  dialogTitle.value = '编辑职工'
  Object.assign(form, {
    id: row.id, name: row.name, age: row.age,
    job: row.job, workingYears: row.workingYears,
    contactInformation: row.contactInformation
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (form.id) {
        await employeeApi.update(form.id, form)
      } else {
        await employeeApi.add(form)
      }
      ElMessage.success('操作成功')
      dialogVisible.value = false
      loadList()
    } finally {
      submitLoading.value = false
    }
  })
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除职工「${row.name}」吗？`, '警告', { type: 'warning' })
  await employeeApi.delete(row.id)
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
</style>
