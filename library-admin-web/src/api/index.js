// ============================================================
// 真实 API 数据层（axios + 统一响应拆包）
// 导出函数与 api/mock.js 同名同签名，页面只需把 import 路径
// 从 '../../api/mock' 改为 '../../api/index' 即可切换数据源。
// ============================================================
import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
})

// 请求拦截：附带 token（登录/注册接口不带，避免过期 token 干扰认证）
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('library_token')
  const isAuthApi = (config.url || '').startsWith('/auth/')
  if (token && !isAuthApi) config.headers.Authorization = `Bearer ${token}`
  // ngrok 免费版会给浏览器请求返回提示页，携带该头可直接跳过，保证接口返回 JSON
  config.headers['ngrok-skip-browser-warning'] = '1'
  return config
})

// 清空本地登录态
function clearAuth() {
  localStorage.removeItem('library_token')
  localStorage.removeItem('library_user')
  localStorage.removeItem('library_is_admin')
}

// 响应拦截：拆包统一响应体 { code, message, data }
// 错误统一以 Error(message) 抛出，由各页面自行 ElMessage 提示（与 Mock 层行为一致）
http.interceptors.response.use(
  (res) => {
    const body = res.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 0) return body.data
      // 业务层返回"请先登录"（无 token 访问）时同样视为登录态失效
      if (body.message === '请先登录') clearAuth()
      throw new Error(body.message || '请求失败')
    }
    return body
  },
  (error) => {
    const status = error.response?.status
    const body = error.response?.data
    // 401：token 失效，清除本地登录态并跳转登录页
    if (status === 401) {
      clearAuth()
      const path = window.location.pathname
      if (path !== '/login' && path !== '/register') window.location.href = '/login'
    }
    throw new Error(body?.message || body?.detail || error.message || '网络异常')
  },
)

/* ---------------- 认证 ---------------- */

export function mockLogin(username, password) {
  return http.post('/auth/login', { username, password })
}

export function register(username, password) {
  return http.post('/auth/register', { username, password })
}

/* ---------------- 字典 / 选项 ---------------- */

export function getCategories() {
  return http.get('/dict/categories')
}

export function getCountries() {
  return http.get('/dict/countries')
}

export function getCities() {
  return http.get('/dict/cities')
}

export function getAuthorOptions(keyword = '') {
  return http.get('/options/authors', { params: { keyword } })
}

export function getPublisherOptions(keyword = '') {
  return http.get('/options/publishers', { params: { keyword } })
}

/* ---------------- 图书 ---------------- */

export function getBooks(q = {}) {
  return http.get('/books', { params: q })
}

export function createBook(payload) {
  return http.post('/books', payload)
}

export function updateBook(id, payload) {
  return http.put(`/books/${id}`, payload)
}

export function deleteBook(id) {
  return http.delete(`/books/${id}`)
}

/* ---------------- 借阅 ---------------- */

export function borrowBook(bookId) {
  return http.post(`/books/${bookId}/borrow`)
}

export function getBorrows(q = {}) {
  return http.get('/borrows', { params: q })
}

export function returnBorrow(id) {
  return http.post(`/borrows/${id}/return`)
}

/* ---------------- 作者 ---------------- */

export function getAuthors(q = {}) {
  return http.get('/authors', { params: q })
}

export function createAuthor(payload) {
  return http.post('/authors', payload)
}

export function updateAuthor(id, payload) {
  return http.put(`/authors/${id}`, payload)
}

export function deleteAuthor(id) {
  return http.delete(`/authors/${id}`)
}

/* ---------------- 出版社 ---------------- */

export function getPublishers(q = {}) {
  return http.get('/publishers', { params: q })
}

export function createPublisher(payload) {
  return http.post('/publishers', payload)
}

export function updatePublisher(id, payload) {
  return http.put(`/publishers/${id}`, payload)
}

export function deletePublisher(id) {
  return http.delete(`/publishers/${id}`)
}

/* ---------------- Dashboard ---------------- */

export function getDashboard() {
  return http.get('/dashboard')
}
