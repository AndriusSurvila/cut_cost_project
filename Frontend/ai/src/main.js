import './assets/index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './Shared/Layouts/Layout.vue'
import router from './Shared/Routes/router'
import Alpine from 'alpinejs'
import ui from './Shared/ui/index'

const app = createApp(App)

router.afterEach((to) => {
  document.title = to.meta.title + ' - Nulaidukas' || 'Nulaidikas'
})

Object.entries(ui).forEach(([name, component]) => {
  app.component(name, component)
})

app.use(createPinia())
app.use(router)

app.mount('#app')

window.Alpine = Alpine
Alpine.start()
