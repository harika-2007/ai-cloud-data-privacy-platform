import { useState } from 'react';
import { AlertTriangle, CheckCircle, Shield } from 'lucide-react';
import StatusBadge from '../Common/StatusBadge';
import Loading from '../Common/Loading';
import EmptyState from '../Common/EmptyState';
import ErrorState from '../Common/ErrorState';
import { DATA_TYPES } from '../../utils/constants';

const DATA_TYPE_ICONS = {
  email: '📧',
  phone: '📞',
  aadhaar: '🆔',
  pan: '💳',
  credit_card: '💳',
  ssn: '🔐',
  passport: '🛂',
  dob: '📅',
  address: '📍',
  ip_address: '🌐',
  bank_account: '🏦',
};

export default function ScanResults({ findings = [], loading = false, error = null, onRetry }) {
  const [sortField, setSortField] = useState('count');
  const [sortDirection, setSortDirection] = useState('desc');

  if (loading) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Scan Findings</h3>
        <Loading message="Loading scan results..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Scan Findings</h3>
        <ErrorState message={error} onRetry={onRetry} />
      </div>
    );
  }

  if (!findings || findings.length === 0) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Scan Findings</h3>
        <EmptyState
          title="No findings detected"
          description="No sensitive data was found in this file"
        />
      </div>
    );
  }

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedFindings = [...findings].sort((a, b) => {
    const multiplier = sortDirection === 'asc' ? 1 : -1;
    const aVal = a[sortField] || 0;
    const bVal = b[sortField] || 0;
    if (typeof aVal === 'string') return multiplier * aVal.localeCompare(bVal);
    return multiplier * (aVal - bVal);
  });

  const totalFindings = findings.reduce((sum, f) => sum + (f.count || f.total_count || 0), 0);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Scan Findings</h3>
        <div className="flex items-center gap-2 text-sm">
          <AlertTriangle className="w-4 h-4 text-orange-500" />
          <span className="text-gray-600 dark:text-gray-400">
            <strong className="text-gray-900 dark:text-white">{totalFindings}</strong> total findings
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
              <th className="table-header">Data Type</th>
              <th className="table-header">Category</th>
              <th className="table-header cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700" onClick={() => handleSort('count')}>
                Count {sortField === 'count' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th className="table-header cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700" onClick={() => handleSort('severity')}>
                Severity {sortField === 'severity' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th className="table-header hidden lg:table-cell">Risk Level</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {sortedFindings.map((finding, index) => {
              const dataTypeInfo = DATA_TYPES[finding.data_type?.toLowerCase()];
              const displayName = dataTypeInfo?.label || finding.data_type || finding.dataType || 'Unknown';
              const count = finding.count || finding.total_count || 0;
              const severity = finding.severity || finding.max_severity || 'low';
              const riskScore = finding.risk_score || finding.riskScore || 0;

              return (
                <tr key={finding.id || index} className="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                  <td className="table-cell">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{DATA_TYPE_ICONS[finding.data_type] || '📄'}</span>
                      <span className="font-medium text-gray-900 dark:text-white">{displayName}</span>
                    </div>
                  </td>
                  <td className="table-cell text-gray-500 dark:text-gray-400">
                    {finding.category || finding.data_category || 'PII'}
                  </td>
                  <td className="table-cell">
                    <span className="font-semibold text-gray-900 dark:text-white">{count.toLocaleString()}</span>
                  </td>
                  <td className="table-cell">
                    <StatusBadge status={severity} type="severity" />
                  </td>
                  <td className="table-cell hidden lg:table-cell">
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            riskScore >= 70 ? 'bg-red-500' : riskScore >= 40 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(riskScore, 100)}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400">{Math.round(riskScore)}%</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
