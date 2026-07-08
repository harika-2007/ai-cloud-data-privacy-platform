import { useState, useRef, useCallback } from 'react';
import { FiUpload, FiFile, FiX, FiCheck, FiAlertCircle } from 'react-icons/fi';
import { fileService } from '../../services/fileService';

const ACCEPTED_TYPES = '.csv,.xlsx,.xls,.pdf,.txt,.json';
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export default function FileUpload({ onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const inputRef = useRef(null);

  const validateFile = (file) => {
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext)) {
      setError(`Unsupported file type "${ext}". Accepted: ${ACCEPTED_TYPES}`);
      return false;
    }
    if (file.size > MAX_FILE_SIZE) {
      setError(`File too large. Maximum size is 50MB.`);
      return false;
    }
    if (file.size === 0) {
      setError('File is empty.');
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
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const files = e.dataTransfer?.files;
    if (files?.[0]) {
      handleFile(files[0]);
    }
  }, []);

  const handleChange = (e) => {
    const files = e.target.files;
    if (files?.[0]) {
      handleFile(files[0]);
    }
    if (inputRef.current) {
      inputRef.current.value = '';
    }
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
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
      setTimeout(() => {
        setSelectedFile(null);
        setUploadProgress(0);
        setUploadSuccess(false);
      }, 2000);
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Upload failed. Please try again.';
      setError(message);
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

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
          dragActive
            ? 'border-cyber-500 bg-cyber-50'
            : selectedFile
            ? 'border-cyber-300 bg-cyber-50/50'
            : 'border-gray-300 hover:border-gray-400 bg-white'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_TYPES}
          onChange={handleChange}
          className="hidden"
        />

        {!selectedFile ? (
          <div className="space-y-3">
            <div className="w-16 h-16 mx-auto bg-cyber-100 rounded-full flex items-center justify-center">
              <FiUpload className="w-7 h-7 text-cyber-600" />
            </div>
            <div>
              <p className="text-gray-700 font-medium">
                Drag and drop your file here, or{' '}
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  className="text-cyber-600 hover:text-cyber-700 underline"
                >
                  browse
                </button>
              </p>
              <p className="text-sm text-gray-400 mt-1">
                Supports CSV, Excel (.xlsx), PDF, TXT, JSON - Max 50MB
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-cyber-100 rounded-lg flex items-center justify-center">
                <FiFile className="w-5 h-5 text-cyber-600" />
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-gray-900 truncate max-w-xs">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-gray-400">{formatFileSize(selectedFile.size)}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={clearSelection}
              disabled={uploading}
              className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400 hover:text-gray-600 transition-colors"
            >
              <FiX className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <FiAlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
            <FiX className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Progress Bar */}
      {uploading && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-500">
            <span>Uploading...</span>
            <span>{uploadProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-cyber-600 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Success Message */}
      {uploadSuccess && (
        <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
          <FiCheck className="w-4 h-4 flex-shrink-0" />
          <span>File uploaded successfully! Starting scan...</span>
        </div>
      )}

      {/* Upload Button */}
      {selectedFile && !uploadSuccess && (
        <button
          type="button"
          onClick={handleUpload}
          disabled={uploading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {uploading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <FiUpload className="w-4 h-4" />
              Upload File
            </>
          )}
        </button>
      )}
    </div>
  );
}
