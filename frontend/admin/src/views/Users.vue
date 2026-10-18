<template>
  <div>
    <div class="page-toolbar">
      <el-select v-model="filterRole" placeholder="全部角色" clearable style="width: 170px" @change="onFilter">
        <el-option v-for="r in roles" :key="r" :label="r" :value="r" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="全部状态" clearable style="width: 130px" @change="onFilter">
        <el-option label="启用" value="启用" />
        <el-option label="禁用" value="禁用" />
      </el-select>
      <el-input v-model="keyword" placeholder="搜索账号 / 姓名" clearable style="width: 220px" :prefix-icon="Search" @input="onFilter" />
      <div class="spacer"></div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增用户</el-button>
    </div>

    <el-table :data="paginated" border stripe>
      <el-table-column prop="username" label="账号" width="150" />
      <el-table-column prop="name" label="姓名" min-width="140" />
      <el-table-column prop="role" label="角色" width="130" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="row.role === '超级管理员' ? 'danger' : 'primary'" effect="plain">
            {{ row.role }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === '启用' ? 'success' : 'info'">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="创建时间" width="130" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" :disabled="isProtected(row)" @click="onRemove(row)">删除</el-button>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑用户' : '新增用户'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" :disabled="!!editingId" placeholder="登录账号" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="登录密码" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="角色" prop="role">
              <el-select v-model="form.role" style="width: 100%">
                <el-option v-for="r in roles" :key="r" :label="r" :value="r" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="form.status" style="width: 100%" :disabled="isAdmin">
                <el-option label="启用" value="启用" />
                <el-option label="禁用" value="禁用" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
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
import { useAuthStore } from '@/stores/auth'

const data = useDataStore()
const auth = useAuthStore()
const roles = ['超级管理员', '运营管理员', '内容编辑']

const filterRole = ref(null)
const filterStatus = ref(null)
const keyword = ref('')

const filtered = computed(() => {
  let list = data.users
  if (filterRole.value) list = list.filter((u) => u.role === filterRole.value)
  if (filterStatus.value) list = list.filter((u) => u.status === filterStatus.value)
  if (keyword.value.trim()) {
    const kw = keyword.value.trim()
    list = list.filter((u) => u.username.includes(kw) || u.name.includes(kw))
  }
  return list
})

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const paginated = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})
function onFilter() {
  currentPage.value = 1
}
function onPageChange() {}

function isProtected(row) {
  return row.username === 'admin'
}

const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref()
const isAdmin = computed(() => editingId.value === 'admin')

const emptyForm = () => ({
  id: '',
  username: '',
  password: '',
  name: '',
  role: '运营管理员',
  status: '启用',
  createdAt: new Date().toISOString().slice(0, 10),
})
const form = reactive(emptyForm())

const rules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    {
      validator: (_, v, cb) => {
        if (!v) return cb()
        if (v.length < 3) return cb(new Error('账号至少 3 个字符'))
        if (!editingId.value && data.users.some((u) => u.username === v)) {
          return cb(new Error('该账号已存在'))
        }
        cb()
      },
      trigger: 'blur',
    },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
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
    data.updateUser({ ...form })
    ElMessage.success('用户已更新')
  } else {
    data.addUser({ ...form })
    ElMessage.success('用户已新增，可用于登录')
  }
  dialogVisible.value = false
}

async function onRemove(row) {
  await ElMessageBox.confirm(`确定删除用户「${row.username}」吗？`, '删除确认', { type: 'warning' })
  if (row.username === auth.user?.username) {
    ElMessage.warning('不能删除当前登录账号')
    return
  }
  data.removeUser(row.id)
  ElMessage.success('已删除')
}
</script>

<style scoped>
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
