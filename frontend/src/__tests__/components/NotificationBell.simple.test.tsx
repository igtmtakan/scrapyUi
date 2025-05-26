import { render, screen } from '@testing-library/react'
import NotificationBell from '@/components/notifications/NotificationBell'

// Mock fetch
global.fetch = jest.fn()

describe('NotificationBell Simple Tests', () => {
  beforeEach(() => {
    // Reset fetch mock
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ unread_count: 0 }),
    })
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  it('renders notification bell', () => {
    render(<NotificationBell />)
    
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
  })

  it('has proper accessibility attributes', () => {
    render(<NotificationBell />)
    
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-label')
  })

  it('calls API on mount', () => {
    render(<NotificationBell />)
    
    expect(global.fetch).toHaveBeenCalled()
  })
})
