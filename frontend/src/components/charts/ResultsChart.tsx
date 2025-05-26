'use client'

import React from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import 'chartjs-adapter-date-fns'
import { format, subDays, parseISO } from 'date-fns'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
)

interface ResultsChartProps {
  type: 'timeline' | 'volume' | 'domains'
  data?: any
  title?: string
  height?: number
}

export default function ResultsChart({ 
  type, 
  data, 
  title,
  height = 300 
}: ResultsChartProps) {
  
  // タイムライン用のデフォルトデータ
  const defaultTimelineData = {
    datasets: [
      {
        label: 'Results Collected',
        data: Array.from({ length: 24 }, (_, i) => ({
          x: new Date(Date.now() - (23 - i) * 60 * 60 * 1000),
          y: Math.floor(Math.random() * 50) + 10
        })),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  }

  // ボリューム用のデフォルトデータ
  const defaultVolumeData = {
    labels: Array.from({ length: 7 }, (_, i) => 
      format(subDays(new Date(), 6 - i), 'MM/dd')
    ),
    datasets: [
      {
        label: 'Items Scraped',
        data: [1250, 1890, 1456, 2100, 1780, 2340, 1920],
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1,
      },
    ],
  }

  // ドメイン別のデフォルトデータ
  const defaultDomainsData = {
    labels: ['amazon.com', 'ebay.com', 'shopify.com', 'etsy.com', 'alibaba.com'],
    datasets: [
      {
        label: 'Results Count',
        data: [3420, 2890, 2150, 1680, 1340],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(168, 85, 247, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(34, 197, 94)',
          'rgb(168, 85, 247)',
          'rgb(245, 158, 11)',
          'rgb(239, 68, 68)',
        ],
        borderWidth: 1,
      },
    ],
  }

  const chartData = data || (
    type === 'timeline' ? defaultTimelineData :
    type === 'volume' ? defaultVolumeData :
    defaultDomainsData
  )

  const getTitle = () => {
    if (title) return title
    switch (type) {
      case 'timeline':
        return 'Results Timeline (Last 24 Hours)'
      case 'volume':
        return 'Daily Scraping Volume'
      case 'domains':
        return 'Top Domains by Results'
      default:
        return 'Results Chart'
    }
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: 'rgb(156, 163, 175)',
          font: {
            size: 12,
          },
        },
      },
      title: {
        display: true,
        text: getTitle(),
        color: 'rgb(255, 255, 255)',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.9)',
        titleColor: 'rgb(255, 255, 255)',
        bodyColor: 'rgb(156, 163, 175)',
        borderColor: 'rgb(75, 85, 99)',
        borderWidth: 1,
        callbacks: type === 'timeline' ? {
          title: function(context: any) {
            return format(new Date(context[0].parsed.x), 'MMM dd, HH:mm')
          }
        } : {},
      },
    },
    scales: {
      x: {
        type: type === 'timeline' ? 'time' as const : 'category' as const,
        time: type === 'timeline' ? {
          unit: 'hour' as const,
          displayFormats: {
            hour: 'HH:mm'
          }
        } : undefined,
        ticks: {
          color: 'rgb(156, 163, 175)',
        },
        grid: {
          color: 'rgba(75, 85, 99, 0.3)',
        },
      },
      y: {
        ticks: {
          color: 'rgb(156, 163, 175)',
        },
        grid: {
          color: 'rgba(75, 85, 99, 0.3)',
        },
      },
    },
  }

  const renderChart = () => {
    if (type === 'timeline') {
      return <Line data={chartData} options={options} />
    } else {
      return <Bar data={chartData} options={options} />
    }
  }

  return (
    <div className="w-full" style={{ height: `${height}px` }}>
      {renderChart()}
    </div>
  )
}

// 個別のチャートコンポーネント
export function ResultsTimelineChart({ data, height = 300 }: { data?: any, height?: number }) {
  return (
    <ResultsChart 
      type="timeline" 
      data={data} 
      height={height}
    />
  )
}

export function DailyVolumeChart({ data, height = 300 }: { data?: any, height?: number }) {
  return (
    <ResultsChart 
      type="volume" 
      data={data} 
      height={height}
    />
  )
}

export function TopDomainsChart({ data, height = 300 }: { data?: any, height?: number }) {
  return (
    <ResultsChart 
      type="domains" 
      data={data} 
      height={height}
    />
  )
}
