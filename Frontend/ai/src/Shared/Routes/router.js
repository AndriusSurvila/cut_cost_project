import { createWebHistory, createRouter } from 'vue-router'

import Settings from '../Pages/Settings.vue'
import ShowChat from '@m/Chat/Pages/ShowChat.vue'

const routes = [
  { path: '/', component: ShowChat, meta: { title: 'Chat' } },
  { path: '/:id', component: ShowChat, name: 'chat', props: true, meta: { title: 'Chat' } },
  { path: '/settings', component: Settings, meta: { title: 'Settings' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
