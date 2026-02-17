/**
 * 简易 YAML 工具（仅用于前端展示，不做完整解析）
 */
export default {
  stringify(obj, indent = 2) {
    return JSON.stringify(obj, null, indent)
  },
}
