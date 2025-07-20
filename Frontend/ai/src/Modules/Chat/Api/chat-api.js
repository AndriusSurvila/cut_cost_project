import { globalStore } from '@s'

export const chatApi = () => {
  const global = globalStore()

  const createChat = async (chat) => {
    const response = await fetch(`${global.app_url}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(chat),
    })
    return await response.json()
  }

  return {
    getChatHistory,
    getChatHistoryByUser,
    createChat,
    updateChat,
  }
}
