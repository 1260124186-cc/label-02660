import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listTemplates, getTemplate, createTemplate, createInteractiveTemplate, deleteTemplate } from '@/api/template'

export const useTemplateStore = defineStore('template', () => {
  const templates = ref([])
  const loading = ref(false)
  const currentTemplate = ref(null)

  async function fetchList() {
    loading.value = true
    try {
      const res = await listTemplates()
      templates.value = res.templates || []
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(name) {
    const res = await getTemplate(name)
    currentTemplate.value = res.template
    return res.template
  }

  async function save(data) {
    await createTemplate(data)
    await fetchList()
  }

  async function saveInteractive(data) {
    await createInteractiveTemplate(data)
    await fetchList()
  }

  async function remove(name) {
    await deleteTemplate(name)
    await fetchList()
  }

  return {
    templates, loading, currentTemplate,
    fetchList, fetchDetail, save, saveInteractive, remove,
  }
})
