import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload as UploadIcon,
  FileText,
  FileSpreadsheet,
  FileCode,
  X,
  Check,
  AlertCircle,
  Shield,
  Lock,
  RefreshCw,
  ChevronRight,
  Cloud,
  Search,
  BarChart3,
} from 'lucide-react';
import { fileService } from '../services/fileService';
import toast from 'react-hot-toast';

const ACCEPTED_TYPES = '.csv,.xlsx,.xls,.pdf,.txt,.json';
const MAX_FILE_SIZE = 50 * 1024 * 1024;

const STEPS = [
  { icon: FileText, label: 'Select File', desc: 'Choose CSV, Excel, PDF, or TXT' },
  { icon: Shield, label: 'Auto-Scan', desc: 'AI scans for PII data' },
  { icon: BarChart3, label: 'Review Results', desc: 'View findings & recommendations' },
];

function getFileIcon(filename) {
  const ext = filename?.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'csv': return FileSpreadsheet;
    case 'xlsx':
    case 'xls': return FileSpreadsheet;
    case 'pdf': return FileText;
    case 'json':
    case 'txt': return FileCode;
    default: return FileText;
  }
}

function getFileColor(filename) {
  const ext = filename?.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'csv': return 'from-emerald-500 to-emerald-400';
    case 'xlsx':
    case 'xls': return 'from-green-500 to-green-400';
    case 'pdf': return 'from-red-500 to-red-400';
    case 'json': return 'from-yellow-500 to-yellow-400';
    case 'txt': return 'from-blue-500 to-blue-400';
    default: return 'from-gray-500 to-gray-400';
  }
}

