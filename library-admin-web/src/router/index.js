import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/login/index.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/register/index.vue'),
    meta: { title: '注册' },
  },
  {
    path: '/',
    component: () => import('../layout/index.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/dashboard/index.vue'),
        meta: { title: '数据大屏' },
      },
      {
        path: 'book',
        name: 'BookList',
        component: () => import('../views/book/index.vue'),
        meta: { title: '图书管理' },
      },
      {
        path: 'borrow',
        name: 'BorrowList',
        component: () => import('../views/borrow/index.vue'),
        meta: { title: '图书借阅' },
      },
      {
        path: 'author',
        name: 'AuthorList',
        component: () => import('../views/author/index.vue'),
        meta: { title: '作者管理' },
      },
      {
        path: 'publisher',
        name: 'PublisherList',
        component: () => import('../views/publisher/index.vue'),
        meta: { title: '出版社管理' },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('library_token')
  const publicPaths = ['/login', '/register']
  if (!publicPaths.includes(to.path) && !token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (publicPaths.includes(to.path) && token) {
    return { path: '/' }
  }
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · 图书管理系统` : '图书管理系统'
})

export default router
