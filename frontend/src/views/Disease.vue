<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>疾病信息管理</span>
          <el-button type="primary" @click="openAdd">新增疾病</el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="query" class="search-form">
        <el-form-item label="疾病名称">
          <el-input v-model="query.diseaseName" placeholder="请输入疾病名称" clearable />
        </el-form-item>
        <el-form-item label="等级">
          <el-select v-model="query.level" placeholder="请选择等级" clearable>
            <el-option label="轻微" value="轻微" />
            <el-option label="普通" value="普通" />
            <el-option label="严重" value="严重" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column prop="diseaseCode" label="疾病编码" width="120" />
        <el-table-column prop="diseaseName" label="疾病名称" width="150" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="level" label="等级" width="80">
          <template #default="{ row }">
            <el-tag :type="levelTagType(row.level)">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="170" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" destroy-on-close>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="疾病编码" prop="diseaseCode">
          <el-input v-model="form.diseaseCode" placeholder="请输入疾病编码" />
        </el-form-item>
        <el-form-item label="疾病名称" prop="diseaseName">
          <el-input v-model="form.diseaseName" placeholder="请输入疾病名称" />
        </el-form-item>
        <el-form-item label="等级" prop="level">
          <el-radio-group v-model="form.level">
            <el-radio label="轻微">轻微</el-radio>
            <el-radio label="普通">普通</el-radio>
            <el-radio label="严重">严重</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入疾病描述" />
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
import { diseaseApi } from '../api/index'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref(null)

const query = reactive({ diseaseName: '', level: '' })
const form = reactive({ id: null, diseaseCode: '', diseaseName: '', description: '', level: '普通' })

const rules = {
  diseaseCode: [{ required: true, message: '请输入疾病编码', trigger: 'blur' }],
  diseaseName: [{ required: true, message: '请输入疾病名称', trigger: 'blur' }],
  level: [{ required: true, message: '请选择等级', trigger: 'change' }]
}

const levelTagType = (level) => {
  if (level === '严重') return 'danger'
  if (level === '轻微') return 'success'
  return 'warning'
}

async function loadData() {
  loading.value = true
  try {
    const res = await diseaseApi.list({ page: page.value, size: size.value, ...query })
    tableData.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { diseaseName: '', level: '' })
  page.value = 1
  loadData()
}

function openAdd() {
  Object.assign(form, { id: null, diseaseCode: '', diseaseName: '', description: '', level: '普通' })
  dialogTitle.value = '新增疾病'
  dialogVisible.value = true
}

function openEdit(row) {
  Object.assign(form, { ...row })
  dialogTitle.value = '编辑疾病'
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  if (form.id) {
    await diseaseApi.update(form.id, form)
  } else {
    await diseaseApi.add(form)
  }
  ElMessage.success('操作成功')
  dialogVisible.value = false
  loadData()
}

async function handleDelete(id) {
  await ElMessageBox.confirm('确定删除该疾病信息吗？', '提示', { type: 'warning' })
  await diseaseApi.delete(id)
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
</style>
