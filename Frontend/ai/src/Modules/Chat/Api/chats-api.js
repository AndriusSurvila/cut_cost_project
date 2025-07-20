import { globalStore } from '@s'

export const chatsApi = () => {
  const global = globalStore()

  const getChats = async () => {
    try {
      const response = await fetch(`${global.app_url}/chats`)

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }
      
      return response.json()
    } catch (error) {
      console.error('Error fetching chats:', error)
      throw error
    }
  }

  const getChat = async (chatId) => {
    try {
      const response = await fetch(`${global.app_url}/chats/${chatId}`)
      if (!response.ok) {
        throw new Error('Network response was not ok')
      }
      return await response.json()
    } catch (error) {
      console.error('Error fetching chat:', error)
      throw error
    }
  }

  return {
    getChats,
    getChat,
  }
}
