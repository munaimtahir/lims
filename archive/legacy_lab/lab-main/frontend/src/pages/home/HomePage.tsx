import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { dashboardService } from '../../services/dashboard'
import type { DashboardAnalytics } from '../../types'
import { ROUTES } from '../../utils/constants'

interface StatTileProps {
  title: string
  value: number | string
  color: 'blue' | 'yellow' | 'green' | 'red' | 'purple' | 'teal' | 'orange'
  to?: string
  isLoading?: boolean
}

function StatTile({ title, value, color, to, isLoading }: StatTileProps) {
  const colorClasses = {
    blue: 'text-blue-600',
    yellow: 'text-yellow-600',
    green: 'text-green-600',
    red: 'text-red-600',
    purple: 'text-purple-600',
    teal: 'text-teal-600',
    orange: 'text-orange-600',
  }

  const content = (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
      <h3 className="text-lg font-semibold text-gray-700 mb-2">{title}</h3>
      {isLoading ? (
        <div className="h-9 w-16 bg-gray-200 animate-pulse rounded"></div>
      ) : (
        <p className={`text-3xl font-bold ${colorClasses[color]}`}>{value}</p>
      )}
    </div>
  )

  if (to) {
    return <Link to={to}>{content}</Link>
  }

  return content
}

interface ActionTileProps {
  title: string
  description: string
  to: string
  color: 'blue' | 'green' | 'purple' | 'teal' | 'orange' | 'red'
}

function ActionTile({ title, description, to, color }: ActionTileProps) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 hover:bg-blue-100',
    green: 'bg-green-50 border-green-200 hover:bg-green-100',
    purple: 'bg-purple-50 border-purple-200 hover:bg-purple-100',
    teal: 'bg-teal-50 border-teal-200 hover:bg-teal-100',
    orange: 'bg-orange-50 border-orange-200 hover:bg-orange-100',
    red: 'bg-red-50 border-red-200 hover:bg-red-100',
  }

  return (
    <Link
      to={to}
      className={`block p-6 rounded-lg border-2 ${colorClasses[color]} transition-colors cursor-pointer`}
    >
      <h3 className="text-lg font-semibold text-gray-800 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </Link>
  )
}

