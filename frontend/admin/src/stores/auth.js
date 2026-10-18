import { defineStore } from 'pinia'
import { useDataStore } from './data'

const TOKEN_KEY = 'hospital-admin-token'
const USER_KEY = 'hospital-admin-user'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: (() => {
      try {
        return JSON.parse(localStorage.getItem(USER_KEY)) || null
      } catch {
        return null
      }
    })(),
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
  },
  actions: {
    login(username, password) {
      const dataStore = useDataStore()
      const user = dataStore.users.find(
        (u) => u.username === username && u.password === password && u.status === '启用'
      )
      if (user) {
        this.token = 'admin-token-' + Date.now()
        this.user = { username: user.username, name: user.name, role: user.role }
        localStorage.setItem(TOKEN_KEY, this.token)
        localStorage.setItem(USER_KEY, JSON.stringify(this.user))
        return true
      }
      return false
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})
