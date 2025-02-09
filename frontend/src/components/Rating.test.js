// frontend/src/components/Rating.test.js
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import Rating from './Rating'

describe('Rating Component', () => {
  test('calls onRate callback when a rating is clicked', () => {
    // Assume that the Rating component receives an onRate prop.
    const onRateMock = jest.fn()
    render(<Rating onRate={onRateMock} />)

    // For example, if the component renders a button for rating "1", click it.
    // Adjust the selector to match your implementation.
    const ratingButton = screen.getByRole('button', { name: /1/i })
    fireEvent.click(ratingButton)
    expect(onRateMock).toHaveBeenCalled()
  })
})
