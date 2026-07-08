import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft, RefreshCw, AlertTriangle, Shield, Cpu, Search,
  Clock, ChevronDown, ChevronUp, Download, Share2, CheckCircle, Info,
  ExternalLink,
} from 'lucide-react';
import { scanService } from '../services/scanService';
import AIRecommendations from '../components/Scans/AIRecommendations';
import StatusBadge from '../components/Common/StatusBadge';
import Loading from '../components/Common/Loading';
import ErrorState from '../components/Common/ErrorState';
import EmptyState from '../components/Common/EmptyState';

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

function FindingCard({ finding, index }) {
  const [expanded, setExpanded] = useState(false);
  const dataTypeInfo = { email: 'Email Address', phone: 'Phone', aadhaar: 'Aadhaar', pan: 'PAN', credit_card: 'Credit Card', ssn: 'SSN', passport: 'Passport', dob: 'Date of Birth', address: 'Address', ip_address: 'IP Address', bank_account: 'Bank Account' };
  const displayName = dataTypeInfo[finding.data_type?.toLowerCase()] || finding.data_type || finding.dataType || 'Unknown';
  const count = finding.count || finding.total_count || 0;
  const severity = (finding.severity || finding.max_severity || 'low').toLowerCase();
  const riskScore = finding.risk_score ?? finding.riskScore ?? 0;
  const samples = finding.samples || finding.examples || [];

  const severityConfig = {
    critical: { color: 'red', bar: 'bg-red-500', dot: 'bg-red-500 animate-pulse-slow', bg: 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800' },
    high: { color: 'orange', bar: 'bg-orange-500', dot: 'bg-orange-500', bg: 'bg-orange-50 dark:bg-orange-900/10 border-orange-200 dark:border-orange-800' },
    medium: { color: 'yellow', bar: 'bg-yellow-500', dot: 'bg-yellow-500', bg: 'bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-800' },
    low: { color: 'green', bar: 'bg-green-500', dot: 'bg-green-500', bg: 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800' },
  };
  const config = severityConfig[severity] || severityConfig.low;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`rounded-xl border transition-all duration-200 ${expanded ? 'shadow-md' : 'hover:shadow-sm'} ${config.bg}`}
    >
      <div
        className="flex items-center gap-4 p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-2xl">{DATA_TYPE_ICONS[finding.data_type] || '📄'}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 dark:text-white">{displayName}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{finding.category || finding.data_category || 'PII'}</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-lg font-bold text-gray-900 dark:text-white">{count.toLocaleString()}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">instances</p>
          </div>
          <StatusBadge status={severity} type="severity" dot />
        </div>
        <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-0 space-y-3 border-t border-gray-200/50 dark:border-gray-700/50">
              {/* Risk Score Bar */}
              <div className="pt-3">
                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                  <span>Risk Level</span>
                  <span className="font-semibold">{Math.round(riskScore)}%</span>
                </div>
                <div className="progress-bar">
                  <div className={`h-2 rounded-full ${config.bar}`} style={{ width: `${Math.min(riskScore, 100)}%` }} />
                </div>
              </div>

              {/* Category & Recommendations */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-white/60 dark:bg-gray-800/40">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Category</p>
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mt-0.5">{finding.category || finding.data_category || 'Sensitive Data'}</p>
                </div>
                <div className="p-3 rounded-lg bg-white/60 dark:bg-gray-800/40">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Confidence</p>
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mt-0.5">{finding.confidence || finding.confidence_score || 'High'}</p>
                </div>
              </div>

              {/* Samples */}
              {samples.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">Sample matches ({samples.length})</p>
                  <div className="space-y-1">
                    {samples.slice(0, 3).map((sample, i) => (
                      <div key={i} className="p-2 rounded bg-white/60 dark:bg-gray-800/40 font-mono text-xs text-gray-600 dark:text-gray-400 truncate">
                        {typeof sample === 'string' ? sample : sample.value || sample.text || JSON.stringify(sample)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendation */}
              <div className="flex gap-2 pt-1">
                <Link to={`/reports/generate?file=${finding.file_id}`} className="btn-ghost text-xs">
                  <ExternalLink className="w-3 h-3" /> View in report
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function RiskAssessment({ riskData, onRetry }) {
  if (!riskData) {
    return (
      <div className="card text-center py-12">
        <Shield className="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
        <p className="text-gray-500 dark:text-gray-400">No risk assessment available</p>
        <button onClick={onRetry} className="btn-ghost mt-4 text-sm">Refresh</button>
      </div>
    );
  }

  const score = riskData.overall_score ?? riskData.risk_score ?? riskData.riskScore ?? 0;
  const level = riskData.risk_level ?? riskData.riskLevel ?? (score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low');
  const breakdown = riskData.breakdown || riskData.risk_factors || [];
  const radius = 72;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(score, 100) / 100;
  const offset = circumference * (1 - progress);

  const getScoreColor = (s) => {
    if (s >= 70) return '#ef4444';
    if (s >= 40) return '#eab308';
    return '#22c55e';
  };

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Risk Assessment</h3>

      <div className="flex flex-col lg:flex-row items-center gap-8">
        {/* Score Gauge */}
        <div className="flex-shrink-0">
          <div className="relative" style={{ width: 180, height: 180 }}>
            <svg width="180" height="180" className="transform -rotate-90">
              <circle cx="90" cy="90" r={radius} fill="none" stroke="currentColor" strokeWidth="12" className="text-gray-100 dark:text-gray-700" />
              <circle
                cx="90" cy="90" r={radius}
                fill="none"
                stroke={getScoreColor(score)}
                strokeWidth="12"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                strokeLinecap="round"
                className="transition-all duration-1000 ease-out"
                style={{ filter: `drop-shadow(0 0 6px ${getScoreColor(score)}40)` }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-bold text-gray-900 dark:text-white">{Math.round(score)}</span>
              <span className="text-sm text-gray-500 dark:text-gray-400">out of 100</span>
            </div>
          </div>
        </div>

        {/* Details */}
        <div className="flex-1 w-full space-y-4">
          <div className={`p-4 rounded-xl border ${score >= 70 ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800' : score >= 40 ? 'bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-800' : 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'}`}>
            <div className="flex items-center gap-3">
              {score >= 70 ? <AlertTriangle className="w-5 h-5 text-red-500" /> : score >= 40 ? <Info className="w-5 h-5 text-yellow-500" /> : <CheckCircle className="w-5 h-5 text-green-500" />}
              <div>
                <p className={`text-lg font-semibold ${score >= 70 ? 'text-red-600 dark:text-red-400' : score >= 40 ? 'text-yellow-600 dark:text-yellow-400' : 'text-green-600 dark:text-green-400'}`}>
                  {level.charAt(0).toUpperCase() + level.slice(1)} Risk
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {score >= 70 ? 'Immediate action recommended' : score >= 40 ? 'Review medium-risk items' : 'Good compliance posture'}
                </p>
              </div>
            </div>
          </div>

          {breakdown.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Risk Breakdown</h4>
              <div className="space-y-2">
                {breakdown.map((factor, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                    <span className="text-sm text-gray-700 dark:text-gray-300">{factor.name || factor.factor || factor.label}</span>
                    <div className="flex items-center gap-3">
                      <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${(factor.score || factor.value || 0) >= 70 ? 'bg-red-500' : (factor.score || factor.value || 0) >= 40 ? 'bg-yellow-500' : 'bg-green-500'}`}
                          style={{ width: `${Math.min(factor.score || factor.value || 0, 100)}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 w-8 text-right">{Math.round(factor.score || factor.value || 0)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            {riskData.total_findings !== undefined && (
              <div className="p-3 bg-gray-50 dark:bg-gray-800/30 rounded-lg text-center">
                <p className="text-lg font-bold text-gray-900 dark:text-white">{riskData.total_findings}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Findings</p>
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
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ScanResults() {
  const { fileId } = useParams();
  const [findings, setFindings] = useState([]);
  const [riskData, setRiskData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('findings');
  const [findingsSort, setFindingsSort] = useState('count');
  const [sortDir, setSortDir] = useState('desc');

  const fetchResults = useCallback(async () => {
    if (!fileId) return;
    setLoading(true);
    setError(null);
    try {
      const [resultsData, riskResult] = await Promise.all([
        scanService.getScanResults(fileId),
        scanService.getRiskAssessment(fileId),
      ]);
      setFindings(resultsData?.findings || resultsData?.results || resultsData || []);
      setRiskData(riskResult);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load scan results');
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  useEffect(() => { fetchResults(); }, [fetchResults]);

  const tabs = [
    { id: 'findings', label: 'Findings', icon: Search, count: findings.length },
    { id: 'risk', label: 'Risk Assessment', icon: Shield },
    { id: 'ai', label: 'AI Analysis', icon: Cpu },
  ];

  const totalFindings = findings.reduce((sum, f) => sum + (f.count || f.total_count || 0), 0);

  const handleSort = (field) => {
    if (findingsSort === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setFindingsSort(field); setSortDir('desc'); }
  };

  const sortedFindings = [...findings].sort((a, b) => {
    const m = sortDir === 'asc' ? 1 : -1;
    const aVal = a[findingsSort] || 0;
    const bVal = b[findingsSort] || 0;
    if (typeof aVal === 'string') return m * aVal.localeCompare(bVal);
    return m * (aVal - bVal);
  });

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Link to="/files" className="btn-icon"><ArrowLeft className="w-5 h-5" /></Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Scan Results</h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm">Loading scan data...</p>
          </div>
        </div>
        <Loading message="Loading scan results..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Link to="/files" className="btn-icon"><ArrowLeft className="w-5 h-5" /></Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Scan Results</h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm">File: {fileId?.slice(0, 8)}...</p>
          </div>
        </div>
        <ErrorState message={error} onRetry={fetchResults} />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <Link to="/files" className="btn-icon"><ArrowLeft className="w-5 h-5" /></Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Scan Results</h1>
              {findings.length > 0 && (
                <span className="px-2.5 py-0.5 bg-cyber-100 dark:bg-cyber-900/30 text-cyber-700 dark:text-cyber-400 text-xs font-medium rounded-full">
                  {totalFindings} findings
                </span>
              )}
            </div>
            <p className="text-gray-500 dark:text-gray-400 text-sm mt-1 flex items-center gap-1">
              <Clock className="w-3 h-3" /> File ID: {fileId?.slice(0, 8)}...
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-ghost text-sm"><Download className="w-4 h-4" /> Export</button>
          <button className="btn-ghost text-sm"><Share2 className="w-4 h-4" /> Share</button>
          <button onClick={fetchResults} className="btn-ghost"><RefreshCw className="w-4 h-4" /></button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-surface-card-dark rounded-t-xl px-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all duration-200 -mb-px ${
              activeTab === tab.id
                ? 'border-cyber-500 text-cyber-600 dark:text-cyber-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
            }`}
          >
            <tab.icon className={`w-4 h-4 ${activeTab === tab.id ? 'text-cyber-500' : 'text-gray-400'}`} />
            {tab.label}
            {tab.count !== undefined && (
              <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded-full ${
                activeTab === tab.id ? 'bg-cyber-100 dark:bg-cyber-900/30 text-cyber-600 dark:text-cyber-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-500'
              }`}>
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'findings' && (
          <motion.div key="findings" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            {sortedFindings.length > 0 ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    <span className="font-semibold text-gray-900 dark:text-white">{totalFindings.toLocaleString()}</span> total sensitive data instances found
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">Sort:</span>
                    <button onClick={() => handleSort('count')} className={`text-xs px-2 py-1 rounded ${findingsSort === 'count' ? 'bg-cyber-50 dark:bg-cyber-900/20 text-cyber-600 dark:text-cyber-400' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'}`}>
                      Count {findingsSort === 'count' && (sortDir === 'asc' ? '↑' : '↓')}
                    </button>
                    <button onClick={() => handleSort('severity')} className={`text-xs px-2 py-1 rounded ${findingsSort === 'severity' ? 'bg-cyber-50 dark:bg-cyber-900/20 text-cyber-600 dark:text-cyber-400' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'}`}>
                      Severity {findingsSort === 'severity' && (sortDir === 'asc' ? '↑' : '↓')}
                    </button>
                  </div>
                </div>
                {sortedFindings.map((finding, idx) => (
                  <FindingCard key={finding.id || idx} finding={finding} index={idx} />
                ))}
              </div>
            ) : (
              <EmptyState icon={Search} title="No findings detected" description="No sensitive data was found in this file" />
            )}
          </motion.div>
        )}

        {activeTab === 'risk' && (
          <motion.div key="risk" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <RiskAssessment riskData={riskData} onRetry={fetchResults} />
          </motion.div>
        )}

        {activeTab === 'ai' && (
          <motion.div key="ai" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <AIRecommendations fileId={fileId} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
