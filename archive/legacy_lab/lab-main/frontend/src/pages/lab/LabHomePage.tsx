import { Link } from 'react-router-dom'
import { ROUTES } from '../../utils/constants'

interface TileProps {
  title: string
  description: string
  to?: string
  onClick?: () => void
  color?: string
}

function Tile({ title, description, to, onClick, color = 'blue' }: TileProps) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 hover:bg-blue-100',
    green: 'bg-green-50 border-green-200 hover:bg-green-100',
    purple: 'bg-purple-50 border-purple-200 hover:bg-purple-100',
    teal: 'bg-teal-50 border-teal-200 hover:bg-teal-100',
    orange: 'bg-orange-50 border-orange-200 hover:bg-orange-100',
    red: 'bg-red-50 border-red-200 hover:bg-red-100',
  }[color]

  const content = (
    <>
      <h3 className="text-lg font-semibold text-gray-800 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </>
  )

  if (to) {
    return (
      <Link
        to={to}
        className={`block p-6 rounded-lg border-2 ${colorClasses} transition-colors cursor-pointer`}
      >
        {content}
      </Link>
    )
  }

  return (
    <div
      onClick={onClick}
      className={`block p-6 rounded-lg border-2 ${colorClasses} transition-colors ${onClick ? 'cursor-pointer' : 'cursor-default opacity-60'}`}
    >
      {content}
    </div>
  )
}

export function LabHomePage() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Lab Home</h1>

      {/* Main Lab Actions */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">
          Lab Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Tile
            title="New Lab Slip"
            description="Create a new test order"
            to={ROUTES.LAB_NEW}
            color="blue"
          />
          <Tile
            title="Due Lab Slips"
            description="View pending orders"
            to={ROUTES.LAB_WORKLIST}
            color="orange"
          />
          <Tile
            title="Sample Collection"
            description="Collect and receive samples"
            to={ROUTES.PHLEBOTOMY}
            color="green"
          />
          <Tile
            title="Enter Results"
            description="Enter test results"
            to={ROUTES.RESULT_ENTRY}
            color="purple"
          />
          <Tile
            title="Verify Results"
            description="Verify entered results"
            to={ROUTES.RESULT_VERIFICATION}
            color="teal"
          />
          <Tile
            title="Publish Results"
            description="Publish verified results"
            to={ROUTES.RESULT_PUBLISHING}
            color="green"
          />
          <Tile
            title="Manage Lab Tests"
            description="View and edit test catalog"
            to={ROUTES.ADMIN_CATALOG}
            color="blue"
          />
        </div>
      </section>

      {/* Reports Section */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Reports</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Tile
            title="Reports"
            description="View and generate reports"
            to={ROUTES.REPORTS}
            color="green"
          />
          <Tile
            title="Patient Records"
            description="View patient history"
            to={ROUTES.PATIENTS}
            color="blue"
          />
          <Tile
            title="Dashboard Analytics"
            description="View lab statistics"
            to={ROUTES.HOME}
            color="purple"
          />
        </div>
      </section>

      {/* Settings Section */}
      <section>
        <h2 className="text-xl font-semibold text-gray-700 mb-4">
          Settings & Admin
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Tile
            title="Workflow Settings"
            description="Configure lab workflow"
            to="/settings/workflow"
            color="purple"
          />
          <Tile
            title="Role Permissions"
            description="Manage user permissions"
            to="/settings/permissions"
            color="teal"
          />
          <Tile
            title="User Management"
            description="Manage system users"
            to={ROUTES.ADMIN_USERS}
            color="orange"
          />
        </div>
      </section>
    </div>
  )
}
