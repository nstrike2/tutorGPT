import React from 'react'
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
      <div className='messageContent'>{message.content}</div>

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
