import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    collapsed: false,
    userName: localStorage.getItem('library_user') || '管理员',
    isAdmin: localStorage.getItem('library_is_admin') === '1',
  }),
  actions: {
    toggleSidebar() {
      this.collapsed = !this.collapsed
    },
    setUser(name, isAdmin) {
      this.userName = name
      this.isAdmin = !!isAdmin
      localStorage.setItem('library_user', name)
      localStorage.setItem('library_is_admin', isAdmin ? '1' : '0')
    },
  },
})
