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
  ArcElement,
} from 'chart.js'
import { Line, Bar, Doughnut } from 'react-chartjs-2'
import { format, subDays } from 'date-fns'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

interface TaskPerformanceChartProps {
  type: 'line' | 'bar' | 'doughnut'
  data?: any
  title?: string
  height?: number
}

export default function TaskPerformanceChart({ 
  type, 
  data, 
  title = 'Task Performance',
  height = 300 
}: TaskPerformanceChartProps) {
  
  // デフォルトデータ（実際の実装ではAPIから取得）
  const defaultLineData = {
    labels: Array.from({ length: 7 }, (_, i) => 
      format(subDays(new Date(), 6 - i), 'MM/dd')
    ),
    datasets: [
      {
        label: 'Completed Tasks',
        data: [12, 19, 8, 15, 22, 18, 25],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Failed Tasks',
        data: [2, 1, 3, 1, 0, 2, 1],
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4,
      },
    ],
  }

  const defaultBarData = {
    labels: ['E-commerce', 'News', 'API', 'Social Media', 'Real Estate'],
    datasets: [
      {
        label: 'Success Rate (%)',
        data: [95, 88, 99, 92, 85],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(168, 85, 247, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderColor: [
          'rgb(34, 197, 94)',
          'rgb(59, 130, 246)',
          'rgb(168, 85, 247)',
          'rgb(245, 158, 11)',
          'rgb(239, 68, 68)',
        ],
        borderWidth: 1,
      },
    ],
  }

  const defaultDoughnutData = {
    labels: ['Completed', 'Running', 'Failed', 'Pending'],
    datasets: [
      {
        data: [142, 8, 6, 12],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(156, 163, 175, 0.8)',
        ],
        borderColor: [
          'rgb(34, 197, 94)',
          'rgb(59, 130, 246)',
          'rgb(239, 68, 68)',
          'rgb(156, 163, 175)',
        ],
        borderWidth: 2,
      },
    ],
  }

  const chartData = data || (
    type === 'line' ? defaultLineData :
    type === 'bar' ? defaultBarData :
    defaultDoughnutData
  )

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
        text: title,
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
      },
    },
    scales: type !== 'doughnut' ? {
      x: {
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
    } : {},
  }

  const renderChart = () => {
    switch (type) {
      case 'line':
        return <Line data={chartData} options={options} />
      case 'bar':
        return <Bar data={chartData} options={options} />
      case 'doughnut':
        return <Doughnut data={chartData} options={options} />
      default:
        return <Line data={chartData} options={options} />
    }
  }

  return (
    <div className="w-full" style={{ height: `${height}px` }}>
      {renderChart()}
    </div>
  )
}

// 個別のチャートコンポーネント
export function TaskTrendChart({ data, height = 300 }: { data?: any, height?: number }) {
  return (
    <TaskPerformanceChart 
      type="line" 
      data={data} 
      title="Task Trends (Last 7 Days)" 
      height={height}
    />
  )
}

export function SpiderSuccessRateChart({ data, height = 300 }: { data?: any, height?: number }) {
  return (
    <TaskPerformanceChart 
      type="bar" 
      data={data} 
      title="Spider Success Rates" 
      height={height}
    />
  )
}

export function TaskStatusChart({ data, height = 300 }: { data?: any, height?: number }) {
  return (
    <TaskPerformanceChart 
      type="doughnut" 
      data={data} 
      title="Task Status Distribution" 
      height={height}
    />
  )
}
