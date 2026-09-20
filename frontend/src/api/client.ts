import axios from 'axios'

export const api = axios.create({
  baseURL: '',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('fdq95_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }

  // ★★★ 关键修复：如果是 FormData，删除 Content-Type
  //     让浏览器自动补 multipart/form-data + boundary
  if (config.data instanceof FormData) {
    if (config.headers) {
      delete (config.headers as any)['Content-Type']
    }
  }

  return config
})

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const url = error.config?.url || ''
    const isAuthEndpoint =
      url.includes('/users/me') || url.includes('/auth/jwt/')
    if (error.response?.status === 401 && isAuthEndpoint) {
      localStorage.removeItem('fdq95_token')
    }
    return Promise.reject(error)
  }
)