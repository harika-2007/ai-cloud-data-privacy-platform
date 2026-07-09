import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FiFileText,
  FiDownload,
  FiRefreshCw,
  FiChevronLeft,
  FiChevronRight,
  FiCalendar,
  FiClock,
} from 'react-icons/fi';
import StatusBadge from '../Common/StatusBadge';
import Loading from '../Common/Loading';
import EmptyState from '../Common/EmptyState';
import ErrorState from '../Common/ErrorState';
import { reportService } from '../../services/reportService';

export default function ReportList({
  reports = [],
  loading = false,
  error = null,
  onRetry,
  page = 1,
  totalPages = 1,
  onPageChange,
}) {
  const [downloadingId, setDownloadingId] = useState(null);

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
      console.error('Download failed:', err);
    } finally {
      setDownloadingId(null);
    }
  };

  if (loading) {
    return <Loading message="Loading reports..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={onRetry} />;
  }

  if (!reports || reports.length === 0) {
    return (
      <EmptyState
        icon={<FiFileText className="w-12 h-12" />}
        title="No reports generated"
        description="Upload and scan files first, then generate compliance reports"
        action={
          <Link to="/upload" className="btn-primary text-sm">
            Upload Files
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button onClick={onRetry} className="btn-ghost p-2" title="Refresh">
            <FiRefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="grid gap-4">
        {reports.map((report) => {
          const reportName = report.name || report.title || report.report_name || `Report #${report.id}`;
          const reportType = report.type || report.report_type || report.format || 'compliance';
          const createdAt = report.created_at || report.generated_at || report.createdAt;
          const status = report.status || 'completed';
          const fileCount = report.file_count || report.total_files || 0;
          const findingCount = report.finding_count || report.total_findings || 0;

          return (
            <div
              key={report.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 min-w-0">
                  <div className="w-10 h-10 bg-cyber-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FiFileText className="w-5 h-5 text-cyber-600" />
                  </div>
                  <div className="min-w-0">
                    <Link
                      to={`/reports/${report.id}`}
                      className="text-sm font-semibold text-gray-900 hover:text-cyber-600 truncate block"
                    >
                      {reportName}
                    </Link>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5">
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <FiCalendar className="w-3 h-3" />
                        {createdAt
                          ? new Date(createdAt).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              year: 'numeric',
                            })
                          : 'N/A'}
                      </span>
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <FiClock className="w-3 h-3" />
                        {reportType}
                      </span>
                      <StatusBadge status={status} />
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {fileCount > 0 && (
                    <span className="text-xs text-gray-500 hidden sm:block">
                      {fileCount} file{fileCount !== 1 ? 's' : ''}
                    </span>
                  )}
                  <button
                    onClick={() => handleDownload(report)}
                    disabled={downloadingId === report.id}
                    className="btn-ghost p-2 text-cyber-600 hover:bg-cyber-50"
                    title="Download report"
                  >
                    {downloadingId === report.id ? (
                      <div className="w-4 h-4 border-2 border-cyber-600 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <FiDownload className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Stats Row */}
              <div className="flex gap-4 mt-3 pt-3 border-t border-gray-100">
                {findingCount > 0 && (
                  <div className="text-xs text-gray-500">
                    Findings: <span className="font-semibold text-gray-700">{findingCount}</span>
                  </div>
                )}
                {report.risk_score !== undefined && (
                  <div className="text-xs text-gray-500">
                    Risk Score: <span className="font-semibold text-gray-700">{report.risk_score}%</span>
                  </div>
                )}
                {report.compliance_score !== undefined && (
                  <div className="text-xs text-gray-500">
                    Compliance: <span className="font-semibold text-gray-700">{report.compliance_score}%</span>
                  </div>
                )}
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
