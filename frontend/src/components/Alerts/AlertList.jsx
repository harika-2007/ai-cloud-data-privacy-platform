import { useState } from 'react';
import {
  FiBell,
  FiCheck,
  FiCheckSquare,
  FiRefreshCw,
  FiChevronLeft,
  FiChevronRight,
  FiAlertTriangle,
  FiInfo,
  FiShield,
  FiXCircle,
  FiClock,
} from 'react-icons/fi';
import StatusBadge from '../Common/StatusBadge';
import Loading from '../Common/Loading';
import EmptyState from '../Common/EmptyState';
import ErrorState from '../Common/ErrorState';

const alertTypeIcons = {
  critical: <FiXCircle className="w-5 h-5 text-red-500" />,
  high: <FiAlertTriangle className="w-5 h-5 text-orange-500" />,
  medium: <FiInfo className="w-5 h-5 text-yellow-500" />,
  low: <FiShield className="w-5 h-5 text-green-500" />,
  info: <FiInfo className="w-5 h-5 text-blue-500" />,
};

export default function AlertList({
  alerts = [],
  loading = false,
  error = null,
  onRetry,
  onMarkRead,
  onMarkAllRead,
  page = 1,
  totalPages = 1,
  onPageChange,
}) {
  const [markingId, setMarkingId] = useState(null);
  const [markingAll, setMarkingAll] = useState(false);

  const handleMarkRead = async (id) => {
    setMarkingId(id);
    try {
      await onMarkRead(id);
    } finally {
      setMarkingId(null);
    }
  };

  const handleMarkAllRead = async () => {
    setMarkingAll(true);
    try {
      await onMarkAllRead();
    } finally {
      setMarkingAll(false);
    }
  };

  if (loading) {
    return <Loading message="Loading alerts..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={onRetry} />;
  }

  if (!alerts || alerts.length === 0) {
    return (
      <EmptyState
        icon={<FiBell className="w-12 h-12" />}
        title="No alerts"
        description="You're all caught up! No alerts to show."
      />
    );
  }

  const unreadCount = alerts.filter((a) => !a.is_read && !a.read).length;

  return (
    <div className="space-y-4">
      {/* Actions Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <span className="text-sm text-gray-500">
              <strong className="text-gray-900">{unreadCount}</strong> unread alert{unreadCount !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              disabled={markingAll}
              className="btn-ghost text-sm flex items-center gap-1.5"
            >
              {markingAll ? (
                <div className="w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin" />
              ) : (
                <FiCheckSquare className="w-4 h-4" />
              )}
              Mark all as read
            </button>
          )}
          <button onClick={onRetry} className="btn-ghost p-2" title="Refresh">
            <FiRefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-2">
        {alerts.map((alert) => {
          const severity = (alert.severity || 'info').toLowerCase();
          const isRead = alert.is_read || alert.read;
          const alertMessage = alert.message || alert.alert_type || alert.title || 'No message';
          const createdAt = alert.created_at || alert.createdAt || alert.timestamp;

          return (
            <div
              key={alert.id}
              className={`bg-white rounded-xl border p-4 transition-colors ${
                isRead
                  ? 'border-gray-200'
                  : 'border-cyber-200 bg-cyber-50/30'
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Type Icon */}
                <div className="mt-0.5 flex-shrink-0">
                  {!isRead && (
                    <span className="absolute w-2 h-2 bg-cyber-500 rounded-full ml-5 mt-1.5" />
                  )}
                  {alertTypeIcons[severity] || <FiInfo className="w-5 h-5 text-blue-500" />}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className={`text-sm ${isRead ? 'text-gray-600' : 'text-gray-900 font-medium'}`}>
                        {alertMessage}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <StatusBadge status={severity} type="severity" />
                        {createdAt && (
                          <span className="text-xs text-gray-400 flex items-center gap-1">
                            <FiClock className="w-3 h-3" />
                            {new Date(createdAt).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1 flex-shrink-0">
                      {!isRead && (
                        <button
                          onClick={() => handleMarkRead(alert.id)}
                          disabled={markingId === alert.id}
                          className="p-1.5 hover:bg-cyber-100 rounded-lg text-cyber-600 hover:text-cyber-700 transition-colors"
                          title="Mark as read"
                        >
                          {markingId === alert.id ? (
                            <div className="w-4 h-4 border-2 border-cyber-600 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <FiCheck className="w-4 h-4" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Metadata */}
                  {alert.source && (
                    <p className="text-xs text-gray-400 mt-1">
                      Source: {alert.source}
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-sm text-gray-500">
            Page {page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="btn-ghost p-2 disabled:opacity-50"
            >
              <FiChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="btn-ghost p-2 disabled:opacity-50"
            >
              <FiChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
