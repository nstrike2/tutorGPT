import React, { useState } from 'react'
import { sendMessage } from '../utils/api'
import Message from './Message'
import '../styles/App.css'
/**
 * Reflow text to a maximum line length, but do NOT split sentences.
 * - We split the text into sentences using a naive regex for punctuation (".", "?", "!").
 * - Then we accumulate sentences onto a line until adding the next sentence
 *   would exceed `maxLen`, at which point we insert a carriage return and continue.
 * - If a single sentence is longer than maxLen, we keep it intact on one line anyway
 *   (to avoid mid-sentence breaks).
 */
function reflowTextNoSplit (text, maxLen = 300) {
  // Match sentences by capturing them with trailing punctuation, or leftover text
  // Example: "Hello world. This is a test? Yes!"
  // will produce ["Hello world.", "This is a test?", "Yes!"]
  // If there's leftover text without punctuation, it appears as a final item.
  const sentences = text.match(/[^.!?]+[.!?]+|\S+$/g) || []

  let result = ''
  let currentLineLen = 0

  for (let i = 0; i < sentences.length; i++) {
    const sentence = sentences[i].trim()
    // If the next sentence won't fit on this line, insert a newline,
    // except if the current line is empty (we don't want infinite newlines).
    if (currentLineLen + sentence.length > maxLen && currentLineLen > 0) {
      result += '\n'
      currentLineLen = 0
    }
    // Add the sentence + space to result
    result += sentence + ' '
    currentLineLen += sentence.length + 1
  }

  return result.trim()
}

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
      const assistantMessage = response.data.assistant_message // entire AI response

      // 4) Insert line breaks AFTER sentences without splitting them
      const reflowed = reflowTextNoSplit(assistantMessage, 300)

      // 5) Create the assistant message (one bubble, but with line breaks)
      const newAssistantMessage = {
        role: 'assistant',
        content: reflowed,
        userInput: userMessage.content,
        assistantOutput: assistantMessage,
        id: `msg-${Date.now()}-assistant`
      }

      // 6) Append the assistant message as a single bubble
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
