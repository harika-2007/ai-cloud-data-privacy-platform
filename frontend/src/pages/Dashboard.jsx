import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line,
} from 'recharts';
import {
  FileText, Search, AlertTriangle, Shield, RefreshCw, TrendingUp, TrendingDown,
  Activity, Bell, ArrowRight, Clock, Server, Database, Cloud, Sparkles, Upload,
} from 'lucide-react';
import { dashboardService } from '../services/dashboardService';
import Loading from '../components/Common/Loading';
import ErrorState from '../components/Common/ErrorState';

const COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  info: '#3b82f6',
};

const PIE_COLORS = ['#6366f1', '#818cf8', '#a5b4fc', '#c7d2fe', '#e0e7ff'];

function KpiCard({ icon: Icon, label, value, trend, color, format = 'number', delay = 0 }) {
  const colorMap = {
    cyber: 'from-cyber-500 to-cyber-600',
    green: 'from-emerald-500 to-emerald-400',
    orange: 'from-orange-500 to-orange-400',
    red: 'from-red-500 to-red-400',
    purple: 'from-purple-500 to-purple-400',
  };

  const iconBgMap = {
    cyber: 'bg-cyber-100 dark:bg-cyber-900/30 text-cyber-600 dark:text-cyber-400',
    green: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400',
    orange: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400',
    red: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
    purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
  };

  const formatValue = (val) => {
    if (format === 'percentage') return `${Math.round(val)}%`;
    if (format === 'number') return (val ?? 0).toLocaleString();
    return val ?? '0';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay * 0.1 }}
      className="relative overflow-hidden rounded-xl bg-white dark:bg-surface-card-dark border border-gray-100 dark:border-gray-700/50 p-5 hover:shadow-lg hover:border-gray-200 dark:hover:border-gray-600/50 transition-all duration-300 group"
    >
      <div className="absolute top-0 right-0 w-32 h-32 -mr-8 -mt-8 rounded-full bg-gradient-to-br opacity-5 dark:opacity-10" />
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
            {formatValue(value)}
          </p>
          {trend !== undefined && (
            <div className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
              trend >= 0
                ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400'
                : 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'
            }`}>
              {trend >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              {Math.abs(trend).toFixed(1)}%
            </div>
          )}
        </div>
        <div className={`w-11 h-11 rounded-xl ${iconBgMap[color]} flex items-center justify-center transition-transform duration-300 group-hover:scale-110`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className={`absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r ${colorMap[color]} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
    </motion.div>
  );
}

