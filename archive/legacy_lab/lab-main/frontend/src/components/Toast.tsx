import { useEffect } from 'react'

/**
 * Interface for the props of the Toast component.
 */
interface ToastProps {
  message: string
  type: 'success' | 'error' | 'info'
  onClose: () => void
  duration?: number
}

const TOAST_CONFIG = {
  success: {
    bgColor: 'bg-green-50 border-green-200',
    textColor: 'text-green-800',
    icon: '✓',
  },
  error: {
    bgColor: 'bg-red-50 border-red-200',
    textColor: 'text-red-800',
    icon: '✕',
  },
  info: {
    bgColor: 'bg-blue-50 border-blue-200',
    textColor: 'text-blue-800',
    icon: 'ℹ',
  },
}

/**
 * A toast notification component.
 * @param {ToastProps} props - The component props.
 * @returns {JSX.Element} The rendered toast.
 */
export function Toast({ message, type, onClose, duration = 5000 }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose()
    }, duration)

    return () => clearTimeout(timer)
  }, [duration, onClose])

  const config = TOAST_CONFIG[type]

  return (
    <div
      className={`fixed top-4 right-4 z-50 ${config.bgColor} border rounded-lg shadow-lg p-4 max-w-sm flex items-start gap-3 animate-slide-in`}
      role="alert"
    >
      <span className={`text-xl ${config.textColor}`}>{config.icon}</span>
      <p className={`text-sm flex-1 ${config.textColor}`}>{message}</p>
      <button
        onClick={onClose}
        className={`${config.textColor} hover:opacity-70 text-lg leading-none`}
        aria-label="Close"
      >
        ×
      </button>
    </div>
  )
}
