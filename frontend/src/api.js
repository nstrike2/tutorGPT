import axios from 'axios'

const apiClient = axios.create({
  baseURL: 'http://localhost:5001/api' // or wherever your Flask app is
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