export default function Upload() {
  const navigate = useNavigate();
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const inputRef = useRef(null);

  const validateFile = (file) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext)) {
      setError(`Unsupported file type "${ext}". Accepted: CSV, Excel, PDF, TXT, JSON`);
      return false;
    }
    if (file.size > MAX_FILE_SIZE) {
      setError('File too large. Maximum size is 50MB');
      return false;
    }
    if (file.size === 0) {
      setError('File is empty');
      return false;
    }
    return true;
  };

  const handleFile = (file) => {
    setError(null);
    setUploadSuccess(false);
    if (validateFile(file)) {
      setSelectedFile(file);
    }
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const files = e.dataTransfer?.files;
    if (files?.[0]) handleFile(files[0]);
  }, []);

  const handleChange = (e) => {
    const files = e.target.files;
    if (files?.[0]) handleFile(files[0]);
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleUpload = async () => {
    if (!selectedFile || uploading) return;
    setUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const result = await fileService.uploadFile(selectedFile, (progress) => {
        setUploadProgress(progress);
      });
      setUploadSuccess(true);
      toast.success('File uploaded successfully!');
      const fileId = result?.id || result?.file_id;
      if (fileId) {
        setTimeout(() => navigate(`/scans/${fileId}`), 1500);
      }
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Upload failed';
      setError(message);
      toast.error(message);
    } finally {
      setUploading(false);
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setError(null);
    setUploadProgress(0);
    setUploadSuccess(false);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const FileIcon = selectedFile ? getFileIcon(selectedFile.name) : UploadIcon;
  const fileColor = selectedFile ? getFileColor(selectedFile.name) : 'from-cyber-500 to-cyber-600';

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <UploadIcon className="w-6 h-6 text-cyber-500" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Upload Files</h1>
        </div>
        <p className="text-gray-500 dark:text-gray-400 mt-1 ml-9">
          Upload files to scan for sensitive data and privacy compliance
        </p>
      </div>

      {/* Steps */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {STEPS.map((step, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-start gap-3 p-4 rounded-xl bg-white dark:bg-surface-card-dark border border-gray-100 dark:border-gray-700/50"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyber-100 to-cyber-50 dark:from-cyber-900/30 dark:to-cyber-800/20 flex items-center justify-center flex-shrink-0">
              <step.icon className="w-5 h-5 text-cyber-600 dark:text-cyber-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                <span className="text-cyber-500 mr-1">{i + 1}.</span>
                {step.label}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{step.desc}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Upload Zone */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card"
      >
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
          <UploadIcon className="w-5 h-5 text-cyber-500" />
          Upload File
        </h3>

        <div
          className={`relative border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-300 cursor-pointer ${
            dragActive
              ? 'border-cyber-500 bg-cyber-50/50 dark:bg-cyber-900/10 scale-[1.01]'
              : selectedFile
              ? 'border-cyber-300 dark:border-cyber-700 bg-cyber-50/30 dark:bg-cyber-900/5'
              : 'border-gray-300 dark:border-gray-600 hover:border-cyber-400 dark:hover:border-cyber-500 bg-gray-50/50 dark:bg-gray-800/20'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => !selectedFile && inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_TYPES}
            onChange={handleChange}
            className="hidden"
          />

          {!selectedFile ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-cyber-100 to-cyber-50 dark:from-cyber-900/30 dark:to-cyber-800/20 flex items-center justify-center">
                <UploadIcon className="w-8 h-8 text-cyber-500" />
              </div>
              <div>
                <p className="text-gray-700 dark:text-gray-300 font-medium text-lg">
                  Drag & drop your file here
                </p>
                <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                  or <span className="text-cyber-600 dark:text-cyber-400 font-semibold hover:underline">browse files</span>
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2 text-xs text-gray-400 dark:text-gray-500">
                <span className="px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-800">CSV</span>
                <span className="px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-800">Excel</span>
                <span className="px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-800">PDF</span>
                <span className="px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-800">TXT</span>
                <span className="px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-800">JSON</span>
              </div>
              <p className="text-xs text-gray-400 flex items-center justify-center gap-1">
                <Lock className="w-3 h-3" /> Max 50MB - Securely encrypted
              </p>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center justify-between p-5 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 max-w-lg mx-auto"
            >
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${fileColor} flex items-center justify-center`}>
                  <FileIcon className="w-6 h-6 text-white" />
                </div>
                <div className="text-left">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white truncate max-w-[200px]">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                    {formatFileSize(selectedFile.size)}
                  </p>
                </div>
              </div>
              {!uploading && !uploadSuccess && (
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); clearSelection(); }}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </motion.div>
          )}
        </div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-center gap-2 p-4 mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-700 dark:text-red-400"
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span className="flex-1">{error}</span>
              <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Progress */}
        {uploading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 space-y-2"
          >
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <Cloud className="w-4 h-4 text-cyber-500 animate-bounce" />
              <span>Encrypting & uploading...</span>
              <span className="ml-auto font-semibold text-cyber-600 dark:text-cyber-400">{uploadProgress}%</span>
            </div>
            <div className="progress-bar">
              <motion.div
                className="progress-fill-primary"
                initial={{ width: 0 }}
                animate={{ width: `${uploadProgress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </motion.div>
        )}

        {/* Success */}
        <AnimatePresence>
          {uploadSuccess && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-3 p-4 mt-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl"
            >
              <div className="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-emerald-800 dark:text-emerald-400">
                  File uploaded successfully!
                </p>
                <p className="text-xs text-emerald-600 dark:text-emerald-500">
                  Starting security scan...
                </p>
              </div>
              <RefreshCw className="w-4 h-4 text-emerald-500 animate-spin" />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Upload Button */}
        {selectedFile && !uploading && !uploadSuccess && (
          <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            type="button"
            onClick={handleUpload}
            className="btn-primary w-full mt-4 py-3"
          >
            <UploadIcon className="w-4 h-4" />
            Upload & Scan File
          </motion.button>
        )}
      </motion.div>

      {/* Quick Link */}
      <div className="text-center">
        <button
          onClick={() => navigate('/files')}
          className="text-sm text-cyber-600 dark:text-cyber-400 hover:text-cyber-700 font-medium inline-flex items-center gap-1"
        >
          View all uploaded files <ChevronRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}
