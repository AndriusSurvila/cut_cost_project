import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useChatStore = defineStore('chatStore', () => {
  const chats = ref([])
  const chat = ref({})

  return { chats, chat }
})
