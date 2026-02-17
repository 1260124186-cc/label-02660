<template>
  <div class="cert-page">
    <!-- 页面导航 -->
    <div class="page-nav">
      <el-menu mode="horizontal" :default-active="activeTab" @select="activeTab = $event">
        <el-menu-item index="upload">
          <el-icon><Upload /></el-icon>上传识别
        </el-menu-item>
        <el-menu-item index="result" :disabled="!hasResults">
          <el-icon><DataAnalysis /></el-icon>识别结果
        </el-menu-item>
      </el-menu>
    </div>

    <!-- 上传识别 -->
    <div v-show="activeTab === 'upload'">
      <!-- 上传区域 -->
      <div class="card">
        <div class="card-title">
          <el-icon><FolderOpened /></el-icon>上传证书文件
          <div class="title-actions">
            <el-button type="primary" size="small" @click="selectFolder">
              选择文件夹
            </el-button>
          </div>
        </div>
        <!-- 隐藏的文件夹选择 input -->
        <input
          ref="folderInputRef"
          type="file"
          webkitdirectory
          multiple
          style="display: none"
          accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.tif"
          @change="onFolderSelect"
        />
        <el-upload
          ref="uploadRef"
          class="upload-area"
          drag
          multiple
          :auto-upload="false"
          :on-change="onFileChange"
          :on-remove="onFileRemove"
          accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.tif"
        >
          <el-icon class="el-icon--upload" :size="48" color="#2563EB"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            将证书文件拖到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 PDF / JPG / PNG / BMP / TIFF 格式，可批量上传，也可点击上方按钮选择整个文件夹
            </div>
          </template>
        </el-upload>
        <!-- 文件夹选择后的文件列表 -->
        <div v-if="folderFiles.length > 0" class="folder-file-list">
          <div class="folder-header">
            <span>已从文件夹选择 {{ folderFiles.length }} 个文件</span>
            <el-button size="small" type="danger" link @click="clearFolderFiles">清除</el-button>
          </div>
          <div v-for="(f, idx) in folderFiles.slice(0, 10)" :key="idx" class="folder-file-item">
            {{ f.name }}
          </div>
          <div v-if="folderFiles.length > 10" class="folder-file-item" style="color: #94a3b8;">
            ... 还有 {{ folderFiles.length - 10 }} 个文件
          </div>
        </div>
      </div>

      <!-- 输出设置 -->
      <div class="card">
        <div class="card-title">
          <el-icon><Setting /></el-icon>输出设置
        </div>
        <el-form :model="form" label-width="100px">
          <el-form-item label="写入模式">
            <el-radio-group v-model="form.writeMode">
              <el-radio value="overwrite">覆盖写入</el-radio>
              <el-radio value="append">追加写入</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="输出文件名">
            <el-input
              v-model="form.outputFilename"
              placeholder="请输入输出文件名"
              style="max-width: 300px"
            >
              <template #append>.xlsx</template>
            </el-input>
          </el-form-item>
        </el-form>
      </div>

      <!-- 操作按钮 -->
      <div class="card action-card">
        <el-button
          type="success"
          size="large"
          :icon="CaretRight"
          :loading="certStore.processing"
          :disabled="totalFileCount === 0"
          @click="startProcess"
        >
          {{ certStore.processing ? '正在识别中...' : '开始整理' }}
        </el-button>
        <el-button
          size="large"
          :disabled="totalFileCount === 0"
          @click="resetAll"
        >
          重置
        </el-button>
        <span v-if="totalFileCount > 0" class="file-count">
          已选择 {{ totalFileCount }} 个文件
        </span>
      </div>
    </div>

    <!-- 识别结果 -->
    <div v-show="activeTab === 'result'">
      <div class="card">
        <div class="card-title">
          <el-icon><DataAnalysis /></el-icon>识别结果
          <div class="title-actions">
            <el-tag class="stat-tag" type="info">总计: {{ certStore.stats.total }}</el-tag>
            <el-tag class="stat-tag" type="success">成功: {{ certStore.stats.success }}</el-tag>
            <el-tag class="stat-tag" type="danger">失败: {{ certStore.stats.failed }}</el-tag>
            <el-button
              v-if="certStore.outputFile"
              type="primary"
              size="small"
              @click="downloadExcel"
            >
              下载 Excel
            </el-button>
          </div>
        </div>

        <el-table
          :data="certStore.results"
          stripe
          border
          style="width: 100%"
          max-height="500"
          empty-text="暂无识别结果"
        >
          <el-table-column prop="source_file" label="源文件" width="180" show-overflow-tooltip />
          <el-table-column prop="award_date" label="获奖时间" width="120" />
          <el-table-column prop="award_name" label="获奖名称" min-width="200" show-overflow-tooltip />
          <el-table-column prop="award_org" label="授奖单位" min-width="180" show-overflow-tooltip />
          <el-table-column prop="award_level" label="获奖等级" width="100" />
          <el-table-column prop="teachers" label="指导老师" width="140" show-overflow-tooltip />
          <el-table-column prop="students" label="获奖学生" width="140" show-overflow-tooltip />
          <el-table-column prop="confidence" label="置信度" width="90">
            <template #default="{ row }">
              <el-tag :type="row.confidence > 0.8 ? 'success' : row.confidence > 0.5 ? 'warning' : 'danger'" size="small">
                {{ (row.confidence * 100).toFixed(1) }}%
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 错误信息 -->
      <div v-if="certStore.errors.length > 0" class="card">
        <div class="card-title" style="color: #ef4444;">
          <el-icon><Warning /></el-icon>处理异常
        </div>
        <div v-for="(err, idx) in certStore.errors" :key="idx" class="error-item">
          ⚠ {{ err }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { CaretRight, Download } from '@element-plus/icons-vue'
import { useCertStore } from '@/stores/cert'
import { downloadResult } from '@/api/cert'

const VALID_EXTS = ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']

const certStore = useCertStore()
const uploadRef = ref(null)
const folderInputRef = ref(null)
const activeTab = ref('upload')
const fileList = ref([])
const folderFiles = ref([])

const form = ref({
  writeMode: 'overwrite',
  outputFilename: 'result_all',
})

const hasResults = computed(() => certStore.results.length > 0)
const totalFileCount = computed(() => fileList.value.length + folderFiles.value.length)

function onFileChange(file, list) {
  fileList.value = list
}

function onFileRemove(file, list) {
  fileList.value = list
}

function selectFolder() {
  folderInputRef.value.click()
}

function onFolderSelect(e) {
  const files = Array.from(e.target.files || [])
  const validFiles = files.filter(f => {
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    return VALID_EXTS.includes(ext)
  })
  if (validFiles.length === 0) {
    ElMessage.warning('所选文件夹中没有支持的证书文件')
    return
  }
  folderFiles.value = validFiles
  ElMessage.success(`已从文件夹选择 ${validFiles.length} 个证书文件`)
  // 重置 input 以便再次选择同一文件夹
  e.target.value = ''
}

function clearFolderFiles() {
  folderFiles.value = []
}

async function startProcess() {
  if (totalFileCount.value === 0) {
    ElMessage.warning('请先上传证书文件')
    return
  }

  try {
    // 合并两种来源的文件
    const allFiles = [
      ...fileList.value,
      ...folderFiles.value.map(f => ({ raw: f, name: f.name })),
    ]

    // 1. 上传
    ElMessage.info('正在上传文件...')
    await certStore.upload(allFiles)
    ElMessage.success(`已上传 ${certStore.uploadedFiles.length} 个文件`)

    // 2. 处理
    ElMessage.info('正在识别证书，请耐心等待...')
    const res = await certStore.process(form.value.writeMode, form.value.outputFilename)

    if (res.success > 0) {
      ElMessage.success(`识别完成！成功 ${res.success} 个，失败 ${res.failed} 个`)
      activeTab.value = 'result'
    } else {
      ElMessage.warning('未能成功识别任何证书，请检查文件格式或模板配置')
    }
  } catch (e) {
    ElMessage.error(`处理失败: ${e.message || e}`)
  }
}

function downloadExcel() {
  const url = downloadResult(certStore.outputFile)
  window.open(url, '_blank')
}

function resetAll() {
  certStore.reset()
  fileList.value = []
  folderFiles.value = []
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
  activeTab.value = 'upload'
  ElMessage.info('已重置')
}
</script>

<style lang="scss" scoped>
.cert-page {
  .action-card {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .file-count {
    color: #64748b;
    font-size: 13px;
  }
  .title-actions {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .error-item {
    color: #ef4444;
    font-size: 13px;
    padding: 4px 0;
    border-bottom: 1px solid #fef2f2;
  }
  .folder-file-list {
    margin-top: 12px;
    padding: 12px 16px;
    background: #f8fafc;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
  }
  .folder-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 13px;
    font-weight: 600;
    color: #475569;
  }
  .folder-file-item {
    font-size: 12px;
    color: #64748b;
    padding: 2px 0;
  }
}
</style>