function ComplianceGauge({ score = 0, size = 180 }) {
  const radius = 78;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(score, 100) / 100;
  const offset = circumference * (1 - progress);

  const getColor = (s) => {
    if (s >= 80) return '#059669';
    if (s >= 50) return '#d97706';
    return '#dc2626';
  };

  const getLabel = (s) => {
    if (s >= 80) return 'Good';
    if (s >= 50) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="currentColor" strokeWidth="10" className="text-gray-100 dark:text-gray-700" />
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none"
            stroke={getColor(score)}
            strokeWidth="10"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out drop-shadow-sm"
            style={{ filter: `drop-shadow(0 0 8px ${getColor(score)}40)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold" style={{ color: getColor(score) }}>{Math.round(score)}%</span>
          <span className="text-sm text-gray-500 dark:text-gray-400 capitalize">{getLabel(score)}</span>
        </div>
      </div>
    </div>
  );
}

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-100 dark:border-gray-700 p-3 text-sm">
        <p className="font-medium text-gray-900 dark:text-white mb-1">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ color: entry.color }}>
            {entry.name}: <span className="font-semibold">{entry.value}</span>
          </p>
        ))}
      </div>
    );
  }
  return null;
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await dashboardService.getFull();
      setData(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">Security compliance overview</p>
          </div>
        </div>
        <Loading message="Loading security dashboard..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">Security compliance overview</p>
          </div>
        </div>
        <ErrorState message={error} onRetry={fetchData} />
      </div>
    );
  }

  const stats = data?.stats || {};
  const riskTrends = data?.risk_trends || data?.trends || [];
  const rawRiskDistribution = data?.risk_distribution || data?.riskDistribution || [];
  const findingsByType = data?.findings_by_type || data?.findingsByType || {};
  const recentAlerts = data?.recent_alerts || data?.recentAlerts || [];
  const complianceScore = stats?.compliance_score ?? stats?.complianceScore ?? 0;
  const riskScore = stats?.risk_score ?? stats?.riskScore ?? 0;

  // Normalize risk distribution data for consistent field names
  const riskDistribution = rawRiskDistribution.map((item) => ({
    data_type: item.data_type || item.dataType || 'Unknown',
    total_count: item.total_count ?? item.count ?? 0,
    severity: item.severity || item.max_severity || 'low',
    count: item.total_count ?? item.count ?? 0,
    ...item,
  }));

  const complianceTrendData = riskTrends?.slice(-7) || [];
  const pieData = Object.entries(findingsByType).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Shield className="w-6 h-6 text-cyber-500" />
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Security Dashboard</h1>
          </div>
          <p className="text-gray-500 dark:text-gray-400 mt-1 ml-9">
            Real-time privacy compliance and risk monitoring
          </p>
        </div>
        <button onClick={fetchData} className="btn-ghost p-2" title="Refresh">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <KpiCard icon={FileText} label="Total Files" value={stats?.total_files ?? stats?.totalFiles ?? 0} color="cyber" delay={0} />
        <KpiCard icon={Search} label="Files Scanned" value={stats?.scanned_files ?? stats?.scannedFiles ?? 0} color="green" trend={12.5} delay={1} />
        <KpiCard icon={AlertTriangle} label="Active Alerts" value={stats?.active_alerts ?? stats?.activeAlerts ?? 0} color="red" delay={2} />
        <KpiCard icon={Shield} label="Compliance Score" value={complianceScore} color="purple" format="percentage" trend={5.2} delay={3} />
        <KpiCard icon={Activity} label="Risk Score" value={riskScore} color="orange" format="percentage" delay={4} />
      </div>

      {/* Security Posture Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Compliance Score */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card flex flex-col items-center"
        >
          <div className="flex items-center justify-between w-full mb-4">
            <h3 className="text-base font-semibold text-gray-900 dark:text-white">Compliance Score</h3>
            <Shield className="w-4 h-4 text-cyber-500" />
          </div>
          <ComplianceGauge score={complianceScore} size={190} />
          <div className="grid grid-cols-3 gap-4 w-full mt-6 pt-4 border-t border-gray-100 dark:border-gray-700/50">
            <div className="text-center">
              <p className="text-xs text-gray-500 dark:text-gray-400">High Risk</p>
              <p className="text-lg font-bold text-red-500">{stats?.high_risk_files ?? stats?.highRiskFiles ?? 0}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500 dark:text-gray-400">Medium</p>
              <p className="text-lg font-bold text-yellow-500">{stats?.medium_risk_files ?? stats?.mediumRiskFiles ?? 0}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500 dark:text-gray-400">Low Risk</p>
              <p className="text-lg font-bold text-emerald-500">{stats?.low_risk_files ?? stats?.lowRiskFiles ?? 0}</p>
            </div>
          </div>
        </motion.div>

        {/* Risk Score Trend */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-2 card"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-gray-900 dark:text-white">Risk Score Trend</h3>
            <div className="flex items-center gap-1 text-xs text-gray-400">
              <Clock className="w-3 h-3" /> Last 7 days
            </div>
          </div>
          {complianceTrendData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={complianceTrendData}>
                  <defs>
                    <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:opacity-20" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} fill="url(#riskGradient)" name="Risk Score" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400 dark:text-gray-500">
              <div className="text-center">
                <Activity className="w-8 h-8 mx-auto mb-2" />
                <p className="text-sm">No trend data available</p>
              </div>
            </div>
          )}
        </motion.div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card"
        >
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">Risk Distribution</h3>
          {riskDistribution.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskDistribution} barCategoryGap="20%">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:opacity-20" />
                  <XAxis dataKey="data_type" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="total_count" radius={[6, 6, 0, 0]}>
                    {riskDistribution.map((entry, index) => (
                      <Cell key={index} fill={COLORS[entry.severity?.toLowerCase()] || '#6366f1'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <Database className="w-8 h-8 mx-auto mb-2" />
                <p className="text-sm">No risk data</p>
              </div>
            </div>
          )}
        </motion.div>

        {/* Findings by Type */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card"
        >
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">Findings by Type</h3>
          {pieData.length > 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="relative">
                <ResponsiveContainer width={220} height={220}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%" cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2 ml-4">
                {pieData.map((entry, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }} />
                    <span className="text-xs text-gray-600 dark:text-gray-400 capitalize">{entry.name}</span>
                    <span className="text-xs font-semibold text-gray-900 dark:text-white">{entry.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <Search className="w-8 h-8 mx-auto mb-2" />
                <p className="text-sm">No findings data</p>
              </div>
            </div>
          )}
        </motion.div>
      </div>

      {/* Alerts + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Alerts */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="lg:col-span-2 card"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-gray-900 dark:text-white">Recent Alerts</h3>
            <Link to="/alerts" className="text-xs text-cyber-600 dark:text-cyber-400 hover:underline font-medium flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {recentAlerts.length > 0 ? (
            <div className="space-y-2">
              {recentAlerts.slice(0, 5).map((alert, i) => {
                const severity = (alert.severity || 'info').toLowerCase();
                return (
                  <motion.div
                    key={alert.id || i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  >
                    <div className={`w-2 h-2 rounded-full ${severity === 'critical' ? 'bg-red-500 animate-pulse-slow' : severity === 'high' ? 'bg-orange-500' : severity === 'medium' ? 'bg-yellow-500' : 'bg-green-500'}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                        {alert.message || alert.alert_type || alert.title || 'Alert'}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                        {alert.created_at ? new Date(alert.created_at).toLocaleString() : ''}
                      </p>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-gray-400 dark:text-gray-500">
              <Bell className="w-8 h-8 mb-2" />
              <p className="text-sm">No recent alerts</p>
            </div>
          )}
        </motion.div>

        {/* AI Recommendations Widget */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="card bg-gradient-to-br from-cyber-50 to-indigo-50 dark:from-cyber-900/20 dark:to-indigo-900/20 border-cyber-100 dark:border-cyber-800/30"
        >
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-cyber-500" />
            <h3 className="text-base font-semibold text-gray-900 dark:text-white">AI Insights</h3>
          </div>
          <div className="space-y-3">
            {[
              { text: 'GDPR compliance improvements recommended', type: 'warning' },
              { text: '3 files contain critical PII data', type: 'critical' },
              { text: 'Encryption recommended for 2 data sets', type: 'info' },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-2.5 p-3 rounded-lg bg-white/60 dark:bg-gray-800/40 backdrop-blur-sm">
                <div className={`w-1.5 h-1.5 rounded-full mt-1.5 ${
                  item.type === 'critical' ? 'bg-red-500' :
                  item.type === 'warning' ? 'bg-yellow-500' : 'bg-cyber-500'
                }`} />
                <p className="text-xs text-gray-600 dark:text-gray-400">{item.text}</p>
              </div>
            ))}
          </div>
          <button className="mt-4 w-full text-xs text-cyber-600 dark:text-cyber-400 font-medium hover:underline flex items-center justify-center gap-1">
            View all recommendations <ArrowRight className="w-3 h-3" />
          </button>
        </motion.div>
      </div>

      {/* Recent Uploads / Activity */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="card"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">Recent Activity</h3>
          <Link to="/files" className="text-xs text-cyber-600 dark:text-cyber-400 hover:underline font-medium flex items-center gap-1">
            View all <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/30">
            <div className="w-9 h-9 rounded-lg bg-cyber-100 dark:bg-cyber-900/30 flex items-center justify-center flex-shrink-0">
              <Upload className="w-4 h-4 text-cyber-600 dark:text-cyber-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">Uploads</p>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                {stats?.total_files ?? 0} total files uploaded
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/30">
            <div className="w-9 h-9 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center flex-shrink-0">
              <Search className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">Scans</p>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                {stats?.scanned_files ?? 0} files scanned
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/30">
            <div className="w-9 h-9 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
              <Cloud className="w-4 h-4 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">Cloud Assets</p>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                {stats?.protected_assets ?? stats?.protectedAssets ?? 0} protected
              </p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
