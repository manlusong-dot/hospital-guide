<template>
  <div>
    <div class="page-toolbar">
      <el-select v-model="filterCategory" placeholder="全部分类" clearable style="width: 180px" @change="onFilter">
        <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
      </el-select>
      <el-input v-model="keyword" placeholder="搜索标题 / 内容" clearable style="width: 220px" :prefix-icon="Search" @input="onFilter" />
      <div class="spacer"></div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增常识</el-button>
    </div>

    <el-table :data="paginated" border stripe>
      <el-table-column prop="category" label="分类" width="130" align="center">
        <template #default="{ row }">
          <el-tag size="small" effect="plain">{{ row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="160" />
      <el-table-column prop="content" label="内容" min-width="320" show-overflow-tooltip />
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑用药常识' : '新增用药常识'" width="540px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="70px">
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category" style="width: 100%" allow-create filterable>
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="5" />
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
const categories = computed(() => [...new Set(data.medicineGuide.map((m) => m.category))].sort())
const filterCategory = ref(null)
const keyword = ref('')

const filtered = computed(() => {
  let list = data.medicineGuide
  if (filterCategory.value) list = list.filter((m) => m.category === filterCategory.value)
  if (keyword.value.trim()) {
    const kw = keyword.value.trim()
    list = list.filter((m) => m.title.includes(kw) || m.content.includes(kw))
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

const emptyForm = () => ({ id: '', category: '用药安全', title: '', content: '' })
const form = reactive(emptyForm())

const rules = {
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
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
    data.updateMedicine({ ...form })
    ElMessage.success('常识已更新')
  } else {
    data.addMedicine({ ...form })
    ElMessage.success('常识已新增')
  }
  dialogVisible.value = false
}

async function onRemove(row) {
  await ElMessageBox.confirm(`确定删除「${row.title}」吗？`, '删除确认', { type: 'warning' })
  data.removeMedicine(row.id)
  ElMessage.success('已删除')
}
</script>
