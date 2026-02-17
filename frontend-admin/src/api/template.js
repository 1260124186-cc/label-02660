import request from './request'

export function listTemplates() {
  return request.get('/template/list')
}

export function getTemplate(name) {
  return request.get(`/template/detail/${name}`)
}

export function createTemplate(data) {
  return request.post('/template/create', data)
}

export function createInteractiveTemplate(data) {
  return request.post('/template/create-interactive', data)
}

export function deleteTemplate(name) {
  return request.delete(`/template/${name}`)
}
