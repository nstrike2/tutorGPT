// frontend/src/components/Chat.test.js
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Chat from './Chat'
import { sendMessage } from '../utils/api'

// Mock the API module so that actual API calls are not made during tests.
jest.mock('../utils/api')

describe('Chat Component', () => {
  beforeEach(() => {
    sendMessage.mockClear()
  })

  test('renders chat input and send button', () => {
    render(<Chat />)
    expect(
      screen.getByPlaceholderText(/Type your question/i)
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Send/i })).toBeInTheDocument()
  })

  test('sends message and displays assistant response', async () => {
    // Arrange: Set up the mocked sendMessage function to resolve with a fake response.
    sendMessage.mockResolvedValueOnce({
      data: { assistant_message: 'This is a test response' }
    })

    render(<Chat />)

    // Act: Simulate user typing a message and clicking the send button.
    const input = screen.getByPlaceholderText(/Type your question/i)
    const sendButton = screen.getByRole('button', { name: /Send/i })
    await userEvent.type(input, 'Hello')
    fireEvent.click(sendButton)

    // Assert: Verify that the user's message appears.
    expect(await screen.findByText('Hello')).toBeInTheDocument()
    // And that the assistant's response is eventually rendered.
    expect(
      await screen.findByText('This is a test response')
    ).toBeInTheDocument()
  })

  test('does nothing when input is empty', () => {
    render(<Chat />)
    const sendButton = screen.getByRole('button', { name: /Send/i })
    fireEvent.click(sendButton)
    // Expect no message to be added (assuming the component ignores empty input).
    expect(screen.queryByText('')).not.toBeInTheDocument()
  })
})
