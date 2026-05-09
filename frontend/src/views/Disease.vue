<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="疾病名称">
          <el-input v-model="searchForm.diseaseName" placeholder="请输入疾病名称" clearable />
        </el-form-item>
        <el-form-item label="疾病类型">
          <el-input v-model="searchForm.diseaseType" placeholder="请输入疾病类型" clearable />
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
          <span class="card-title">疾病信息列表</span>
          <el-button type="primary" :icon="Plus" @click="openAdd">新增疾病</el-button>
        </div>
      </template>

      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="diseaseName" label="疾病名称" />
        <el-table-column prop="diseaseType" label="疾病类型">
          <template #default="{ row }">
            <el-tag v-if="row.diseaseType" type="warning">{{ row.diseaseType }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="460px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="疾病名称" prop="diseaseName">
          <el-input v-model="form.diseaseName" placeholder="如：高血压、糖尿病" />
        </el-form-item>
        <el-form-item label="疾病类型" prop="diseaseType">
          <el-input v-model="form.diseaseType" placeholder="如：慢性病、心血管疾病、职业病" />
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
import { diseaseApi } from '../api/index'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增疾病')
const formRef = ref(null)

const searchForm = reactive({ diseaseName: '', diseaseType: '' })
const pagination = reactive({ page: 1, size: 10, total: 0 })
const form = reactive({ id: null, diseaseName: '', diseaseType: '' })

const rules = {
  diseaseName: [{ required: true, message: '请输入疾病名称', trigger: 'blur' }]
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await diseaseApi.list({
      page: pagination.page,
      size: pagination.size,
      diseaseName: searchForm.diseaseName || undefined,
      diseaseType: searchForm.diseaseType || undefined
    })
    tableData.value = res.data.list || []
    pagination.total = Number(res.data.total) || 0
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.diseaseName = ''
  searchForm.diseaseType = ''
  pagination.page = 1
  loadList()
}

const openAdd = () => {
  dialogTitle.value = '新增疾病'
  Object.assign(form, { id: null, diseaseName: '', diseaseType: '' })
  dialogVisible.value = true
}

const openEdit = (row) => {
  dialogTitle.value = '编辑疾病'
  Object.assign(form, { id: row.id, diseaseName: row.diseaseName, diseaseType: row.diseaseType })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (form.id) {
        await diseaseApi.update(form.id, form)
      } else {
        await diseaseApi.add(form)
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
  await ElMessageBox.confirm(`确定删除疾病「${row.diseaseName}」吗？`, '警告', { type: 'warning' })
  await diseaseApi.delete(row.id)
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
