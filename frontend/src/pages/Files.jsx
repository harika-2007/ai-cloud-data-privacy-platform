import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, Upload, RefreshCw, Search, Trash2, ChevronLeft, ChevronRight,
  Loader2, FileSpreadsheet, FileCode, Shield, AlertTriangle, Clock, Download,
} from 'lucide-react';
import { fileService } from '../services/fileService';
import { scanService } from '../services/scanService';
import StatusBadge from '../components/Common/StatusBadge';
import Loading from '../components/Common/Loading';
import ErrorState from '../components/Common/ErrorState';
import EmptyState from '../components/Common/EmptyState';
import toast from 'react-hot-toast';

function getFileIcon(filename) {
  const ext = filename?.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'csv':
    case 'xlsx':
    case 'xls': return FileSpreadsheet;
    case 'json':
    case 'txt': return FileCode;
    default: return FileText;
  }
}

export default function Files() {
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [deletingId, setDeletingId] = useState(null);
  const [scanningId, setScanningId] = useState(null);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fileService.getFiles({ page, page_size: 20 });
      const fileList = result?.files || [];
      setFiles(Array.isArray(fileList) ? fileList : []);
      const total = result?.total || fileList.length;
      setTotalPages(Math.ceil(total / 20) || 1);
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to load files');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { fetchFiles(); }, [fetchFiles]);

  const handleDelete = async (id) => {
    setDeletingId(id);
    try {
      await fileService.deleteFile(id);
      toast.success('File deleted');
      fetchFiles();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete');
    } finally {
      setDeletingId(null);
    }
  };

  const handleScan = async (fileId) => {
    setScanningId(fileId);
    try {
      await scanService.startScan(fileId);
      toast.success('Scan started');
      setTimeout(fetchFiles, 2000);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start scan');
    } finally {
      setScanningId(null);
    }
  };

  const filteredFiles = files.filter((f) =>
    f.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    f.original_filename?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading && files.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Files</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">Manage uploaded files</p>
          </div>
        </div>
        <Loading message="Loading files..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Files</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">Manage uploaded files</p>
          </div>
        </div>
        <ErrorState message={error} onRetry={fetchFiles} />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-3">
            <FileText className="w-6 h-6 text-cyber-500" />
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Files</h1>
          </div>
          <p className="text-gray-500 dark:text-gray-400 mt-1 ml-9">
            {files.length > 0 ? `${files.length} file${files.length !== 1 ? 's' : ''} uploaded` : 'Manage uploaded files'}
          </p>
        </div>
        <button onClick={() => navigate('/upload')} className="btn-primary">
          <Upload className="w-4 h-4" /> Upload File
        </button>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-10"
          />
        </div>
        <button onClick={fetchFiles} className="btn-ghost" title="Refresh">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Files Table */}
      {filteredFiles.length === 0 ? (
        files.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No files uploaded"
            description="Upload your first file to get started with privacy scanning"
            action={
              <Link to="/upload" className="btn-primary">Upload File</Link>
            }
          />
        ) : (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <Search className="w-10 h-10 mb-3" />
            <p className="text-sm">No files match your search</p>
          </div>
        )
      ) : (
        <div className="table-container">
          <table className="w-full">
            <thead>
              <tr>
                <th className="table-header">File Name</th>
                <th className="table-header hidden sm:table-cell">Size</th>
                <th className="table-header hidden md:table-cell">Type</th>
                <th className="table-header">Status</th>
                <th className="table-header hidden lg:table-cell">Uploaded</th>
                <th className="table-header text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
              {filteredFiles.map((file, idx) => {
                const Icon = getFileIcon(file.original_filename || file.filename);
                return (
                  <motion.tr
                    key={file.id}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.03 }}
                    className="table-row"
                  >
                    <td className="table-cell">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-gray-100 to-gray-50 dark:from-gray-700 dark:to-gray-600 flex items-center justify-center flex-shrink-0">
                          <Icon className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                        </div>
                        <div className="min-w-0">
                          <Link
                            to={`/scans/${file.id}`}
                            className="text-sm font-medium text-gray-900 dark:text-white hover:text-cyber-600 dark:hover:text-cyber-400 truncate block max-w-[200px]"
                          >
                            {file.original_filename || file.filename}
                          </Link>
                        </div>
                      </div>
                    </td>
                    <td className="table-cell hidden sm:table-cell text-gray-500 dark:text-gray-400">
                      {file.file_size ? `${(file.file_size / 1024).toFixed(1)} KB` : '-'}
                    </td>
                    <td className="table-cell hidden md:table-cell">
                      <span className="text-xs font-mono text-gray-500 dark:text-gray-400 uppercase px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">
                        {file.file_type || file.original_filename?.split('.').pop() || '-'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <StatusBadge status={file.scan_status || file.status || 'pending'} type="scan" dot />
                    </td>
                    <td className="table-cell hidden lg:table-cell">
                      <span className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {file.created_at
                          ? new Date(file.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                          : '-'}
                      </span>
                    </td>
                    <td className="table-cell text-right">
                      <div className="flex items-center justify-end gap-1">
                        {(file.scan_status === 'pending' || !file.scan_status) && (
                          <button
                            onClick={() => handleScan(file.id)}
                            disabled={scanningId === file.id}
                            className="btn-icon text-cyber-600 dark:text-cyber-400 hover:bg-cyber-50 dark:hover:bg-cyber-900/20"
                            title="Start scan"
                          >
                            {scanningId === file.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Shield className="w-4 h-4" />
                            )}
                          </button>
                        )}
                        <Link
                          to={`/scans/${file.id}`}
                          className="btn-icon text-gray-500 hover:text-cyber-600 hover:bg-cyber-50 dark:hover:bg-cyber-900/20"
                          title="View results"
                        >
                          <Search className="w-4 h-4" />
                        </Link>
                        <button
                          onClick={() => handleDelete(file.id)}
                          disabled={deletingId === file.id}
                          className="btn-icon text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                          title="Delete"
                        >
                          {deletingId === file.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
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
