<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <el-icon :size="36" color="#2563EB"><Document /></el-icon>
        <h2>比赛证书自动识别管理系统</h2>
        <p class="login-subtitle">PaddleOCR 驱动 · 支持 PDF / JPG / PNG / BMP / TIFF</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" size="large" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = ref({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  setTimeout(() => {
    const ok = userStore.login(form.value.username, form.value.password)
    loading.value = false
    if (ok) {
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error('用户名或密码错误')
    }
  }, 500)
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e0e7ff 0%, #f1f5f9 50%, #dbeafe 100%);
}
.login-card {
  width: 400px;
  background: #fff;
  border-radius: 12px;
  padding: 40px 36px 32px;
  box-shadow: 0 8px 32px rgba(37, 99, 235, 0.12);
  border: 1px solid #e2e8f0;
}
.login-header {
  text-align: center;
  margin-bottom: 32px;
  h2 {
    margin: 12px 0 8px;
    font-size: 22px;
    color: #1e293b;
    font-weight: 700;
  }
}
.login-subtitle {
  color: #94a3b8;
  font-size: 13px;
}

/* 覆盖浏览器自动填充的蓝色背景 */
:deep(input:-webkit-autofill),
:deep(input:-webkit-autofill:hover),
:deep(input:-webkit-autofill:focus),
:deep(input:-webkit-autofill:active) {
  -webkit-box-shadow: 0 0 0 1000px #fff inset !important;
  box-shadow: 0 0 0 1000px #fff inset !important;
  -webkit-text-fill-color: #1e293b !important;
  transition: background-color 5000s ease-in-out 0s;
}
</style>
