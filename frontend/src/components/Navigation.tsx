'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  Home, 
  Code, 
  Monitor, 
  Calendar,
  Settings,
  Database,
  Bell,
  User
} from 'lucide-react'

const Navigation = () => {
  const pathname = usePathname()

  const navItems = [
    {
      name: 'ダッシュボード',
      href: '/',
      icon: Home
    },
    {
      name: 'エディタ',
      href: '/editor',
      icon: Code
    },
    {
      name: '監視',
      href: '/monitoring',
      icon: Monitor
    },
    {
      name: 'スケジュール',
      href: '/schedules',
      icon: Calendar
    },
    {
      name: 'プロジェクト',
      href: '/projects',
      icon: Database
    },
    {
      name: '設定',
      href: '/settings',
      icon: Settings
    }
  ]

  return (
    <nav className="bg-gray-800 text-white w-64 min-h-screen p-4">
      <div className="mb-8">
        <h1 className="text-xl font-bold">Scrapy UI</h1>
      </div>
      
      <ul className="space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href
          
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`flex items-center space-x-3 px-4 py-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.name}</span>
              </Link>
            </li>
          )
        })}
      </ul>
      
      <div className="mt-auto pt-8">
        <div className="border-t border-gray-700 pt-4">
          <Link
            href="/profile"
            className="flex items-center space-x-3 px-4 py-2 rounded-lg text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
          >
            <User className="w-5 h-5" />
            <span>プロフィール</span>
          </Link>
        </div>
      </div>
    </nav>
  )
}

export default Navigation
