<template>
  <div>
    <div class="page-toolbar">
      <el-select v-model="filterFasting" placeholder="空腹要求" clearable style="width: 140px" @change="onFilter">
        <el-option label="需空腹" :value="1" />
        <el-option label="无需空腹" :value="0" />
      </el-select>
      <el-input v-model="keyword" placeholder="搜索检查名称" clearable style="width: 220px" :prefix-icon="Search" @input="onFilter" />
      <div class="spacer"></div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增须知</el-button>
    </div>

    <el-table :data="paginated" border stripe>
      <el-table-column prop="exam_name" label="检查名称" min-width="160" />
      <el-table-column label="空腹" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.fasting === 1 ? 'danger' : 'success'" size="small">
            {{ row.fasting === 1 ? '需空腹' : '无需' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="duration" label="预计时长" width="100" align="center" />
      <el-table-column prop="prep_text" label="准备要点" min-width="280" show-overflow-tooltip />
      <el-table-column prop="keywords" label="触发关键词" min-width="180" show-overflow-tooltip />
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑检查须知' : '新增检查须知'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="检查名称" prop="exam_name">
              <el-input v-model="form.exam_name" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="空腹" prop="fasting">
              <el-select v-model="form.fasting" style="width: 100%">
                <el-option label="需空腹" :value="1" />
                <el-option label="无需" :value="0" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="时长">
              <el-input v-model="form.duration" placeholder="约10分钟" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="准备要点" prop="prep_text">
          <el-input v-model="form.prep_text" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="form.keywords" placeholder="逗号分隔，用于导诊匹配" />
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
const filterFasting = ref(null)
const keyword = ref('')

const filtered = computed(() => {
  let list = data.examPrep
  if (filterFasting.value != null) list = list.filter((e) => e.fasting === filterFasting.value)
  if (keyword.value.trim()) {
    const kw = keyword.value.trim()
    list = list.filter((e) => e.exam_name.includes(kw) || (e.keywords || '').includes(kw))
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

const emptyForm = () => ({ id: '', exam_name: '', fasting: 0, duration: '', prep_text: '', keywords: '' })
const form = reactive(emptyForm())

const rules = {
  exam_name: [{ required: true, message: '请输入检查名称', trigger: 'blur' }],
  fasting: [{ required: true, message: '请选择空腹要求', trigger: 'change' }],
  prep_text: [{ required: true, message: '请填写准备要点', trigger: 'blur' }],
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
    data.updateExam({ ...form })
    ElMessage.success('须知已更新')
  } else {
    data.addExam({ ...form })
    ElMessage.success('须知已新增')
  }
  dialogVisible.value = false
}

async function onRemove(row) {
  await ElMessageBox.confirm(`确定删除「${row.exam_name}」吗？`, '删除确认', { type: 'warning' })
  data.removeExam(row.id)
  ElMessage.success('已删除')
}
</script>
