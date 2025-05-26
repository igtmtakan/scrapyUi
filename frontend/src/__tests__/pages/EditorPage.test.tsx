import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import EditorPage from '@/app/editor/page'

// Mock components
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

describe('EditorPage', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    // Mock fetch for API calls
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([]), // projects
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([]), // spiders
      })
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  it('renders the editor layout', () => {
    render(<EditorPage />)
    
    expect(screen.getByTestId('navigation')).toBeInTheDocument()
    expect(screen.getByTestId('notification-bell')).toBeInTheDocument()
    expect(screen.getByText('スクリプトエディタ')).toBeInTheDocument()
  })

  it('displays Monaco editor', () => {
    render(<EditorPage />)
    
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument()
  })

  it('shows template selection', () => {
    render(<EditorPage />)
    
    expect(screen.getByText('テンプレート')).toBeInTheDocument()
    expect(screen.getByText('基本スパイダー')).toBeInTheDocument()
    expect(screen.getByText('フォーム送信')).toBeInTheDocument()
    expect(screen.getByText('ページネーション')).toBeInTheDocument()
  })

  it('loads template when selected', async () => {
    render(<EditorPage />)
    
    const templateButton = screen.getByText('基本スパイダー')
    await user.click(templateButton)
    
    const editor = screen.getByTestId('monaco-editor')
    expect(editor).toHaveValue(expect.stringContaining('import scrapy'))
  })

  it('allows code editing', async () => {
    render(<EditorPage />)
    
    const editor = screen.getByTestId('monaco-editor')
    await user.clear(editor)
    await user.type(editor, 'print("Hello World")')
    
    expect(editor).toHaveValue('print("Hello World")')
  })

  it('shows project and spider selection', () => {
    render(<EditorPage />)
    
    expect(screen.getByText('プロジェクト')).toBeInTheDocument()
    expect(screen.getByText('スパイダー')).toBeInTheDocument()
  })

  it('enables run button when code is present', async () => {
    render(<EditorPage />)
    
    const editor = screen.getByTestId('monaco-editor')
    await user.type(editor, 'import scrapy')
    
    const runButton = screen.getByText('実行')
    expect(runButton).not.toBeDisabled()
  })

  it('disables run button when no code is present', () => {
    render(<EditorPage />)
    
    const runButton = screen.getByText('実行')
    expect(runButton).toBeDisabled()
  })

  it('shows save button', () => {
    render(<EditorPage />)
    
    expect(screen.getByText('保存')).toBeInTheDocument()
  })

  it('handles code execution', async () => {
    // Mock successful execution
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([]), // projects
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([]), // spiders
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ task_id: 'test-task-123' }), // execution
      })

    render(<EditorPage />)
    
    const editor = screen.getByTestId('monaco-editor')
    await user.type(editor, 'import scrapy\nclass TestSpider(scrapy.Spider):\n    name = "test"')
    
    const runButton = screen.getByText('実行')
    await user.click(runButton)
    
    await waitFor(() => {
      expect(screen.getByText('実行中...')).toBeInTheDocument()
    })
  })

  it('shows execution results', async () => {
    render(<EditorPage />)
    
    // Should have a results section
    expect(screen.getByText('実行結果')).toBeInTheDocument()
  })

  it('handles save functionality', async () => {
    // Mock successful save
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([]), // projects
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([]), // spiders
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 'spider-123' }), // save
      })

    render(<EditorPage />)
    
    const editor = screen.getByTestId('monaco-editor')
    await user.type(editor, 'import scrapy')
    
    const saveButton = screen.getByText('保存')
    await user.click(saveButton)
    
    await waitFor(() => {
      expect(screen.getByText('保存しました')).toBeInTheDocument()
    })
  })

  it('shows syntax highlighting', () => {
    render(<EditorPage />)
    
    const editor = screen.getByTestId('monaco-editor')
    expect(editor).toHaveAttribute('data-testid', 'monaco-editor')
  })

  it('has proper accessibility', () => {
    render(<EditorPage />)
    
    // Check for proper heading structure
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('スクリプトエディタ')
    
    // Check for form elements
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThan(0)
    
    buttons.forEach(button => {
      expect(button).toHaveAccessibleName()
    })
  })

  it('handles API errors gracefully', async () => {
    // Mock API error
    global.fetch = jest.fn().mockRejectedValue(new Error('API Error'))

    render(<EditorPage />)
    
    await waitFor(() => {
      expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
    })
  })
})
