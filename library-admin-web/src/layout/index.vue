<template>
  <div class="layout">
    <aside class="sidebar" :class="{ collapsed: app.collapsed }">
      <div class="logo">
        <div class="logo-icon">
          <el-icon :size="20"><Collection /></el-icon>
        </div>
        <span v-show="!app.collapsed">图书管理系统</span>
      </div>
      <el-menu
        class="menu"
        :default-active="$route.path"
        :collapse="app.collapsed"
        :collapse-transition="false"
        router
      >
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <template #title>{{ m.title }}</template>
        </el-menu-item>
      </el-menu>
      <div v-show="!app.collapsed" class="copyright">© 2026 Library Admin</div>
    </aside>

    <div class="right">
      <header class="header">
        <div class="header-left">
          <el-icon class="icon-btn" :size="18" @click="app.toggleSidebar()">
            <Expand v-if="app.collapsed" />
            <Fold v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="$route.path !== '/dashboard'">
              {{ $route.meta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-popover placement="bottom-end" :width="320" trigger="click">
            <template #reference>
              <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="icon-btn">
                <el-icon :size="18"><Bell /></el-icon>
              </el-badge>
            </template>
            <div class="notify-panel">
              <div class="notify-header">
                <span>通知消息</span>
                <el-link type="primary" :underline="false" @click="markAllRead">全部已读</el-link>
              </div>
              <div
                v-for="n in notifications"
                :key="n.id"
                class="notify-item"
                :class="{ read: n.read }"
                @click="markRead(n)"
              >
                <span class="notify-dot" />
                <div class="notify-content">
                  <div class="notify-title">{{ n.title }}</div>
                  <div class="notify-time">{{ n.time }}</div>
                </div>
              </div>
            </div>
          </el-popover>
          <el-icon class="icon-btn" :size="18" @click="toggleFullscreen">
            <FullScreen />
          </el-icon>
          <el-dropdown trigger="click" @command="onCommand">
            <div class="user">
              <el-avatar :size="30" class="user-avatar">{{ userName[0] }}</el-avatar>
              <span class="user-name">{{ userName }}</span>
              <el-icon :size="14"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'

const app = useAppStore()
const router = useRouter()
const userName = computed(() => app.userName)

/* 窄屏自动折叠侧边栏 */
function onResize() {
  const isNarrow = window.innerWidth <= 768
  if (isNarrow && !app.collapsed) app.toggleSidebar()
  else if (!isNarrow && app.collapsed) app.toggleSidebar()
}
onMounted(() => {
  onResize()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => window.removeEventListener('resize', onResize))

const notifications = ref([
  { id: 1, title: '系统更新：图书管理系统已升级至 v1.0', time: '10 分钟前', read: false },
  { id: 2, title: '你有新的借阅申请待处理', time: '1 小时前', read: false },
  { id: 3, title: '库存预警：3 本图书库存不足', time: '今天 09:30', read: false },
])
const unreadCount = computed(() => notifications.value.filter((n) => !n.read).length)

function markRead(n) {
  n.read = true
}

function markAllRead() {
  notifications.value.forEach((n) => (n.read = true))
}

const menus = [
  { path: '/dashboard', title: '数据大屏', icon: 'DataAnalysis' },
  { path: '/book', title: '图书管理', icon: 'Reading' },
  { path: '/borrow', title: '图书借阅', icon: 'Tickets' },
  { path: '/author', title: '作者管理', icon: 'EditPen' },
  { path: '/publisher', title: '出版社管理', icon: 'OfficeBuilding' },
]

function toggleFullscreen() {
  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    document.documentElement.requestFullscreen()
  }
}

function onCommand(cmd) {
  if (cmd === 'logout') {
    localStorage.removeItem('library_token')
    localStorage.removeItem('library_user')
    router.push('/login')
  }
}
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ---------- 侧边栏 ---------- */
.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--white);
  border-right: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease-in-out;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 64px;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  border-bottom: 1px solid var(--gray-200);
  white-space: nowrap;
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, #4f6bff, #8b5cf6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.logo span {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-900);
}

.menu {
  flex: 1;
  border-right: none;
  padding: 8px;
  --el-menu-bg-color: transparent;
  --el-menu-hover-bg-color: var(--gray-100);
}

.menu :deep(.el-menu-item) {
  height: 44px;
  line-height: 44px;
  border-radius: 8px;
  margin: 4px 0;
  color: var(--gray-700);
}

.menu :deep(.el-menu-item:hover) {
  background: var(--gray-100);
}

.menu :deep(.el-menu-item.is-active) {
  background: var(--brand-primary-light);
  color: var(--brand-primary);
  font-weight: 500;
}

.copyright {
  padding: 16px;
  font-size: 12px;
  color: var(--gray-400);
  text-align: center;
  white-space: nowrap;
}

/* ---------- 右侧 ---------- */
.right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.header {
  height: 64px;
  flex-shrink: 0;
  background: var(--white);
  box-shadow: var(--shadow-header);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.icon-btn {
  color: var(--gray-500);
  cursor: pointer;
  transition: color 0.15s;
}

.icon-btn:hover {
  color: var(--brand-primary);
}

.user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--gray-700);
  outline: none;
}

.user-avatar {
  background: var(--brand-primary);
  font-size: 13px;
}

.user-name {
  font-size: 14px;
}

.main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  background: var(--gray-50);
}

/* ---------- 通知面板 ---------- */
.notify-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-900);
  padding-bottom: 10px;
  border-bottom: 1px solid var(--gray-200);
}

.notify-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 4px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.15s;
}

.notify-item:hover {
  background: var(--gray-100);
}

.notify-item + .notify-item {
  border-top: 1px solid var(--gray-200);
}

.notify-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
  margin-top: 6px;
  flex-shrink: 0;
}

.notify-item.read .notify-dot {
  background: var(--gray-300);
}

.notify-title {
  font-size: 13px;
  color: var(--gray-900);
  line-height: 1.5;
}

.notify-item.read .notify-title {
  color: var(--gray-400);
}

.notify-time {
  font-size: 12px;
  color: var(--gray-400);
  margin-top: 2px;
}

/* ---------- 移动端适配 ---------- */
@media (max-width: 768px) {
  .sidebar {
    width: 64px;
  }
  .logo span,
  .copyright,
  .user-name,
  .el-breadcrumb {
    display: none !important;
  }
  .header {
    padding: 0 12px;
    gap: 8px;
  }
  .header-right {
    gap: 12px;
  }
}
</style>
