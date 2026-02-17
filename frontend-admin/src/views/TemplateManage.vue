<template>
  <div class="template-page">
    <div class="page-nav">
      <el-menu mode="horizontal" :default-active="activeTab" @select="activeTab = $event">
        <el-menu-item index="list">
          <el-icon><List /></el-icon>模板列表
        </el-menu-item>
        <el-menu-item index="create">
          <el-icon><Plus /></el-icon>新建模板
        </el-menu-item>
        <el-menu-item index="interactive">
          <el-icon><Edit /></el-icon>交互式生成
        </el-menu-item>
      </el-menu>
    </div>

    <!-- 模板列表 -->
    <div v-show="activeTab === 'list'">
      <div class="card">
        <div class="card-title">
          <el-icon><Files /></el-icon>已有模板
          <div class="title-actions">
            <el-button type="primary" size="small" :icon="Refresh" @click="loadTemplates">刷新</el-button>
          </div>
        </div>
        <el-table :data="templateStore.templates" stripe border v-loading="templateStore.loading" empty-text="暂无模板">
          <el-table-column prop="name" label="名称" width="180" />
          <el-table-column prop="cert_type" label="类型" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ row.cert_type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="keywords" label="关键词" min-width="200">
            <template #default="{ row }">
              <el-tag v-for="kw in (row.keywords || []).slice(0, 5)" :key="kw" size="small" type="info" class="kw-tag">{{ kw }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="viewDetail(row.name)">查看</el-button>
              <el-popconfirm title="确定删除该模板？" @confirm="handleDelete(row.name)">
                <template #reference>
                  <el-button size="small" type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 模板详情弹窗 -->
      <el-dialog v-model="detailVisible" title="模板详情" width="650px">
        <pre class="yaml-preview">{{ detailYaml }}</pre>
      </el-dialog>
    </div>

    <!-- 新建模板 -->
    <div v-show="activeTab === 'create'">
      <div class="card">
        <div class="card-title">
          <el-icon><DocumentAdd /></el-icon>新建/编辑模板
        </div>
        <el-form :model="createForm" label-width="100px">
          <el-form-item label="模板名称" required>
            <el-input v-model="createForm.name" placeholder="英文名称，如 math_competition" />
          </el-form-item>
          <el-form-item label="证书类型">
            <el-select v-model="createForm.cert_type" style="width: 100%">
              <el-option v-for="t in typeOptions" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input v-model="createForm.keywordsStr" placeholder="逗号分隔，如：数学,竞赛,奥林匹克" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="createForm.description" placeholder="模板描述" />
          </el-form-item>
          <el-form-item label="YAML内容">
            <el-input
              v-model="createForm.yaml_content"
              type="textarea"
              :rows="12"
              placeholder="可选：粘贴完整 YAML 模板内容，留空则使用默认模板"
              style="font-family: Consolas, monospace;"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="success" :loading="saving" @click="handleCreate">保存模板</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 交互式生成 -->
    <div v-show="activeTab === 'interactive'">
      <div class="card">
        <div class="card-title">
          <el-icon><MagicStick /></el-icon>交互式生成模板
        </div>
        <el-form :model="interForm" label-width="100px">
          <el-form-item label="模板名称" required>
            <el-input v-model="interForm.name" placeholder="英文名称" />
          </el-form-item>
          <el-form-item label="证书类型">
            <el-select v-model="interForm.cert_type" style="width: 100%">
              <el-option v-for="t in typeOptions" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input v-model="interForm.keywordsStr" placeholder="逗号分隔" />
          </el-form-item>
        </el-form>
      </div>

      <div class="card">
        <div class="card-title">
          <el-icon><EditPen /></el-icon>字段正则配置
          <span style="font-weight: normal; font-size: 13px; color: #64748b; margin-left: 8px;">每行一个正则表达式</span>
        </div>
        <el-form label-width="100px">
          <el-form-item v-for="(label, key) in fieldLabels" :key="key" :label="label">
            <el-input
              v-model="interForm.fields[key]"
              type="textarea"
              :rows="2"
              :placeholder="`输入${label}的匹配正则，每行一个`"
              style="font-family: Consolas, monospace;"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="success" :loading="saving" @click="handleInteractive">生成并保存</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { useTemplateStore } from '@/stores/template'
import yaml from '@/utils/yaml-lite'

const templateStore = useTemplateStore()
const activeTab = ref('list')
const detailVisible = ref(false)
const detailYaml = ref('')
const saving = ref(false)

const typeOptions = ['general', 'math', 'science', 'language', 'sports', 'art', 'tech', 'other']

const fieldLabels = {
  award_date: '获奖日期',
  award_name: '获奖名称',
  award_org: '授奖单位',
  award_level: '获奖等级',
  teachers: '指导老师',
  students: '获奖学生',
}

const createForm = reactive({
  name: '',
  cert_type: 'general',
  keywordsStr: '',
  description: '',
  yaml_content: '',
})

const interForm = reactive({
  name: '',
  cert_type: 'general',
  keywordsStr: '',
  fields: {
    award_date: '',
    award_name: '',
    award_org: '',
    award_level: '',
    teachers: '',
    students: '',
  },
})

onMounted(() => {
  loadTemplates()
})

function loadTemplates() {
  templateStore.fetchList()
}

async function viewDetail(name) {
  try {
    const tpl = await templateStore.fetchDetail(name)
    detailYaml.value = JSON.stringify(tpl, null, 2)
    detailVisible.value = true
  } catch (e) {
    ElMessage.error('加载模板详情失败')
  }
}

async function handleDelete(name) {
  try {
    await templateStore.remove(name)
    ElMessage.success('模板已删除')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function handleCreate() {
  if (!createForm.name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  saving.value = true
  try {
    await templateStore.save({
      name: createForm.name.trim(),
      cert_type: createForm.cert_type,
      description: createForm.description,
      keywords: createForm.keywordsStr.split(',').map(s => s.trim()).filter(Boolean),
      yaml_content: createForm.yaml_content || null,
    })
    ElMessage.success('模板保存成功')
    activeTab.value = 'list'
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleInteractive() {
  if (!interForm.name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  saving.value = true
  try {
    const fieldConfigs = {}
    for (const [key, text] of Object.entries(interForm.fields)) {
      if (text.trim()) {
        fieldConfigs[key] = {
          patterns: text.split('\n').map(s => s.trim()).filter(Boolean),
        }
      }
    }
    await templateStore.saveInteractive({
      name: interForm.name.trim(),
      cert_type: interForm.cert_type,
      keywords: interForm.keywordsStr.split(',').map(s => s.trim()).filter(Boolean),
      field_configs: fieldConfigs,
    })
    ElMessage.success('模板已生成并保存')
    activeTab.value = 'list'
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
.template-page {
  .kw-tag {
    margin-right: 4px;
    margin-bottom: 2px;
  }
  .title-actions {
    margin-left: auto;
  }
  .yaml-preview {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 16px;
    font-family: Consolas, 'Courier New', monospace;
    font-size: 13px;
    max-height: 500px;
    overflow: auto;
    white-space: pre-wrap;
    word-break: break-all;
  }
}
</style>
