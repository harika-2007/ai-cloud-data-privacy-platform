import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell, RefreshCw, Check, CheckSquare, ChevronLeft, ChevronRight,
  AlertTriangle, Shield, Info, XCircle, Clock, Filter,
  Search,
} from 'lucide-react';
import { alertService } from '../services/alertService';
import StatusBadge from '../components/Common/StatusBadge';
import Loading from '../components/Common/Loading';
import ErrorState from '../components/Common/ErrorState';
import EmptyState from '../components/Common/EmptyState';
import toast from 'react-hot-toast';

const SEVERITY_FILTERS = [
  { value: 'ALL', label: 'All', color: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300' },
  { value: 'critical', label: 'Critical', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' },
  { value: 'high', label: 'High', color: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400' },
  { value: 'medium', label: 'Medium', color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' },
  { value: 'low', label: 'Low', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' },
];

const alertTypeIcons = {
  critical: XCircle,
  high: AlertTriangle,
  medium: Info,
  low: Shield,
  info: Info,
};

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [alertStats, setAlertStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('ALL');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [markingId, setMarkingId] = useState(null);
  const [markingAll, setMarkingAll] = useState(false);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, page_size: 20 };
      if (filter !== 'ALL') params.severity = filter;
      const [alertsResult, statsResult] = await Promise.all([
        alertService.getAlerts(params),
        alertService.getAlertStats(),
      ]);
      const alertList = alertsResult?.alerts || alertsResult?.data || alertsResult || [];
      setAlerts(Array.isArray(alertList) ? alertList : []);
      setTotalPages(alertsResult?.total_pages || alertsResult?.totalPages || 1);
      setAlertStats(statsResult);
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  }, [page, filter]);

  useEffect(() => { fetchAlerts(); }, [fetchAlerts]);

  const handleMarkRead = async (id) => {
    setMarkingId(id);
    try {
      await alertService.markAsRead(id);
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, is_read: true, read: true } : a)));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to mark as read');
    } finally {
      setMarkingId(null);
    }
  };

  const handleMarkAllRead = async () => {
    setMarkingAll(true);
    try {
      await alertService.markAllAsRead();
      setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true, read: true })));
      toast.success('All alerts marked as read');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    } finally {
      setMarkingAll(false);
    }
  };

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    setPage(1);
  };

  if (loading && alerts.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Alerts</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">Security Operations Center</p>
          </div>
        </div>
        <Loading message="Loading alerts..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Alerts</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">Security Operations Center</p>
          </div>
        </div>
        <ErrorState message={error} onRetry={fetchAlerts} />
      </div>
    );
  }

  const unreadCount = alertStats?.unread_alerts ?? alerts.filter((a) => !a.is_read && !a.read).length;
  const totalCount = alertStats?.total_alerts ?? alerts.length;

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-3">
            <Bell className="w-6 h-6 text-cyber-500" />
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Alerts</h1>
            {unreadCount > 0 && (
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="px-2.5 py-0.5 bg-red-500 text-white text-xs font-bold rounded-full"
              >
                {unreadCount}
              </motion.span>
            )}
          </div>
          <p className="text-gray-500 dark:text-gray-400 mt-1 ml-9">
            {totalCount > 0
              ? `${unreadCount} unread of ${totalCount} total alerts`
              : 'Security Operations Center'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <button onClick={handleMarkAllRead} disabled={markingAll} className="btn-ghost text-sm">
              {markingAll ? (
                <div className="w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin" />
              ) : (
                <CheckSquare className="w-4 h-4" />
              )}
              Mark all read
            </button>
          )}
          <button onClick={fetchAlerts} className="btn-ghost"><RefreshCw className="w-4 h-4" /></button>
        </div>
      </div>

      {/* Filter Chips */}
      <div className="flex flex-wrap items-center gap-2">
        <Filter className="w-4 h-4 text-gray-400" />
        {SEVERITY_FILTERS.map((sev) => (
          <button
            key={sev.value}
            onClick={() => handleFilterChange(sev.value)}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
              filter === sev.value
                ? 'bg-cyber-50 dark:bg-cyber-900/20 border-cyber-300 dark:border-cyber-700 text-cyber-700 dark:text-cyber-400 shadow-sm'
                : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            {sev.label}
          </button>
        ))}
      </div>

      {/* Alerts List */}
      {alerts.length === 0 ? (
        <EmptyState
          icon={Bell}
          title="All clear!"
          description="No alerts to show. You're up to date."
        />
      ) : (
        <div className="space-y-3">
          <AnimatePresence>
            {alerts.map((alert, idx) => {
              const severity = (alert.severity || 'info').toLowerCase();
              const isRead = alert.is_read || alert.read;
              const alertMessage = alert.message || alert.alert_type || alert.title || 'No message';
              const createdAt = alert.created_at || alert.createdAt || alert.timestamp;
              const TypeIcon = alertTypeIcons[severity] || Info;

              return (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.03 }}
                  className={`group relative rounded-xl border transition-all duration-200 ${
                    isRead
                      ? 'bg-white dark:bg-surface-card-dark border-gray-100 dark:border-gray-700/50'
                      : 'bg-gradient-to-r from-cyber-50/50 to-white dark:from-cyber-900/10 dark:to-surface-card-dark border-cyber-200 dark:border-cyber-800/50 shadow-sm'
                  }`}
                >
                  <div className="flex items-start gap-4 p-4">
                    {/* Severity icon */}
                    <div className={`mt-0.5 relative ${
                      severity === 'critical' ? 'text-red-500' :
                      severity === 'high' ? 'text-orange-500' :
                      severity === 'medium' ? 'text-yellow-500' :
                      'text-green-500'
                    }`}>
                      <TypeIcon className="w-5 h-5" />
                      {!isRead && (
                        <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-cyber-500 rounded-full ring-2 ring-white dark:ring-gray-900" />
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className={`text-sm ${isRead ? 'text-gray-600 dark:text-gray-400' : 'text-gray-900 dark:text-white font-semibold'}`}>
                            {alertMessage}
                          </p>
                          <div className="flex items-center gap-2.5 mt-1.5 flex-wrap">
                            <StatusBadge status={severity} type="severity" dot />
                            {createdAt && (
                              <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {new Date(createdAt).toLocaleDateString('en-US', {
                                  month: 'short', day: 'numeric',
                                  hour: '2-digit', minute: '2-digit',
                                })}
                              </span>
                            )}
                            {alert.source && (
                              <span className="text-xs text-gray-400 dark:text-gray-500">Source: {alert.source}</span>
                            )}
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                          {!isRead && (
                            <button
                              onClick={() => handleMarkRead(alert.id)}
                              disabled={markingId === alert.id}
                              className="p-1.5 rounded-lg text-cyber-600 dark:text-cyber-400 hover:bg-cyber-50 dark:hover:bg-cyber-900/20 transition-colors"
                              title="Mark as read"
                            >
                              {markingId === alert.id ? (
                                <div className="w-4 h-4 border-2 border-cyber-500 border-t-transparent rounded-full animate-spin" />
                              ) : (
                                <Check className="w-4 h-4" />
                              )}
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-sm text-gray-500 dark:text-gray-400">Page {page} of {totalPages}</p>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="btn-ghost p-2 disabled:opacity-50">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="btn-ghost p-2 disabled:opacity-50">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
