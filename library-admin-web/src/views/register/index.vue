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
        <h2>创建账号</h2>
        <p class="sub">注册图书管理系统账号</p>
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
          placeholder="密码（至少 6 位）"
          :prefix-icon="Lock"
          class="field"
        />
        <el-input
          v-model="confirmPassword"
          size="large"
          type="password"
          show-password
          placeholder="确认密码"
          :prefix-icon="Lock"
          class="field"
          @keyup.enter="doRegister"
        />
        <el-button type="primary" size="large" class="submit" :loading="loading" @click="doRegister">
          注 册
        </el-button>
        <p class="tip">
          已有账号？
          <el-link type="primary" :underline="false" @click="router.push('/login')">
            返回登录
          </el-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { register } from '../../api/index'

const router = useRouter()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)

async function doRegister() {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  if (password.value.length < 6) {
    ElMessage.warning('密码至少 6 位')
    return
  }
  if (password.value !== confirmPassword.value) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    await register(username.value, password.value)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (e) {
    ElMessage.error(e.message)
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

/* 右侧注册卡片 */
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
