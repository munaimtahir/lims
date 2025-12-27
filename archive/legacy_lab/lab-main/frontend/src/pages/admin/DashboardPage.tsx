import { useState, useEffect, useCallback } from 'react'
import { dashboardService } from '../../services/dashboard'
import type { DashboardAnalytics } from '../../types'

interface BarChartProps {
  data: { date: string; count: number }[]
  title: string
}

function BarChart({ data, title }: BarChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <p className="text-gray-500 text-center py-8">No data available</p>
      </div>
    )
  }

  const maxCount = Math.max(...data.map(d => d.count), 1)

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <div className="space-y-2">
        {data.slice(-10).map((item, index) => (
          <div key={index} className="flex items-center gap-2">
            <div className="w-24 text-sm text-gray-600 flex-shrink-0">
              {new Date(item.date).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
              })}
            </div>
            <div className="flex-1 flex items-center gap-2">
              <div
                className="bg-blue-500 h-8 rounded transition-all"
                style={{
                  width: `${(item.count / maxCount) * 100}%`,
                  minWidth: item.count > 0 ? '2rem' : '0',
                }}
              />
              <span className="text-sm font-medium text-gray-700">
                {item.count}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

interface PieChartProps {
  data: { label: string; value: number; color: string }[]
  title: string
}

function PieChart({ data, title }: PieChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0)

  if (total === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <p className="text-gray-500 text-center py-8">No data available</p>
      </div>
    )
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <div className="space-y-3">
        {data.map((item, index) => {
          const percentage = ((item.value / total) * 100).toFixed(1)
          return (
            <div key={index}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-700 font-medium">{item.label}</span>
                <span className="text-gray-600">
                  {item.value} ({percentage}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${item.color}`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

interface QuickTileProps {
  title: string
  value: number
  icon: string
  color: string
}

function QuickTile({ title, value, icon, color }: QuickTileProps) {
  return (
    <div className={`${color} p-6 rounded-lg shadow text-white`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-white/80 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold mt-2">{value}</p>
        </div>
        <div className="text-5xl opacity-80">{icon}</div>
      </div>
    </div>
  )
}

export function DashboardPage() {
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [dateRange, setDateRange] = useState({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
  })

  const loadAnalytics = useCallback(async () => {
    try {
      setLoading(true)
      setError('')
      const data = await dashboardService.getAnalytics(dateRange)
      setAnalytics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }, [dateRange])

  useEffect(() => {
    loadAnalytics()
  }, [loadAnalytics])

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setDateRange(prev => ({ ...prev, [name]: value }))
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading analytics...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    )
  }

  if (!analytics) {
    return null
  }

  const sampleStatusData = [
    {
      label: 'Pending',
      value: analytics.sample_status.pending,
      color: 'bg-gray-500',
    },
    {
      label: 'Collected',
      value: analytics.sample_status.collected,
      color: 'bg-yellow-500',
    },
    {
      label: 'Received',
      value: analytics.sample_status.received,
      color: 'bg-teal-500',
    },
    {
      label: 'Rejected',
      value: analytics.sample_status.rejected,
      color: 'bg-red-500',
    },
  ]

  const resultStatusData = [
    {
      label: 'Draft',
      value: analytics.result_status.draft,
      color: 'bg-gray-500',
    },
    {
      label: 'Entered',
      value: analytics.result_status.entered,
      color: 'bg-blue-500',
    },
    {
      label: 'Verified',
      value: analytics.result_status.verified,
      color: 'bg-green-500',
    },
    {
      label: 'Published',
      value: analytics.result_status.published,
      color: 'bg-green-700',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          Lab Dashboard & Analytics
        </h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">From:</label>
            <input
              type="date"
              name="start_date"
              value={dateRange.start_date}
              onChange={handleDateChange}
              className="border border-gray-300 rounded px-3 py-1 text-sm"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">To:</label>
            <input
              type="date"
              name="end_date"
              value={dateRange.end_date}
              onChange={handleDateChange}
              className="border border-gray-300 rounded px-3 py-1 text-sm"
            />
          </div>
        </div>
      </div>

      {/* Quick Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <QuickTile
          title="Total Orders Today"
          value={analytics.quick_tiles.total_orders_today}
          icon="📋"
          color="bg-blue-600"
        />
        <QuickTile
          title="Reports Published Today"
          value={analytics.quick_tiles.reports_published_today}
          icon="✓"
          color="bg-green-600"
        />
        <QuickTile
          title="Average TAT (hours)"
          value={parseFloat(analytics.avg_tat_hours.toFixed(1))}
          icon="⏱"
          color="bg-purple-600"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BarChart data={analytics.orders_per_day} title="Orders Per Day" />
        <PieChart data={sampleStatusData} title="Sample Status Distribution" />
        <PieChart data={resultStatusData} title="Result Status Distribution" />
      </div>
    </div>
  )
}
