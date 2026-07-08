import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart3, FileText, Download, RefreshCw, ChevronLeft, ChevronRight,
  Calendar, Clock, Plus, X, Shield, AlertTriangle, FileSpreadsheet,
  Search, Filter,
} from 'lucide-react';
import { reportService } from '../services/reportService';
import { fileService } from '../services/fileService';
import StatusBadge from '../components/Common/StatusBadge';
import Loading from '../components/Common/Loading';
import ErrorState from '../components/Common/ErrorState';
import EmptyState from '../components/Common/EmptyState';
import toast from 'react-hot-toast';

function ReportCard({ report, downloadingId, onDownload }) {
  const reportName = report.name || report.title || report.report_name || `Report #${report.id}`;
  const reportType = report.type || report.report_type || report.format || 'compliance';
  const createdAt = report.created_at || report.generated_at || report.createdAt;
  const status = report.status || 'completed';
  const fileCount = report.file_count || report.total_files || 0;
  const findingCount = report.finding_count || report.total_findings || 0;
  const riskScore = report.risk_score ?? report.riskScore;
  const complianceScore = report.compliance_score ?? report.complianceScore;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="group bg-white dark:bg-surface-card-dark rounded-xl border border-gray-100 dark:border-gray-700/50 p-5 hover:shadow-md hover:border-gray-200 dark:hover:border-gray-600/50 transition-all duration-300"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 min-w-0">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-cyber-100 to-cyber-50 dark:from-cyber-900/30 dark:to-cyber-800/20 flex items-center justify-center flex-shrink-0">
            <FileText className="w-5 h-5 text-cyber-600 dark:text-cyber-400" />
          </div>
          <div className="min-w-0">
            <Link
              to={`/reports/${report.id}`}
              className="text-sm font-semibold text-gray-900 dark:text-white hover:text-cyber-600 dark:hover:text-cyber-400 truncate block max-w-[250px]"
            >
              {reportName}
            </Link>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5">
              <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {createdAt ? new Date(createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A'}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {reportType}
              </span>
              <StatusBadge status={status} />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={() => onDownload(report)}
            disabled={downloadingId === report.id}
            className="p-2 rounded-lg text-gray-400 hover:text-cyber-600 hover:bg-cyber-50 dark:hover:bg-cyber-900/20 transition-colors"
            title="Download"
          >
            {downloadingId === report.id ? (
              <div className="w-4 h-4 border-2 border-cyber-500 border-t-transparent rounded-full animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="flex gap-4 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700/50">
        {findingCount > 0 && (
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Findings: <span className="font-semibold text-gray-900 dark:text-white">{findingCount}</span>
          </div>
        )}
        {riskScore !== undefined && (
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Risk Score: <span className={`font-semibold ${riskScore >= 70 ? 'text-red-500' : riskScore >= 40 ? 'text-yellow-500' : 'text-green-500'}`}>{riskScore}%</span>
          </div>
        )}
        {complianceScore !== undefined && (
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Compliance: <span className={`font-semibold ${complianceScore >= 80 ? 'text-emerald-500' : complianceScore >= 50 ? 'text-yellow-500' : 'text-red-500'}`}>{complianceScore}%</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function Reports() {
  const navigate = useNavigate();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [downloadingId, setDownloadingId] = useState(null);

  // Generate modal
  const [showGenerate, setShowGenerate] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [form, setForm] = useState({
    file_id: '',
    title: 'Compliance Report',
    report_type: 'compliance',
    include_ai_summary: true,
  });
  const [availableFiles, setAvailableFiles] = useState([]);

  const fetchReports = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await reportService.getReports({ page, page_size: 20 });
      const reportList = result?.reports || [];
      setReports(Array.isArray(reportList) ? reportList : []);
      const total = result?.total || reportList.length;
      setTotalPages(Math.ceil(total / 20) || 1);
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { fetchReports(); }, [fetchReports]);

  const openGenerateModal = async () => {
    try {
      const result = await fileService.getFiles({ page_size: 100 });
      setAvailableFiles(Array.isArray(result?.files) ? result.files : []);
    } catch { setAvailableFiles([]); }
    setForm({ file_id: '', title: 'Compliance Report', report_type: 'compliance', include_ai_summary: true });
    setShowGenerate(true);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await reportService.generateReport(form);
      toast.success('Report generated');
      setShowGenerate(false);
      fetchReports();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (report) => {
    setDownloadingId(report.id);
    try {
      const blob = await reportService.downloadReport(report.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.name || report.title || 'report'}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      toast.error('Download failed');
    } finally {
      setDownloadingId(null);
    }
  };

  if (loading && reports.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div><h1 className="text-2xl font-bold text-gray-900 dark:text-white">Reports</h1><p className="text-gray-500 dark:text-gray-400 mt-1">Compliance & audit reports</p></div>
        </div>
        <Loading message="Loading reports..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div><h1 className="text-2xl font-bold text-gray-900 dark:text-white">Reports</h1><p className="text-gray-500 dark:text-gray-400 mt-1">Compliance & audit reports</p></div>
        </div>
        <ErrorState message={error} onRetry={fetchReports} />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-3">
            <BarChart3 className="w-6 h-6 text-cyber-500" />
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Reports</h1>
          </div>
          <p className="text-gray-500 dark:text-gray-400 mt-1 ml-9">
            {reports.length > 0 ? `${reports.length} report${reports.length !== 1 ? 's' : ''} generated` : 'Generate compliance and audit reports'}
          </p>
        </div>
        <button onClick={openGenerateModal} className="btn-primary">
          <Plus className="w-4 h-4" /> Generate Report
        </button>
      </div>

      {/* Stats Bar */}
      {reports.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-white dark:bg-surface-card-dark border border-gray-100 dark:border-gray-700/50 text-center">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{reports.filter(r => r.status === 'completed').length}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Completed</p>
          </div>
          <div className="p-4 rounded-xl bg-white dark:bg-surface-card-dark border border-gray-100 dark:border-gray-700/50 text-center">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{reports.filter(r => r.status === 'generating' || r.status === 'pending').length}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Generating</p>
          </div>
          <div className="p-4 rounded-xl bg-white dark:bg-surface-card-dark border border-gray-100 dark:border-gray-700/50 text-center">
            <p className="text-2xl font-bold text-red-500">{reports.reduce((s, r) => s + (r.risk_score || 0), 0) / Math.max(reports.length, 1) || 0}%</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Avg Risk</p>
          </div>
          <div className="p-4 rounded-xl bg-white dark:bg-surface-card-dark border border-gray-100 dark:border-gray-700/50 text-center">
            <p className="text-2xl font-bold text-emerald-500">{reports.reduce((s, r) => s + (r.compliance_score || 0), 0) / Math.max(reports.length, 1) || 0}%</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Avg Compliance</p>
          </div>
        </div>
      )}

      {/* Report List */}
      {reports.length === 0 ? (
        <EmptyState
          icon={BarChart3}
          title="No reports generated"
          description="Upload and scan files first, then generate compliance reports"
          action={<button onClick={openGenerateModal} className="btn-primary">Generate Report</button>}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {reports.map((report) => (
            <ReportCard key={report.id} report={report} downloadingId={downloadingId} onDownload={handleDownload} />
          ))}
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

      {/* Generate Modal */}
      <AnimatePresence>
        {showGenerate && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={() => setShowGenerate(false)}
          >
            <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" />
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-lg p-6 z-10 border border-gray-200 dark:border-gray-700"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyber-100 to-cyber-50 dark:from-cyber-900/30 dark:to-cyber-800/20 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-cyber-600 dark:text-cyber-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Generate Report</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Create a new compliance report</p>
                  </div>
                </div>
                <button onClick={() => setShowGenerate(false)} className="btn-icon">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="label">Report Title</label>
                  <input type="text" className="input-field" value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    placeholder="e.g., Monthly Compliance Report" />
                </div>

                <div>
                  <label className="label">Report Type</label>
                  <select className="input-field" value={form.report_type}
                    onChange={(e) => setForm({ ...form, report_type: e.target.value })}>
                    <option value="compliance">Compliance Report</option>
                    <option value="audit">Audit Report</option>
                    <option value="summary">Summary Report</option>
                    <option value="detailed">Detailed Analysis</option>
                  </select>
                </div>

                <div>
                  <label className="label">File (optional)</label>
                  <select className="input-field" value={form.file_id}
                    onChange={(e) => setForm({ ...form, file_id: e.target.value })}>
                    <option value="">All files (summary report)</option>
                    {availableFiles.map((file) => (
                      <option key={file.id} value={file.id}>
                        {file.filename || file.original_filename || `File #${file.id}`}
                      </option>
                    ))}
                  </select>
                </div>

                <label className="flex items-center gap-2.5 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                  <input type="checkbox" checked={form.include_ai_summary}
                    onChange={(e) => setForm({ ...form, include_ai_summary: e.target.checked })}
                    className="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-cyber-600 focus:ring-cyber-500/50" />
                  <div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Include AI Analysis</span>
                    <p className="text-xs text-gray-400 dark:text-gray-500">Add AI-generated compliance recommendations</p>
                  </div>
                </label>
              </div>

              <div className="flex gap-3 mt-6 pt-4 border-t border-gray-100 dark:border-gray-700/50">
                <button onClick={handleGenerate} disabled={generating || !form.title.trim()} className="btn-primary flex-1">
                  {generating ? (
                    <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Generating...</>
                  ) : (
                    <><FileText className="w-4 h-4" /> Generate</>
                  )}
                </button>
                <button onClick={() => setShowGenerate(false)} className="btn-secondary">Cancel</button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
