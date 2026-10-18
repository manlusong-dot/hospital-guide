<template>
  <div class="login-page">
    <div class="login-hero">
      <div class="hero-badge">深圳大学医院 · AI 就医陪伴</div>
      <h1 class="hero-title">医院就医辅助系统</h1>
      <p class="hero-desc">面向中老年与儿童家长的全流程就医陪伴助手，智能导诊、院内导航、用药与检查须知。</p>
      <ul class="hero-features">
        <li><el-icon><Odometer /></el-icon>运行数据总览</li>
        <li><el-icon><OfficeBuilding /></el-icon>科室与医生管理</li>
        <li><el-icon><FirstAidKit /></el-icon>检查须知 · 用药常识</li>
      </ul>
    </div>

    <div class="login-panel">
      <div class="login-card">
        <div class="card-head">
          <div class="card-logo">
            <el-icon :size="22"><FirstAidKit /></el-icon>
          </div>
          <div class="card-title">管理端登录</div>
          <div class="card-sub">请使用管理员账号登录系统</div>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large" @submit.prevent="onSubmit">
          <el-form-item label="账号" prop="username">
            <el-input v-model="form.username" placeholder="请输入账号" :prefix-icon="User" clearable />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="onSubmit"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" class="login-btn" :loading="loading" native-type="submit">
              登 录
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-hint">
          <el-icon><InfoFilled /></el-icon>
          <span>演示账号：admin / admin123</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, InfoFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin123' })

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  setTimeout(() => {
    const ok = auth.login(form.username.trim(), form.password)
    loading.value = false
    if (ok) {
      ElMessage.success('登录成功')
      router.replace({ path: '/dashboard' })
    } else {
      ElMessage.error('账号或密码错误，请重试')
    }
  }, 400)
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.1fr 1fr;
}

.login-hero {
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(14, 116, 144, 0.55), transparent 60%),
    radial-gradient(1000px 500px at 110% 110%, rgba(16, 185, 129, 0.4), transparent 55%),
    linear-gradient(150deg, #0e1a2b, #0f2a3f 55%, #0e7490);
  color: #fff;
  padding: 64px 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.hero-badge {
  display: inline-block;
  align-self: flex-start;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 13px;
  color: #d7e8ee;
  margin-bottom: 22px;
}

.hero-title {
  font-size: 40px;
  font-weight: 700;
  letter-spacing: 1px;
  margin: 0 0 18px;
}

.hero-desc {
  font-size: 15px;
  line-height: 1.9;
  color: #b9cddc;
  max-width: 520px;
  margin: 0 0 32px;
}

.hero-features {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hero-features li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #dbe7ee;
}

.hero-features .el-icon {
  color: #10b981;
}

.login-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  padding: 32px;
}

.login-card {
  width: 360px;
  background: #fff;
  border-radius: 14px;
  padding: 36px 32px;
  box-shadow: 0 10px 40px rgba(15, 42, 63, 0.12);
}

.card-head {
  text-align: center;
  margin-bottom: 28px;
}

.card-logo {
  width: 52px;
  height: 52px;
  margin: 0 auto 14px;
  border-radius: 14px;
  background: linear-gradient(135deg, #0e7490, #10b981);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-title {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}

.card-sub {
  font-size: 13px;
  color: #9ca3af;
  margin-top: 6px;
}

.login-btn {
  width: 100%;
  margin-top: 6px;
}

.login-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 18px;
  font-size: 12px;
  color: #9ca3af;
  background: #f0fdf9;
  border-radius: 8px;
  padding: 9px;
  border: 1px solid #d1fae5;
}

.login-hint .el-icon {
  color: #10b981;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
  }
  .login-hero {
    display: none;
  }
}
</style>
