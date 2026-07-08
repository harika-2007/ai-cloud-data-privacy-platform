import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FiFile, FiTrash2, FiDownload, FiSearch, FiRefreshCw, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import StatusBadge from '../Common/StatusBadge';
import Loading from '../Common/Loading';
import EmptyState from '../Common/EmptyState';
import ErrorState from '../Common/ErrorState';

export default function FileList({ files = [], loading = false, error = null, onRetry, onDelete, onScan, page = 1, totalPages = 1, onPageChange }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  const filteredFiles = files.filter((file) =>
    file.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    file.original_filename?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDelete = async (id) => {
    setDeletingId(id);
    try {
      await onDelete(id);
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) {
    return <Loading message="Loading files..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={onRetry} />;
  }

  if (!files || files.length === 0) {
    return (
      <EmptyState
        icon={<FiFile className="w-12 h-12" />}
        title="No files uploaded"
        description="Upload your first file to get started with privacy scanning"
        action={
          <Link to="/upload" className="btn-primary text-sm">
            Upload File
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div className="relative flex-1 max-w-xs">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-9 text-sm"
          />
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onRetry} className="btn-ghost text-sm p-2" title="Refresh">
            <FiRefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Files Table */}
      <div className="overflow-x-auto bg-white rounded-xl border border-gray-200">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="table-header">File Name</th>
              <th className="table-header hidden sm:table-cell">Size</th>
              <th className="table-header hidden md:table-cell">Type</th>
              <th className="table-header">Status</th>
              <th className="table-header hidden md:table-cell">Uploaded</th>
              <th className="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filteredFiles.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-400">
                  No files match your search
                </td>
              </tr>
            ) : (
              filteredFiles.map((file) => (
                <tr key={file.id} className="hover:bg-gray-50 transition-colors">
                  <td className="table-cell">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                        <FiFile className="w-4 h-4 text-gray-500" />
                      </div>
                      <div className="min-w-0">
                        <Link
                          to={`/scans/${file.id}`}
                          className="text-sm font-medium text-gray-900 hover:text-cyber-600 truncate block max-w-[200px]"
                        >
                          {file.original_filename || file.filename}
                        </Link>
                        <span className="text-xs text-gray-400 sm:hidden">
                          {file.file_size ? `${(file.file_size / 1024).toFixed(1)} KB` : ''}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="table-cell hidden sm:table-cell text-gray-500">
                    {file.file_size ? `${(file.file_size / 1024).toFixed(1)} KB` : '-'}
                  </td>
                  <td className="table-cell hidden md:table-cell">
                    <span className="text-xs text-gray-500 uppercase">
                      {file.file_type || file.original_filename?.split('.').pop() || '-'}
                    </span>
                  </td>
                  <td className="table-cell">
                    <StatusBadge status={file.scan_status || file.status || 'pending'} type="scan" />
                  </td>
                  <td className="table-cell hidden md:table-cell text-gray-500 text-sm">
                    {file.created_at
                      ? new Date(file.created_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })
                      : '-'}
                  </td>
                  <td className="table-cell text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Link
                        to={`/scans/${file.id}`}
                        className="p-1.5 hover:bg-cyber-50 rounded-lg text-cyber-600 hover:text-cyber-700 transition-colors"
                        title="View scan results"
                      >
                        <FiSearch className="w-4 h-4" />
                      </Link>
                      <button
                        onClick={() => handleDelete(file.id)}
                        disabled={deletingId === file.id}
                        className="p-1.5 hover:bg-red-50 rounded-lg text-red-500 hover:text-red-600 transition-colors disabled:opacity-50"
                        title="Delete file"
                      >
                        {deletingId === file.id ? (
                          <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <FiTrash2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
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
