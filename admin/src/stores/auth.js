import { ref } from 'vue'

const token = ref(localStorage.getItem('admin_token') || '')
const user = ref(JSON.parse(localStorage.getItem('admin_user') || 'null'))

export function useAuth() {
  function setAuth(t, u) {
    token.value = t
    user.value = u
    localStorage.setItem('admin_token', t)
    localStorage.setItem('admin_user', JSON.stringify(u))
  }

  function clearAuth() {
    token.value = ''
    user.value = null
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
  }

  function isLoggedIn() {
    return !!token.value
  }

  return { token, user, setAuth, clearAuth, isLoggedIn }
}
