import { defineStore } from 'pinia'
import { ref } from 'vue'
import { uploadFiles, processBatch } from '@/api/cert'

export const useCertStore = defineStore('cert', () => {
  const batchId = ref('')
  const uploadedFiles = ref([])
  const processing = ref(false)
  const results = ref([])
  const stats = ref({ total: 0, success: 0, failed: 0 })
  const errors = ref([])
  const outputFile = ref('')

  async function upload(files) {
    const res = await uploadFiles(files)
    batchId.value = res.batch_id
    uploadedFiles.value = res.files
    return res
  }

  async function process(writeMode = 'overwrite', outputFilename = 'result_all', outputDir = '') {
    if (!batchId.value) throw new Error('请先上传文件')
    processing.value = true
    try {
      const hasPrevious = results.value.length > 0
      const res = await processBatch(batchId.value, writeMode, hasPrevious, outputFilename, outputDir)
      results.value = res.results || []
      // 追加模式下 results 包含全部数据，stats 反映全部结果数量
      stats.value = {
        total: results.value.length,
        success: res.success,
        failed: res.failed,
      }
      errors.value = res.errors || []
      outputFile.value = res.output_file || ''
      return res
    } finally {
      processing.value = false
    }
  }

  function reset() {
    batchId.value = ''
    uploadedFiles.value = []
    results.value = []
    stats.value = { total: 0, success: 0, failed: 0 }
    errors.value = []
    outputFile.value = ''
  }

  return {
    batchId, uploadedFiles, processing, results, stats, errors, outputFile,
    upload, process, reset,
  }
})
