import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Download, FileText, Calendar, Clock, Shield, AlertTriangle,
  CheckCircle, AlertOctagon, Info, BarChart3, Loader2, ExternalLink,
} from 'lucide-react';
import { reportService } from '../services/reportService';
import StatusBadge from '../components/Common/StatusBadge';
import Loading from '../components/Common/Loading';
import ErrorState from '../components/Common/ErrorState';
import toast from 'react-hot-toast';

export default function ReportDetail() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloading, setDownloading] = useState(false);

  const fetchReport = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const result = await reportService.getReport(id);
      setReport(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchReport(); }, [fetchReport]);

  const handleDownload = async () => {
    if (!report) return;
    setDownloading(true);
    try {
      const blob = await reportService.downloadReport(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.name || report.title || 'report'}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success('Report downloaded');
    } catch {
      toast.error('Download failed');
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Link to="/reports" className="btn-icon"><ArrowLeft className="w-5 h-5" /></Link>
          <div><h1 className="text-2xl font-bold text-gray-900 dark:text-white">Report</h1><p className="text-gray-500 dark:text-gray-400 text-sm">Loading report...</p></div>
        </div>
        <Loading message="Loading report details..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Link to="/reports" className="btn-icon"><ArrowLeft className="w-5 h-5" /></Link>
          <div><h1 className="text-2xl font-bold text-gray-900 dark:text-white">Report</h1></div>
        </div>
        <ErrorState message={error} onRetry={fetchReport} />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Link to="/reports" className="btn-icon"><ArrowLeft className="w-5 h-5" /></Link>
          <div><h1 className="text-2xl font-bold text-gray-900 dark:text-white">Not Found</h1></div>
        </div>
        <div className="card text-center py-12 text-gray-400"><FileText className="w-12 h-12 mx-auto mb-3" /><p>Report not found</p></div>
      </div>
    );
  }

  const reportName = report.name || report.title || `Report #${report.id}`;
  const reportType = report.type || report.report_type || 'compliance';
  const createdAt = report.created_at || report.generated_at || report.createdAt;
  const status = report.status || 'completed';
  const riskScore = report.risk_score ?? report.riskScore;
  const complianceScore = report.compliance_score ?? report.complianceScore;
  const summary = report.summary || report.executive_summary || '';
  const findings = report.findings || report.results || [];

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <Link to="/reports" className="btn-icon"><ArrowLeft className="w-5 h-5" /></Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{reportName}</h1>
            <div className="flex items-center gap-3 mt-1 flex-wrap">
              <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {createdAt ? new Date(createdAt).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : 'N/A'}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {reportType}
              </span>
              <StatusBadge status={status} />
            </div>
          </div>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleDownload}
          disabled={downloading}
          className="btn-primary"
        >
          {downloading ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Downloading...</>
          ) : (
            <><Download className="w-4 h-4" /> Download PDF</>
          )}
        </motion.button>
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-5 rounded-xl bg-gradient-to-br from-cyber-50 to-indigo-50 dark:from-cyber-900/20 dark:to-indigo-900/20 border border-cyber-100 dark:border-cyber-800/30"
        >
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-4 h-4 text-cyber-600 dark:text-cyber-400" />
            <p className="text-xs font-semibold text-cyber-600 dark:text-cyber-400 uppercase tracking-wider">Report Type</p>
          </div>
          <p className="text-2xl font-bold text-cyber-800 dark:text-cyber-200 capitalize">{reportType}</p>
          <p className="text-xs text-cyber-600 dark:text-cyber-400 mt-1 capitalize">Status: {status}</p>
        </motion.div>

        {riskScore !== undefined && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className={`p-5 rounded-xl border ${
              riskScore >= 70
                ? 'bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/10 border-red-200 dark:border-red-800/30'
                : riskScore >= 40
                ? 'bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/10 border-yellow-200 dark:border-yellow-800/30'
                : 'bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/10 border-green-200 dark:border-green-800/30'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              {riskScore >= 70 ? <AlertTriangle className="w-4 h-4 text-red-500" /> : riskScore >= 40 ? <AlertOctagon className="w-4 h-4 text-yellow-500" /> : <CheckCircle className="w-4 h-4 text-green-500" />}
              <p className={`text-xs font-semibold uppercase tracking-wider ${riskScore >= 70 ? 'text-red-600 dark:text-red-400' : riskScore >= 40 ? 'text-yellow-600 dark:text-yellow-400' : 'text-green-600 dark:text-green-400'}`}>
                Risk Score
              </p>
            </div>
            <p className={`text-2xl font-bold ${riskScore >= 70 ? 'text-red-700 dark:text-red-300' : riskScore >= 40 ? 'text-yellow-700 dark:text-yellow-300' : 'text-green-700 dark:text-green-300'}`}>
              {Math.round(riskScore)}%
            </p>
          </motion.div>
        )}

        {complianceScore !== undefined && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className={`p-5 rounded-xl border ${
              complianceScore >= 80
                ? 'bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/10 border-green-200 dark:border-green-800/30'
                : complianceScore >= 50
                ? 'bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/10 border-yellow-200 dark:border-yellow-800/30'
                : 'bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/10 border-red-200 dark:border-red-800/30'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <Shield className={`w-4 h-4 ${complianceScore >= 80 ? 'text-green-500' : complianceScore >= 50 ? 'text-yellow-500' : 'text-red-500'}`} />
              <p className={`text-xs font-semibold uppercase tracking-wider ${complianceScore >= 80 ? 'text-green-600 dark:text-green-400' : complianceScore >= 50 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'}`}>
                Compliance Score
              </p>
            </div>
            <p className={`text-2xl font-bold ${complianceScore >= 80 ? 'text-green-700 dark:text-green-300' : complianceScore >= 50 ? 'text-yellow-700 dark:text-yellow-300' : 'text-red-700 dark:text-red-300'}`}>
              {Math.round(complianceScore)}%
            </p>
          </motion.div>
        )}
      </div>

      {/* Executive Summary */}
      {summary && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyber-500" />
            Executive Summary
          </h3>
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50">
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{summary}</p>
          </div>
        </motion.div>
      )}

      {/* Findings Table */}
      {findings.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card"
        >
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-500" />
            Findings ({findings.length})
          </h3>
          <div className="table-container">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="table-header">Data Type</th>
                  <th className="table-header">Category</th>
                  <th className="table-header">Count</th>
                  <th className="table-header">Severity</th>
                  <th className="table-header">Risk Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
                {findings.map((finding, idx) => (
                  <tr key={finding.id || idx} className="table-row">
                    <td className="table-cell font-medium text-gray-900 dark:text-white">
                      {finding.data_type || finding.dataType || 'Unknown'}
                    </td>
                    <td className="table-cell text-gray-500 dark:text-gray-400">
                      {finding.category || finding.data_category || 'PII'}
                    </td>
                    <td className="table-cell">
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {finding.count || finding.total_count || 0}
                      </span>
                    </td>
                    <td className="table-cell">
                      <StatusBadge status={finding.severity || 'low'} type="severity" dot />
                    </td>
                    <td className="table-cell">
                      <div className="flex items-center gap-2">
                        <div className="progress-bar w-20">
                          <div
                            className={`h-2 rounded-full ${(finding.risk_score || 0) >= 70 ? 'progress-fill-danger' : (finding.risk_score || 0) >= 40 ? 'progress-fill-warning' : 'progress-fill-success'}`}
                            style={{ width: `${Math.min(finding.risk_score || finding.riskScore || 0, 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400">{Math.round(finding.risk_score || finding.riskScore || 0)}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Empty State */}
      {findings.length === 0 && !summary && (
        <div className="card text-center py-12">
          <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
          <p className="text-gray-500 dark:text-gray-400 mb-4">No detailed data available for this report</p>
          <button onClick={handleDownload} disabled={downloading} className="btn-primary">
            <Download className="w-4 h-4" /> Download Report
          </button>
        </div>
      )}
    </div>
  );
}
