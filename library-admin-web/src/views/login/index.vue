<template>
  <div class="login-page">
    <div class="brand">
      <div class="brand-inner">
        <div class="brand-logo">
          <el-icon :size="30"><Collection /></el-icon>
        </div>
        <h1>Library Admin</h1>
        <p>现代化图书管理系统 · 让馆藏管理更高效</p>
      </div>
      <div class="circle c1"></div>
      <div class="circle c2"></div>
    </div>

    <div class="panel">
      <div class="login-card">
        <h2>欢迎回来</h2>
        <p class="sub">登录图书管理系统</p>
        <el-input
          v-model="username"
          size="large"
          placeholder="账号"
          :prefix-icon="User"
          class="field"
        />
        <el-input
          v-model="password"
          size="large"
          type="password"
          show-password
          placeholder="密码"
          :prefix-icon="Lock"
          class="field"
          @keyup.enter="doLogin"
        />
        <div class="row-between">
          <el-checkbox v-model="remember">记住我</el-checkbox>
          <el-link type="primary" :underline="false">忘记密码？</el-link>
        </div>
        <el-button type="primary" size="large" class="submit" :loading="loading" @click="doLogin">
          登 录
        </el-button>
        <p class="tip">
          没有账号？
          <el-link type="primary" :underline="false" @click="router.push('/register')">
            立即注册
          </el-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { mockLogin } from '../../api/index'
import { useAppStore } from '../../stores/app'

const route = useRoute()
const router = useRouter()
const app = useAppStore()

const username = ref('admin')
const password = ref('')
const remember = ref(true)
const loading = ref(false)

async function doLogin() {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    const res = await mockLogin(username.value, password.value)
    localStorage.setItem('library_token', res.token)
    app.setUser(res.user.name, res.isAdmin)
    router.push(route.query.redirect || '/')
  } catch (e) {
    ElMessage.error(e.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  height: 100vh;
}

/* 左侧品牌区 */
.brand {
  flex: 3;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #4f6bff 0%, #8b5cf6 100%);
  color: #fff;
  display: flex;
  align-items: center;
  padding: 0 8%;
}

.brand-inner {
  position: relative;
  z-index: 1;
}

.brand-logo {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
}

.brand h1 {
  font-size: 40px;
  letter-spacing: 1px;
  margin-bottom: 16px;
}

.brand p {
  font-size: 16px;
  opacity: 0.85;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.circle.c1 {
  width: 380px;
  height: 380px;
  right: -120px;
  top: -120px;
}

.circle.c2 {
  width: 240px;
  height: 240px;
  left: -80px;
  bottom: -80px;
}

/* 右侧登录卡片 */
.panel {
  flex: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gray-50);
}

.login-card {
  width: 380px;
  background: var(--white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-modal);
  padding: 40px;
}

.login-card h2 {
  font-size: 24px;
  color: var(--gray-900);
}

.sub {
  font-size: 13px;
  color: var(--gray-500);
  margin: 8px 0 28px;
}

.field {
  margin-bottom: 18px;
}

.row-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.submit {
  width: 100%;
  height: 44px;
  font-size: 15px;
  letter-spacing: 4px;
}

.tip {
  margin-top: 20px;
  text-align: center;
  font-size: 12px;
  color: var(--gray-400);
}

@media (max-width: 900px) {
  .brand {
    display: none;
  }
}
</style>
