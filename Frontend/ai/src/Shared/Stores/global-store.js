import { defineStore } from 'pinia'

export const globalStore = defineStore('global', () => {
  const app_url = import.meta.env.VITE_API_URL
  const app_name = import.meta.env.VITE_APP_NAME

  return { app_url, app_name }
})