export function HomePage() {
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setIsLoading(true)
        const data = await dashboardService.getAnalytics()
        setAnalytics(data)
        setError(null)
      } catch (err) {
        console.error('Failed to fetch analytics:', err)
        setError('Failed to load dashboard data')
      } finally {
        setIsLoading(false)
      }
    }

    fetchAnalytics()
  }, [])

  // Calculate pending counts from analytics
  const pendingSamples =
    analytics?.sample_status.pending ?? 0
  const pendingCollection =
    analytics?.sample_status.collected ?? 0
  const pendingResultEntry =
    (analytics?.sample_status.received ?? 0) -
    (analytics?.result_status.entered ?? 0) -
    (analytics?.result_status.verified ?? 0) -
    (analytics?.result_status.published ?? 0)
  const pendingVerification = analytics?.result_status.entered ?? 0
  const pendingPublishing = analytics?.result_status.verified ?? 0
  const totalOrdersToday = analytics?.quick_tiles.total_orders_today ?? 0
  const reportsPublishedToday =
    analytics?.quick_tiles.reports_published_today ?? 0
  const avgTat = analytics?.avg_tat_hours ?? 0

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Lab Dashboard</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Quick Stats */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">
          Today's Overview
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatTile
            title="Today's Orders"
            value={totalOrdersToday}
            color="blue"
            isLoading={isLoading}
          />
          <StatTile
            title="Pending Phlebotomy"
            value={pendingCollection}
            color="yellow"
            to={ROUTES.PHLEBOTOMY}
            isLoading={isLoading}
          />
          <StatTile
            title="Pending Result Entry"
            value={pendingResultEntry > 0 ? pendingResultEntry : 0}
            color="purple"
            to={ROUTES.RESULT_ENTRY}
            isLoading={isLoading}
          />
          <StatTile
            title="Pending Verification"
            value={pendingVerification}
            color="orange"
            to={ROUTES.RESULT_VERIFICATION}
            isLoading={isLoading}
          />
        </div>
      </section>

      {/* More Stats */}
      <section className="mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatTile
            title="Pending Publishing"
            value={pendingPublishing}
            color="teal"
            to={ROUTES.RESULT_PUBLISHING}
            isLoading={isLoading}
          />
          <StatTile
            title="Reports Published Today"
            value={reportsPublishedToday}
            color="green"
            isLoading={isLoading}
          />
          <StatTile
            title="Samples Pending"
            value={pendingSamples}
            color="yellow"
            to={ROUTES.PHLEBOTOMY}
            isLoading={isLoading}
          />
          <StatTile
            title="Avg. Turnaround Time"
            value={isLoading ? '--' : `${avgTat.toFixed(1)} hrs`}
            color="blue"
            isLoading={isLoading}
          />
        </div>
      </section>

      {/* Quick Actions */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <ActionTile
            title="New Lab Slip"
            description="Create a new test order"
            to={ROUTES.LAB_NEW}
            color="blue"
          />
          <ActionTile
            title="Due Lab Slips"
            description="View pending orders"
            to={ROUTES.LAB_WORKLIST}
            color="orange"
          />
          <ActionTile
            title="Sample Collection"
            description="Collect and receive samples"
            to={ROUTES.PHLEBOTOMY}
            color="green"
          />
          <ActionTile
            title="Enter Results"
            description="Enter test results"
            to={ROUTES.RESULT_ENTRY}
            color="purple"
          />
          <ActionTile
            title="Verify Results"
            description="Verify entered results"
            to={ROUTES.RESULT_VERIFICATION}
            color="teal"
          />
          <ActionTile
            title="Publish Results"
            description="Publish verified results"
            to={ROUTES.RESULT_PUBLISHING}
            color="green"
          />
        </div>
      </section>

      {/* Admin Actions */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">
          Administration
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <ActionTile
            title="Manage Lab Tests"
            description="View and edit test catalog"
            to={ROUTES.ADMIN_CATALOG}
            color="blue"
          />
          <ActionTile
            title="Workflow Settings"
            description="Configure lab workflow"
            to="/settings/workflow"
            color="purple"
          />
          <ActionTile
            title="Role Permissions"
            description="Manage user permissions"
            to="/settings/permissions"
            color="teal"
          />
          <ActionTile
            title="User Management"
            description="Manage system users"
            to={ROUTES.ADMIN_USERS}
            color="orange"
          />
          <ActionTile
            title="Lab Terminals"
            description="Manage lab terminals"
            to={ROUTES.ADMIN_TERMINALS}
            color="green"
          />
          <ActionTile
            title="Reports"
            description="View reports and statistics"
            to={ROUTES.REPORTS}
            color="blue"
          />
        </div>
      </section>

      {/* Sample Status Distribution */}
      {analytics && !isLoading && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">
            Sample Status Distribution
          </h2>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-600">
                  {analytics.sample_status.pending}
                </p>
                <p className="text-sm text-gray-500">Pending</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-600">
                  {analytics.sample_status.collected}
                </p>
                <p className="text-sm text-gray-500">Collected</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {analytics.sample_status.received}
                </p>
                <p className="text-sm text-gray-500">Received</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">
                  {analytics.sample_status.rejected}
                </p>
                <p className="text-sm text-gray-500">Rejected</p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Result Status Distribution */}
      {analytics && !isLoading && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">
            Result Status Distribution
          </h2>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-600">
                  {analytics.result_status.draft}
                </p>
                <p className="text-sm text-gray-500">Draft</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {analytics.result_status.entered}
                </p>
                <p className="text-sm text-gray-500">Entered</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-600">
                  {analytics.result_status.verified}
                </p>
                <p className="text-sm text-gray-500">Verified</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {analytics.result_status.published}
                </p>
                <p className="text-sm text-gray-500">Published</p>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
