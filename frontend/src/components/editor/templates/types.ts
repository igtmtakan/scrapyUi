import { ReactNode } from 'react'

export interface Template {
  id: string
  name: string
  description: string
  icon: ReactNode
  category: 'basic' | 'ecommerce' | 'news' | 'api' | 'advanced' | 'social' | 'data' | 'monitoring' | 'security' | 'performance' | 'testing' | 'automation' | 'integration' | 'mobile' | 'media' | 'finance' | 'travel' | 'food' | 'real-estate' | 'job' | 'education' | 'health' | 'sports' | 'gaming' | 'weather' | 'government' | 'legal' | 'nonprofit' | 'playwright' | 'parsing' | 'browser-automation'
  code: string
}

export interface Category {
  id: string
  name: string
}

export const CATEGORIES: Category[] = [
  { id: 'all', name: 'All Templates' },
  { id: 'basic', name: 'Basic' },
  { id: 'api', name: 'API' },
  { id: 'data', name: 'Data Extraction' },
  { id: 'ecommerce', name: 'E-commerce' },
  { id: 'news', name: 'News' },
  { id: 'social', name: 'Social Media' },
  { id: 'monitoring', name: 'Monitoring' },
  { id: 'security', name: 'Security' },
  { id: 'performance', name: 'Performance' },
  { id: 'testing', name: 'Testing' },
  { id: 'automation', name: 'Automation' },
  { id: 'integration', name: 'Integration' },
  { id: 'mobile', name: 'Mobile' },
  { id: 'media', name: 'Media' },
  { id: 'finance', name: 'Finance' },
  { id: 'travel', name: 'Travel' },
  { id: 'food', name: 'Food' },
  { id: 'real-estate', name: 'Real Estate' },
  { id: 'job', name: 'Job Boards' },
  { id: 'education', name: 'Education' },
  { id: 'health', name: 'Health' },
  { id: 'sports', name: 'Sports' },
  { id: 'gaming', name: 'Gaming' },
  { id: 'weather', name: 'Weather' },
  { id: 'government', name: 'Government' },
  { id: 'legal', name: 'Legal' },
  { id: 'nonprofit', name: 'Non-profit' },
  { id: 'playwright', name: 'Playwright' },
  { id: 'parsing', name: 'Parsing' },
  { id: 'browser-automation', name: 'Browser Automation' },
  { id: 'advanced', name: 'Advanced' }
]
