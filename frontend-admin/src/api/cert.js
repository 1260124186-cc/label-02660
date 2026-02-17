import request from './request'

export function uploadFiles(files) {
  const formData = new FormData()
  files.forEach((f) => formData.append('files', f.raw || f))
  return request.post('/cert/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function processBatch(batchId, writeMode = 'overwrite', hasPrevious = false, outputFilename = 'result_all', outputDir = '') {
  const formData = new FormData()
  formData.append('batch_id', batchId)
  formData.append('write_mode', writeMode)
  formData.append('has_previous', hasPrevious ? 'true' : 'false')
  formData.append('output_filename', outputFilename)
  formData.append('output_dir', outputDir)
  return request.post('/cert/process', formData)
}

export function downloadResult(filename) {
  return `/api/cert/download/${filename}`
}

export function recognizeSingle(file) {
  const formData = new FormData()
  formData.append('file', file.raw || file)
  return request.post('/cert/recognize-single', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function deleteBatch(batchId) {
  return request.delete(`/cert/batch/${batchId}`)
}
