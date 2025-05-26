import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import NotificationBell from '@/components/notifications/NotificationBell'

// Mock the NotificationCenter component
jest.mock('@/components/notifications/NotificationCenter', () => {
  return function MockNotificationCenter({ isOpen, onClose }: any) {
    return isOpen ? (
      <div data-testid="notification-center">
        <button onClick={onClose}>Close</button>
        <div>Mock Notification Center</div>
      </div>
    ) : null
  }
})

describe('NotificationBell Component', () => {
  beforeEach(() => {
    // Reset fetch mock
    global.fetch = jest.fn()
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  it('renders notification bell icon', () => {
    render(<NotificationBell />)
    
    const bellButton = screen.getByRole('button')
    expect(bellButton).toBeInTheDocument()
    expect(bellButton).toHaveAttribute('aria-label', 'Notifications')
  })

  it('shows unread count when there are unread notifications', async () => {
    // Mock API response
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ unread_count: 5 }),
    })

    render(<NotificationBell />)
    
    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument()
    })
  })

  it('does not show count when there are no unread notifications', async () => {
    // Mock API response
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ unread_count: 0 }),
    })

    render(<NotificationBell />)
    
    await waitFor(() => {
      expect(screen.queryByText('0')).not.toBeInTheDocument()
    })
  })

  it('opens notification center when clicked', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ unread_count: 3 }),
    })

    render(<NotificationBell />)
    
    const bellButton = screen.getByRole('button')
    fireEvent.click(bellButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('notification-center')).toBeInTheDocument()
    })
  })

  it('closes notification center when close button is clicked', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ unread_count: 3 }),
    })

    render(<NotificationBell />)
    
    // Open notification center
    const bellButton = screen.getByRole('button')
    fireEvent.click(bellButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('notification-center')).toBeInTheDocument()
    })
    
    // Close notification center
    const closeButton = screen.getByText('Close')
    fireEvent.click(closeButton)
    
    await waitFor(() => {
      expect(screen.queryByTestId('notification-center')).not.toBeInTheDocument()
    })
  })

  it('handles API error gracefully', async () => {
    // Mock API error
    global.fetch = jest.fn().mockRejectedValueOnce(new Error('API Error'))

    render(<NotificationBell />)
    
    // Should not crash and should not show any count
    await waitFor(() => {
      expect(screen.queryByText(/\d+/)).not.toBeInTheDocument()
    })
  })

  it('updates count when notifications are marked as read', async () => {
    // Initial fetch
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unread_count: 5 }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unread_count: 3 }),
      })

    render(<NotificationBell />)
    
    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument()
    })

    // Simulate marking notifications as read by triggering a refetch
    // This would normally happen through the NotificationCenter component
    const bellButton = screen.getByRole('button')
    fireEvent.click(bellButton)
    
    // The count should update when the component refetches
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument()
    })
  })
})
