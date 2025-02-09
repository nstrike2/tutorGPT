import React from 'react'
import ChatRat from './components/Chat'
import './styles/App.css'

function App () {
  return (
    <div className='appRoot'>
      <h1 className='appTitle'>TutorGPT: TA for CS109</h1>
      {/* Optional subtitle or tagline */}
      <p className='appSubtitle'>
        Your friendly course assistant for Probability for Computer Scientists
      </p>

      {/* Render the chat interface */}
      <ChatRat />
    </div>
  )
}

export default App
