import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ROUTES } from '../utils/constants'

// TEMPORARY FULL PERMISSION OVERRIDE — REMOVE LATER WHEN FINE-GRAINED PERMISSIONS ARE ACTIVATED.
// Set this to false to enable role-based route protection
// Can also be controlled via VITE_TEMPORARY_FULL_ACCESS_MODE environment variable
export const TEMPORARY_FULL_ACCESS_MODE = 
  import.meta.env.VITE_TEMPORARY_FULL_ACCESS_MODE !== 'false'

/**
 * Interface for the props of the ProtectedRoute component.
 */
interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: string[]
}

/**
 * A component that protects a route from unauthenticated or unauthorized users.
 * @param {ProtectedRouteProps} props - The component props.
 * @returns {JSX.Element} The rendered component.
 */
export function ProtectedRoute({
  children,
  allowedRoles,
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-red-900 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />
  }

  // TEMPORARY FULL PERMISSION OVERRIDE — REMOVE LATER WHEN FINE-GRAINED PERMISSIONS ARE ACTIVATED.
  if (TEMPORARY_FULL_ACCESS_MODE) {
    return <>{children}</>
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-md bg-white rounded-lg shadow-lg p-8 text-center">
          <h2 className="text-2xl font-bold text-red-900 mb-4">
            Access Denied
          </h2>
          <p className="text-gray-600">
            You don't have permission to access this page.
          </p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
