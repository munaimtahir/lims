import { Link } from 'react-router-dom'
import { ROUTES } from '../../utils/constants'

interface SettingsTileProps {
  title: string
  description: string
  to?: string
  isImplemented?: boolean
}

function SettingsTile({
  title,
  description,
  to,
  isImplemented = false,
}: SettingsTileProps) {
  const content = (
    <>
      <h3 className="text-lg font-semibold text-gray-800 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
      {!isImplemented && (
        <p className="text-xs text-orange-600 mt-2">Coming soon</p>
      )}
    </>
  )

  if (to && isImplemented) {
    return (
      <Link
        to={to}
        className="block bg-white rounded-lg shadow p-6 border-2 border-gray-200 hover:border-blue-500 hover:shadow-lg transition-all cursor-pointer"
      >
        {content}
      </Link>
    )
  }

  return (
    <div
      className={`block bg-white rounded-lg shadow p-6 border-2 border-gray-200 ${!isImplemented ? 'opacity-60' : ''}`}
    >
      {content}
    </div>
  )
}

export function SettingsPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Settings</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <SettingsTile
          title="User Management"
          description="Manage users, roles, and permissions"
          to={ROUTES.ADMIN_USERS}
          isImplemented={true}
        />

        <SettingsTile
          title="Test Catalog"
          description="Manage test catalog and pricing"
          to={ROUTES.ADMIN_CATALOG}
          isImplemented={true}
        />

        <SettingsTile
          title="Lab Terminals"
          description="Configure offline MRN ranges for terminals"
          to={ROUTES.ADMIN_TERMINALS}
          isImplemented={true}
        />

        <SettingsTile
          title="Tests Management"
          description="Manage LIMS test definitions and configurations"
          to="/admin/tests"
          isImplemented={true}
        />

        <SettingsTile
          title="Parameters Management"
          description="Manage test parameters and analytes"
          to="/admin/parameters"
          isImplemented={true}
        />

        <SettingsTile
          title="Test-Parameter Relationships"
          description="Link parameters to tests and configure display"
          to="/admin/test-parameters"
          isImplemented={true}
        />

        <SettingsTile
          title="Workflow Customization"
          description="Configure which workflow steps are enabled"
          to="/settings/workflow"
          isImplemented={true}
        />

        <SettingsTile
          title="Role & Permissions"
          description="Configure permissions for each role"
          to="/settings/permissions"
          isImplemented={true}
        />

        <SettingsTile
          title="Branches"
          description="Configure lab branches and locations"
          isImplemented={false}
        />

        <SettingsTile
          title="Departments"
          description="Manage test departments"
          isImplemented={false}
        />

        <SettingsTile
          title="Doctors"
          description="Doctor information and signatures"
          isImplemented={false}
        />

        <SettingsTile
          title="System Settings"
          description="General system configuration"
          isImplemented={false}
        />

        <SettingsTile
          title="Page Headers"
          description="Customize report headers and branding"
          isImplemented={false}
        />
      </div>
    </div>
  )
}
