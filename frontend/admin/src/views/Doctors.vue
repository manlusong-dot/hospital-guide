<template>
  <div>
    <div class="page-toolbar">
      <el-select v-model="filterDept" placeholder="全部科室" clearable style="width: 200px" @change="onFilter">
        <el-option v-for="d in deptOptions" :key="d.id" :label="d.name" :value="d.id" />
      </el-select>
      <el-input v-model="keyword" placeholder="搜索医生姓名 / 简介" clearable style="width: 220px" :prefix-icon="Search" @input="onFilter" />
      <div class="spacer"></div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增医生</el-button>
    </div>

    <el-table :data="paginated" border stripe>
      <el-table-column prop="id" label="编号" width="90" />
      <el-table-column prop="name" label="姓名" width="110" />
      <el-table-column label="科室" width="150">
        <template #default="{ row }">
          <el-tag size="small" effect="plain">{{ deptName(row.dept_id) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="职称" width="120" />
      <el-table-column prop="schedule_text" label="出诊时间" width="170" />
      <el-table-column prop="intro" label="擅长" min-width="220" show-overflow-tooltip />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="onRemove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="[5, 10, 15]"
        :total="filtered.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="onPageChange"
        @current-change="onPageChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑医生' : '新增医生'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="科室" prop="dept_id">
          <el-select v-model="form.dept_id" style="width: 100%">
            <el-option v-for="d in deptOptions" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="职称" prop="title">
          <el-select v-model="form.title" style="width: 100%" allow-create filterable>
            <el-option v-for="t in titles" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="出诊时间">
          <el-input v-model="form.schedule_text" placeholder="如 周一/三/五 上午" />
        </el-form-item>
        <el-form-item label="擅长">
          <el-input v-model="form.intro" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { useDataStore } from '@/stores/data'

const data = useDataStore()
const titles = ['主任医师', '副主任医师', '主治医师', '住院医师']

const deptOptions = computed(() => data.departments.map((d) => ({ id: d.id, name: d.name })))

function deptName(id) {
  return data.departments.find((d) => d.id === id)?.name || id
}

const filterDept = ref(null)
const keyword = ref('')

const filtered = computed(() => {
  let list = data.doctors
  if (filterDept.value) list = list.filter((d) => d.dept_id === filterDept.value)
  if (keyword.value.trim()) {
    const kw = keyword.value.trim()
    list = list.filter((d) => d.name.includes(kw) || (d.intro || '').includes(kw))
  }
  return list
})

function onFilter() {
  currentPage.value = 1
}

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const paginated = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})
function onPageChange() {}

const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref()

const emptyForm = () => ({ id: '', name: '', dept_id: '', title: '主治医师', schedule_text: '', intro: '' })
const form = reactive(emptyForm())

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  dept_id: [{ required: true, message: '请选择科室', trigger: 'change' }],
  title: [{ required: true, message: '请选择职称', trigger: 'change' }],
}

function openCreate() {
  editingId.value = null
  Object.assign(form, emptyForm())
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, { ...row })
  dialogVisible.value = true
}

async function onSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  if (editingId.value) {
    data.updateDoctor({ ...form })
    ElMessage.success('医生信息已更新')
  } else {
    data.addDoctor({ ...form })
    ElMessage.success('医生已新增')
  }
  dialogVisible.value = false
}

async function onRemove(row) {
  await ElMessageBox.confirm(`确定删除医生「${row.name}」吗？`, '删除确认', { type: 'warning' })
  data.removeDoctor(row.id)
  ElMessage.success('已删除')
}
</script>
