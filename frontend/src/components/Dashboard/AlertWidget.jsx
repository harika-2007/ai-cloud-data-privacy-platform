import { Link } from 'react-router-dom'
import StatusBadge from '../Common/StatusBadge'
import { AlertTriangle } from 'lucide-react'

export default function AlertWidget({ alerts = [] }) {
  if (!alerts.length) return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Alerts</h3>
        <Link to="/alerts" className="text-sm text-cyber-600 dark:text-cyber-400 hover:underline">View all</Link>
      </div>
      <div className="text-center py-6 text-gray-400 dark:text-gray-500 flex flex-col items-center gap-2">
        <AlertTriangle className="w-8 h-8" />
        <p>No alerts</p>
      </div>
    </div>
  )

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Alerts</h3>
        <Link to="/alerts" className="text-sm text-cyber-600 dark:text-cyber-400 hover:underline">View all</Link>
      </div>
      <div className="space-y-3">
        {alerts.slice(0, 5).map((alert) => (
          <div key={alert.id} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <StatusBadge status={alert.severity} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{alert.message || alert.alert_type}</p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                {alert.created_at ? new Date(alert.created_at).toLocaleDateString() : ''}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
