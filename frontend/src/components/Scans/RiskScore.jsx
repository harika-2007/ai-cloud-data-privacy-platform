import { AlertTriangle, CheckCircle, Info, Shield } from 'lucide-react';
import Loading from '../Common/Loading';
import ErrorState from '../Common/ErrorState';

export default function RiskScore({ riskData = null, loading = false, error = null, onRetry }) {
  if (loading) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Risk Assessment</h3>
        <Loading message="Calculating risk score..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Risk Assessment</h3>
        <ErrorState message={error} onRetry={onRetry} />
      </div>
    );
  }

  if (!riskData) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Risk Assessment</h3>
        <div className="flex flex-col items-center justify-center py-8 text-gray-400 dark:text-gray-500">
          <Shield className="w-12 h-12 mb-3" />
          <p>No risk assessment available</p>
        </div>
      </div>
    );
  }

  const score = riskData.overall_score ?? riskData.risk_score ?? riskData.riskScore ?? 0;
  const level = riskData.risk_level ?? riskData.riskLevel ?? (score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low');
  const breakdown = riskData.breakdown || riskData.risk_factors || [];

  const getScoreColor = (s) => {
    if (s >= 70) return { text: 'text-red-600', bg: 'bg-red-50 dark:bg-red-900/10', border: 'border-red-200 dark:border-red-800' };
    if (s >= 40) return { text: 'text-yellow-600', bg: 'bg-yellow-50 dark:bg-yellow-900/10', border: 'border-yellow-200 dark:border-yellow-800' };
    return { text: 'text-green-600', bg: 'bg-green-50 dark:bg-green-900/10', border: 'border-green-200 dark:border-green-800' };
  };

  const getLevelIcon = (lvl) => {
    switch (lvl.toLowerCase()) {
      case 'critical':
      case 'high':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'medium':
        return <Info className="w-5 h-5 text-yellow-500" />;
      default:
        return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
  };

  const colors = getScoreColor(score);
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(score, 100) / 100;
  const offset = circumference * (1 - progress);

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Risk Assessment</h3>

      <div className="flex flex-col lg:flex-row items-center gap-8">
        {/* Score Gauge */}
        <div className="flex-shrink-0">
          <div className="relative flex items-center justify-center">
            <svg width="180" height="180" className="transform -rotate-90">
              <circle cx="90" cy="90" r={radius} fill="none" stroke="#e5e7eb" strokeWidth="14" />
              <circle
                cx="90" cy="90" r={radius}
                fill="none"
                stroke={score >= 70 ? '#ef4444' : score >= 40 ? '#eab308' : '#22c55e'}
                strokeWidth="14"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                strokeLinecap="round"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className="text-4xl font-bold text-gray-900 dark:text-white">{Math.round(score)}</span>
              <span className="text-sm text-gray-500 dark:text-gray-400">out of 100</span>
            </div>
          </div>
        </div>

        {/* Details */}
        <div className="flex-1 w-full space-y-4">
          <div className={`flex items-center gap-3 p-4 rounded-xl ${colors.bg} ${colors.border} border`}>
            {getLevelIcon(level)}
            <div>
              <p className={`text-lg font-semibold ${colors.text}`}>
                {level.charAt(0).toUpperCase() + level.slice(1)} Risk
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {score >= 70
                  ? 'Immediate action recommended'
                  : score >= 40
                  ? 'Review and address medium-risk items'
                  : 'Good compliance posture'}
              </p>
            </div>
          </div>

          {breakdown.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Risk Breakdown</h4>
              <div className="space-y-2">
                {breakdown.map((factor, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                    <span className="text-sm text-gray-700 dark:text-gray-300">{factor.name || factor.factor || factor.label}</span>
                    <div className="flex items-center gap-3">
                      <div className="w-20 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${
                            (factor.score || factor.value || 0) >= 70 ? 'bg-red-500' : (factor.score || factor.value || 0) >= 40 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(factor.score || factor.value || 0, 100)}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400 w-8 text-right">
                        {Math.round(factor.score || factor.value || 0)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
            {riskData.total_findings !== undefined && (
              <div className="p-3 bg-gray-50 dark:bg-gray-800/30 rounded-lg text-center">
                <p className="text-lg font-bold text-gray-900 dark:text-white">{riskData.total_findings}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Total Findings</p>
              </div>
            )}
            {riskData.critical_count !== undefined && (
              <div className="p-3 bg-red-50 dark:bg-red-900/10 rounded-lg text-center">
                <p className="text-lg font-bold text-red-600 dark:text-red-400">{riskData.critical_count}</p>
                <p className="text-xs text-red-500 dark:text-red-400">Critical</p>
              </div>
            )}
            {riskData.high_count !== undefined && (
              <div className="p-3 bg-orange-50 dark:bg-orange-900/10 rounded-lg text-center">
                <p className="text-lg font-bold text-orange-600 dark:text-orange-400">{riskData.high_count}</p>
                <p className="text-xs text-orange-500 dark:text-orange-400">High</p>
              </div>
            )}
            {riskData.medium_count !== undefined && (
              <div className="p-3 bg-yellow-50 dark:bg-yellow-900/10 rounded-lg text-center">
                <p className="text-lg font-bold text-yellow-600 dark:text-yellow-400">{riskData.medium_count}</p>
                <p className="text-xs text-yellow-500 dark:text-yellow-400">Medium</p>
              </div>
            )}
            {riskData.low_count !== undefined && (
              <div className="p-3 bg-green-50 dark:bg-green-900/10 rounded-lg text-center">
                <p className="text-lg font-bold text-green-600 dark:text-green-400">{riskData.low_count}</p>
                <p className="text-xs text-green-500 dark:text-green-400">Low</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
