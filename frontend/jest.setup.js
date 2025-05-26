import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    }
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  usePathname() {
    return '/'
  },
}))

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ value, onChange, ...props }) => {
    return (
      <textarea
        data-testid="monaco-editor"
        value={value}
        onChange={(e) => onChange && onChange(e.target.value)}
        {...props}
      />
    )
  },
}))

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options, ...props }) => (
    <div data-testid="line-chart" {...props}>
      Chart: {JSON.stringify(data)}
    </div>
  ),
  Bar: ({ data, options, ...props }) => (
    <div data-testid="bar-chart" {...props}>
      Chart: {JSON.stringify(data)}
    </div>
  ),
  Doughnut: ({ data, options, ...props }) => (
    <div data-testid="doughnut-chart" {...props}>
      Chart: {JSON.stringify(data)}
    </div>
  ),
}))

// Mock WebSocket
global.WebSocket = jest.fn(() => ({
  close: jest.fn(),
  send: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}))

// Mock fetch
global.fetch = jest.fn()

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
global.localStorage = localStorageMock

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
global.sessionStorage = sessionStorageMock

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))
