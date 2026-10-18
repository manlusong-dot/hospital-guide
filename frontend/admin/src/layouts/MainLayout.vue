<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="brand">
        <div class="brand-logo">
          <el-icon :size="20"><FirstAidKit /></el-icon>
        </div>
        <div class="brand-text">
          <div class="brand-title">就医辅助管理端</div>
          <div class="brand-sub">深圳大学医院</div>
        </div>
      </div>
      <el-menu
        :default-active="activePath"
        router
        class="nav-menu"
        background-color="transparent"
        text-color="#c7d2e3"
        active-text-color="#ffffff"
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">{{ currentTitle }}</div>
        <div class="spacer"></div>
        <el-dropdown trigger="click" @command="onCommand">
          <div class="user-box">
            <el-avatar :size="32" class="user-avatar">{{ avatarText }}</el-avatar>
            <span class="user-name">{{ auth.user?.name || '管理员' }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>
                {{ auth.user?.role || '' }} · {{ auth.user?.username || '' }}
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const menuItems = computed(() => {
  const layout = router.options.routes.find((r) => r.path === '/')
  const children = (layout?.children || []).filter((c) => c.meta?.title)
  return children.map((c) => ({
    path: '/' + c.path,
    title: c.meta.title,
    icon: c.meta.icon,
  }))
})

const activePath = computed(() => route.path)
const currentTitle = computed(() => route.meta.title || '')
const avatarText = computed(() => (auth.user?.name || '管').slice(0, 1))

async function onCommand(cmd) {
  if (cmd === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
    auth.logout()
    router.replace({ name: 'login' })
  }
}
</script>

<style scoped>
.layout {
  height: 100vh;
}

.aside {
  background: #0e1a2b;
  display: flex;
  flex-direction: column;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px;
}

.brand-logo {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: linear-gradient(135deg, #0e7490, #10b981);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-title {
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.2;
}

.brand-sub {
  color: #6d86a8;
  font-size: 12px;
  margin-top: 2px;
}

.nav-menu {
  border-right: none;
  flex: 1;
  padding: 6px 8px;
}

.nav-menu :deep(.el-menu-item) {
  height: 46px;
  border-radius: 8px;
  margin-bottom: 4px;
}

.nav-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #0e7490, #1288a5);
}

.nav-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
}

.header {
  background: #fff;
  border-bottom: 1px solid #eef2f6;
  display: flex;
  align-items: center;
  height: 60px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.spacer {
  flex: 1;
}

.user-box {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
}

.user-box:hover {
  background: #f3f4f6;
}

.user-avatar {
  background: #0e7490;
  font-size: 15px;
}

.user-name {
  font-size: 14px;
  color: #374151;
}

.main {
  padding: 20px;
  background: var(--page-bg);
  overflow-y: auto;
}
</style>
