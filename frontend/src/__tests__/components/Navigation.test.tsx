import { render, screen } from '@testing-library/react'
import Navigation from '@/components/Navigation'

// Mock usePathname
jest.mock('next/navigation', () => ({
  usePathname: () => '/',
}))

describe('Navigation Component', () => {
  it('renders navigation items', () => {
    render(<Navigation />)

    // Check if main navigation items are present
    expect(screen.getByText('ダッシュボード')).toBeInTheDocument()
    expect(screen.getByText('エディタ')).toBeInTheDocument()
    expect(screen.getByText('監視')).toBeInTheDocument()
    expect(screen.getByText('スケジュール')).toBeInTheDocument()
  })

  it('highlights active navigation item', () => {
    render(<Navigation />)

    // The dashboard should be active by default (pathname is '/')
    const dashboardLink = screen.getByText('ダッシュボード').closest('a')
    expect(dashboardLink).toHaveClass('bg-blue-600')
  })

  it('renders all navigation links with correct hrefs', () => {
    render(<Navigation />)

    const links = [
      { text: 'ダッシュボード', href: '/' },
      { text: 'エディタ', href: '/editor' },
      { text: '監視', href: '/monitoring' },
      { text: 'スケジュール', href: '/schedules' },
    ]

    links.forEach(({ text, href }) => {
      const link = screen.getByText(text).closest('a')
      expect(link).toHaveAttribute('href', href)
    })
  })

  it('has proper accessibility attributes', () => {
    render(<Navigation />)

    const nav = screen.getByRole('navigation')
    expect(nav).toBeInTheDocument()

    // Check if links are accessible
    const links = screen.getAllByRole('link')
    expect(links.length).toBeGreaterThan(0)

    links.forEach(link => {
      expect(link).toHaveAttribute('href')
    })
  })
})
