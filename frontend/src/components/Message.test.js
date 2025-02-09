// frontend/src/components/Message.test.js
import React from 'react'
import { render, screen } from '@testing-library/react'
import Message from './Message'

describe('Message Component', () => {
  test('displays the message content', () => {
    const message = { role: 'user', content: 'Test message', id: 'msg-1' }
    render(<Message message={message} />)
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })
})
