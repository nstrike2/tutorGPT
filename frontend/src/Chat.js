import React, { useState } from 'react'
import { sendMessage } from './api'
import Message from './Message'
import './App.css' // <-- Import your CSS file so .chatContainer, etc. are recognized

function ChatRat () {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')

  const handleSend = async () => {
    if (!inputValue.trim()) return

    // 1) Create the user message object
    const userMessage = {
      role: 'user',
      content: inputValue,
      id: `msg-${Date.now()}-user`
    }

    // 2) Append user message to the conversation
    setMessages(prev => [...prev, userMessage])
    setInputValue('')

    try {
      // 3) Call backend
      const response = await sendMessage(inputValue)
      const assistantMessage = response.data.assistant_message

      // 4) Create the assistant message
      const newAssistantMessage = {
        role: 'assistant',
        content: assistantMessage,
        userInput: userMessage.content,
        assistantOutput: assistantMessage,
        id: `msg-${Date.now()}-assistant`
      }

      // 5) Append assistant message
      setMessages(prev => [...prev, newAssistantMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      // Optionally handle or display an error in the UI
    }
  }

  const handleKeyDown = e => {
    if (e.key === 'Enter') {
      handleSend()
    }
  }

  return (
    <div className='chatContainer'>
      <div className='messagesContainer'>
        {messages.map(msg => (
          <Message key={msg.id} message={msg} />
        ))}
      </div>
      <div className='inputContainer'>
        <input
          className='input'
          placeholder='Type your question...'
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button className='sendButton' onClick={handleSend}>
          Send
        </button>
      </div>
    </div>
  )
}

export default ChatRat
