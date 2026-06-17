import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import ChatInterface from '../ChatInterface'
import * as api from '@/lib/api'

// Mock the API module
vi.mock('@/lib/api', () => ({
  chat: vi.fn(),
}))

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the welcome screen when no messages exist', () => {
    render(<ChatInterface />)
    expect(screen.getByText(/Welcome to CinemaRAG/i)).toBeInTheDocument()
    expect(screen.getByText(/Your AI-powered film discovery companion/i)).toBeInTheDocument()
  })

  it('sends a message and displays the AI response', async () => {
    const mockResponse = { response: 'This is a mocked AI response about Batman.' }
    vi.mocked(api.chat).mockResolvedValue(mockResponse)

    render(<ChatInterface />)

    const input = screen.getByPlaceholderText(/Search for a movie or ask a question/i)
    const sendButton = screen.getByRole('button')

    // Type a message
    fireEvent.change(input, { target: { value: 'Tell me about Batman' } })
    fireEvent.click(sendButton)

    // Check if user message appears
    expect(screen.getByText('Tell me about Batman')).toBeInTheDocument()

    // Check if loading state appears
    expect(screen.getByText(/CinemaRAG is analyzing the film archives/i)).toBeInTheDocument()

    // Wait for the AI response to appear
    await waitFor(() => {
      expect(screen.getByText('This is a mocked AI response about Batman.')).toBeInTheDocument()
    })

    // Verify the API was called correctly
    expect(api.chat).toHaveBeenCalledWith('Tell me about Batman')
    
    // Welcome screen should be gone
    expect(screen.queryByText(/Welcome to CinemaRAG/i)).not.toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    vi.mocked(api.chat).mockRejectedValue(new Error('API Error'))

    render(<ChatInterface />)

    const input = screen.getByPlaceholderText(/Search for a movie or ask a question/i)
    const sendButton = screen.getByRole('button')

    fireEvent.change(input, { target: { value: 'Trigger Error' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(screen.getByText(/Sorry, I'm having trouble connecting to the backend/i)).toBeInTheDocument()
    })
  })
})
