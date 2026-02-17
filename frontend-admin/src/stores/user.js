import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const avatar = ref(localStorage.getItem('avatar') || '')

  function login(user, pass) {
    // 简易前端模拟登录（无后端接口）
    if (user === 'admin' && pass === 'admin123') {
      token.value = 'mock-token-' + Date.now()
      username.value = user
      avatar.value = ''
      localStorage.setItem('token', token.value)
      localStorage.setItem('username', username.value)
      localStorage.setItem('avatar', avatar.value)
      return true
    }
    return false
  }

  function logout() {
    token.value = ''
    username.value = ''
    avatar.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('avatar')
  }

  const isLoggedIn = () => !!token.value

  return { token, username, avatar, login, logout, isLoggedIn }
})
