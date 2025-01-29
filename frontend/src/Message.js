import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css' // <-- KaTeX CSS for math rendering

import Rating from './Rating'

function Message ({ message }) {
  const isUser = message.role === 'user'

  // We'll read these so we can pass them to the Rating component
  const userInput = message.userInput
  const assistantOutput = message.assistantOutput

  // Choose a className based on the user/assistant role
  const messageClass = isUser
    ? 'message userMessage'
    : 'message assistantMessage'

  return (
    <div className={messageClass}>
      {isUser ? (
        // For user messages, just show raw text
        <div className='messageContent'>{message.content}</div>
      ) : (
        // For assistant messages, render Markdown with math support
        <div className='messageContent'>
          <ReactMarkdown
            // Add remark and rehype plugins for math
            remarkPlugins={[remarkMath]}
            rehypePlugins={[rehypeKatex]}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      )}

      {/* Show the rating only for assistant messages */}
      {!isUser && (
        <Rating
          messageId={message.id}
          userInput={userInput}
          assistantOutput={assistantOutput}
        />
      )}
    </div>
  )
}

export default Message
