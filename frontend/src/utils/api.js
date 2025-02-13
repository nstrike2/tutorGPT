import axios from 'axios'

const api = axios.create({
  baseURL: '/api'
})

export const sendMessage = async message => {
  return apiClient.post('/chat', { message })
}

export const rateMessage = async (
  rating,
  messageId,
  userInput,
  assistantOutput
) => {
  return apiClient.post('/rate', {
    rating,
    messageId,
    userInput,
    assistantOutput
  })
}
