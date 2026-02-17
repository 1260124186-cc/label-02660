<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <!-- 登录页不显示 header -->
      <template v-if="route.path === '/login'">
        <router-view />
      </template>
      <template v-else>
        <el-container>
          <el-header class="app-header">
            <div class="header-left">
              <el-icon :size="28" color="#2563EB"><Document /></el-icon>
              <span class="app-title">比赛证书自动识别管理系统</span>
            </div>
            <div class="header-right">
              <span class="header-desc">PaddleOCR 驱动 · 支持 PDF / JPG / PNG / BMP / TIFF</span>
              <el-dropdown trigger="click" @command="handleCommand">
                <div class="user-info">
                  <el-avatar :size="32" class="user-avatar">
                    {{ userStore.username?.charAt(0)?.toUpperCase() || 'U' }}
                  </el-avatar>
                  <span class="user-name">{{ userStore.username }}</span>
                  <el-icon :size="14"><ArrowDown /></el-icon>
                </div>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="logout">
                      <el-icon><SwitchButton /></el-icon>退出登录
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </el-header>
          <el-main class="app-main">
            <router-view />
          </el-main>
        </el-container>
      </template>
    </div>
  </el-config-provider>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

function handleCommand(cmd) {
  if (cmd === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style lang="scss" scoped>
.app-container {
  min-height: 100vh;
  background-color: #f1f5f9;
}
.app-header {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 60px;
  box-shadow: 0 2px 12px rgba(37, 99, 235, 0.3);
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.app-title {
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.2s;
  &:hover {
    background: rgba(255, 255, 255, 0.15);
  }
}
.user-avatar {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
  font-weight: 700;
  font-size: 14px;
}
.user-name {
  color: #fff;
  font-size: 14px;
  font-weight: 500;
}
.user-info .el-icon {
  color: rgba(255, 255, 255, 0.7);
}
.app-main {
  padding: 24px;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}
</style>
