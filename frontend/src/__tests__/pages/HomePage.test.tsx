import { render, screen, waitFor } from '@testing-library/react'
import HomePage from '@/app/page'

// Mock the components
jest.mock('@/components/Navigation', () => {
  return function MockNavigation() {
    return <nav data-testid="navigation">Mock Navigation</nav>
  }
})

jest.mock('@/components/notifications/NotificationBell', () => {
  return function MockNotificationBell() {
    return <div data-testid="notification-bell">Mock Notification Bell</div>
  }
})

describe('HomePage', () => {
  beforeEach(() => {
    // Mock fetch for API calls
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([]), // projects
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([]), // tasks
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([]), // recent results
      })
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  it('renders the main layout components', () => {
    render(<HomePage />)
    
    // Check if main layout components are present
    expect(screen.getByTestId('navigation')).toBeInTheDocument()
    expect(screen.getByTestId('notification-bell')).toBeInTheDocument()
  })

  it('displays the dashboard title', () => {
    render(<HomePage />)
    
    expect(screen.getByText('ダッシュボード')).toBeInTheDocument()
  })

  it('renders dashboard cards', async () => {
    render(<HomePage />)
    
    await waitFor(() => {
      // Check for dashboard sections
      expect(screen.getByText('プロジェクト')).toBeInTheDocument()
      expect(screen.getByText('実行中のタスク')).toBeInTheDocument()
      expect(screen.getByText('最近の結果')).toBeInTheDocument()
    })
  })

  it('displays statistics cards', async () => {
    render(<HomePage />)
    
    await waitFor(() => {
      // Check for statistics
      expect(screen.getByText('総プロジェクト数')).toBeInTheDocument()
      expect(screen.getByText('実行中タスク')).toBeInTheDocument()
      expect(screen.getByText('今日の結果')).toBeInTheDocument()
    })
  })

  it('handles loading state', () => {
    render(<HomePage />)
    
    // Should show loading indicators initially
    const loadingElements = screen.getAllByText(/読み込み中|Loading/)
    expect(loadingElements.length).toBeGreaterThan(0)
  })

  it('handles empty data state', async () => {
    render(<HomePage />)
    
    await waitFor(() => {
      // Should show empty state messages
      expect(screen.getByText('プロジェクトがありません')).toBeInTheDocument()
      expect(screen.getByText('実行中のタスクはありません')).toBeInTheDocument()
    })
  })

  it('displays charts when data is available', async () => {
    // Mock data with some content
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([
          { id: '1', name: 'Test Project', created_at: '2024-01-01' }
        ]),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([
          { id: '1', status: 'RUNNING', created_at: '2024-01-01' }
        ]),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([
          { id: '1', data: { title: 'Test' }, created_at: '2024-01-01' }
        ]),
      })

    render(<HomePage />)
    
    await waitFor(() => {
      // Check if charts are rendered
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })
  })

  it('handles API errors gracefully', async () => {
    // Mock API error
    global.fetch = jest.fn().mockRejectedValue(new Error('API Error'))

    render(<HomePage />)
    
    await waitFor(() => {
      // Should show error state or fallback content
      expect(screen.getByText('データの取得に失敗しました')).toBeInTheDocument()
    })
  })

  it('has proper accessibility structure', () => {
    render(<HomePage />)
    
    // Check for proper heading structure
    const mainHeading = screen.getByRole('heading', { level: 1 })
    expect(mainHeading).toBeInTheDocument()
    expect(mainHeading).toHaveTextContent('ダッシュボード')
    
    // Check for main content area
    const main = screen.getByRole('main')
    expect(main).toBeInTheDocument()
  })

  it('renders responsive layout', () => {
    render(<HomePage />)
    
    // Check if the layout has responsive classes
    const container = screen.getByRole('main')
    expect(container).toHaveClass('container', 'mx-auto', 'px-4')
  })
})
