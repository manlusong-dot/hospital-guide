<template>
  <div>
    <div class="page-toolbar">
      <el-select v-model="filterFloor" placeholder="全部楼层" clearable style="width: 130px" @change="onFilter">
        <el-option v-for="f in floors" :key="f" :label="`${f}F 楼`" :value="f" />
      </el-select>
      <el-select v-model="filterCategory" placeholder="全部类别" clearable style="width: 150px" @change="onFilter">
        <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
      </el-select>
      <el-input v-model="keyword" placeholder="搜索科室名称 / 别名" clearable style="width: 220px" :prefix-icon="Search" @input="onFilter" />
      <div class="spacer"></div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增科室</el-button>
    </div>

    <el-table :data="paginated" border stripe>
      <el-table-column prop="id" label="编号" width="90" />
      <el-table-column prop="name" label="科室名称" min-width="150" />
      <el-table-column label="楼层" width="90" align="center">
        <template #default="{ row }">
          <el-tag size="small" type="info" class="tag-floor">{{ row.floor }}F</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="类别" width="110" align="center">
        <template #default="{ row }">
          <el-tag size="small" effect="plain">{{ row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="nav_node_id" label="导航节点" width="150" />
      <el-table-column prop="intro" label="简介" min-width="200" show-overflow-tooltip />
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑科室' : '新增科室'" width="620px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="科室名称" prop="name">
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="楼层" prop="floor">
              <el-select v-model="form.floor" style="width: 100%">
                <el-option v-for="f in floors" :key="f" :label="`${f}F`" :value="f" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="类别" prop="category">
              <el-select v-model="form.category" style="width: 100%" allow-create filterable>
                <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="导航节点" prop="nav_node_id">
          <el-input v-model="form.nav_node_id" placeholder="如 1f_poi_fangshe" />
        </el-form-item>
        <el-form-item label="简介" prop="intro">
          <el-input v-model="form.intro" type="textarea" :rows="2" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="常见检查">
              <el-input v-model="form.common_exams" placeholder="逗号分隔" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="别名">
              <el-input v-model="form.aliases" placeholder="逗号分隔" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="就诊提示">
          <el-input v-model="form.tips" type="textarea" :rows="2" />
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

const floors = [1, 2, 3, 4]
const categories = computed(() => [...new Set(data.departments.map((d) => d.category))].sort())

const filterFloor = ref(null)
const filterCategory = ref(null)
const keyword = ref('')

const filtered = computed(() => {
  let list = data.departments
  if (filterFloor.value != null) list = list.filter((d) => d.floor === filterFloor.value)
  if (filterCategory.value) list = list.filter((d) => d.category === filterCategory.value)
  if (keyword.value.trim()) {
    const kw = keyword.value.trim()
    list = list.filter(
      (d) => d.name.includes(kw) || (d.aliases || '').includes(kw) || (d.id || '').includes(kw)
    )
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

const emptyForm = () => ({
  id: '',
  name: '',
  floor: 1,
  category: '门诊',
  nav_node_id: '',
  intro: '',
  common_exams: '',
  tips: '',
  aliases: '',
})
const form = reactive(emptyForm())

const rules = {
  name: [{ required: true, message: '请输入科室名称', trigger: 'blur' }],
  floor: [{ required: true, message: '请选择楼层', trigger: 'change' }],
  category: [{ required: true, message: '请选择类别', trigger: 'change' }],
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
  const payload = { ...form }
  if (editingId.value) {
    data.updateDepartment(payload)
    ElMessage.success('科室已更新')
  } else {
    data.addDepartment(payload)
    ElMessage.success('科室已新增')
  }
  dialogVisible.value = false
}

async function onRemove(row) {
  await ElMessageBox.confirm(`确定删除科室「${row.name}」吗？`, '删除确认', { type: 'warning' })
  data.removeDepartment(row.id)
  ElMessage.success('已删除')
}
</script>
