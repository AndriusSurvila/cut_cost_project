import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
// import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@s': fileURLToPath(new URL('./src/Shared', import.meta.url)),
      '@m': fileURLToPath(new URL('./src/Modules', import.meta.url)),
    },
  },
})
