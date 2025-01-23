import React, { useState } from 'react'
import { rateMessage } from './api'
import './Rating.css' // <-- Import a dedicated CSS file (or use App.css)

function Rating ({ messageId, userInput, assistantOutput }) {
  const [rating, setRating] = useState(null)

  const handleRate = async value => {
    setRating(value)
    try {
      await rateMessage(value, messageId, userInput, assistantOutput)
    } catch (error) {
      console.error('Error rating message:', error)
    }
  }

  return (
    <div className='ratingContainer'>
      <span
        className={`thumb thumbUp ${rating === 'up' ? 'active' : ''}`}
        onClick={() => handleRate('up')}
      >
        👍
      </span>
      <span
        className={`thumb thumbDown ${rating === 'down' ? 'active' : ''}`}
        onClick={() => handleRate('down')}
      >
        👎
      </span>
    </div>
  )
}

export default Rating
