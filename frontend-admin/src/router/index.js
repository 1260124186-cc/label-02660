import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    redirect: '/cert',
  },
  {
    path: '/cert',
    name: 'CertRecognition',
    component: () => import('@/views/CertRecognition.vue'),
    meta: { title: '证书识别' },
  },
  {
    path: '/template',
    name: 'TemplateManage',
    component: () => import('@/views/TemplateManage.vue'),
    meta: { title: '模板管理' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title
    ? `${to.meta.title} - 证书识别系统`
    : '证书识别系统'

  // 登录守卫
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
