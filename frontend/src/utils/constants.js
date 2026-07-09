/**
 * Application constants and configuration.
 *
 * VITE_API_URL is set at build time via environment variables:
 * - Default: '' (relative path — works when nginx/Vite proxy routes /api to backend)
 * - Development: http://localhost:8000 (Vite proxy in vite.config.js)
 * - Docker: http://backend:8000 (nginx proxy in frontend/nginx.conf)
 * - Production: https://your-api.com (set in deployment env vars)
 *
 * All API service modules use relative paths (e.g., api.post('/auth/login'))
 * which are resolved against the configured VITE_API_URL at runtime.
 */

// API base URL — defaults to empty string (relative) for nginx proxy setups.
// Set VITE_API_URL=http://localhost:8000/api/v1 for local dev without Docker.
// Set VITE_API_URL=https://your-api.com/api/v1 for production.
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const APP_NAME = 'SecureCloud AI';
export const APP_TAGLINE = 'Enterprise Privacy Security Platform';

export const TOKEN_KEYS = {
  ACCESS: 'access_token',
  REFRESH: 'refresh_token',
};

export const SEVERITY_COLORS = {
  critical: { bg: 'bg-red-500', text: 'text-red-600', hex: '#dc2626', light: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200 dark:border-red-800' },
  high: { bg: 'bg-orange-500', text: 'text-orange-600', hex: '#ea580c', light: 'bg-orange-50 dark:bg-orange-900/20', border: 'border-orange-200 dark:border-orange-800' },
  medium: { bg: 'bg-yellow-500', text: 'text-yellow-600', hex: '#ca8a04', light: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-200 dark:border-yellow-800' },
  low: { bg: 'bg-green-500', text: 'text-green-600', hex: '#16a34a', light: 'bg-green-50 dark:bg-green-900/20', border: 'border-green-200 dark:border-green-800' },
  info: { bg: 'bg-blue-500', text: 'text-blue-600', hex: '#2563eb', light: 'bg-blue-50 dark:bg-blue-900/20', border: 'border-blue-200 dark:border-blue-800' },
};

export const SEVERITY_CLASSES = {
  critical: 'badge-critical',
  high: 'badge-high',
  medium: 'badge-medium',
  low: 'badge-low',
  info: 'badge-info',
};

export const RISK_LEVELS = {
  critical: { label: 'Critical', color: 'text-red-600', bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200' },
  high: { label: 'High', color: 'text-orange-600', bg: 'bg-orange-50 dark:bg-orange-900/20', border: 'border-orange-200' },
  medium: { label: 'Medium', color: 'text-yellow-600', bg: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-200' },
  low: { label: 'Low', color: 'text-green-600', bg: 'bg-green-50 dark:bg-green-900/20', border: 'border-green-200' },
  safe: { label: 'Safe', color: 'text-emerald-600', bg: 'bg-emerald-50 dark:bg-emerald-900/20', border: 'border-emerald-200' },
};

export const SCAN_STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  FAILED: 'failed',
};

export const FILE_TYPES = [
  { value: '.csv', label: 'CSV', accept: '.csv', icon: 'fileSpreadsheet', color: 'text-green-500' },
  { value: '.xlsx', label: 'Excel', accept: '.xlsx,.xls', icon: 'fileSpreadsheet', color: 'text-emerald-500' },
  { value: '.pdf', label: 'PDF', accept: '.pdf', icon: 'fileText', color: 'text-red-500' },
  { value: '.txt', label: 'Text', accept: '.txt', icon: 'fileText', color: 'text-blue-500' },
  { value: '.json', label: 'JSON', accept: '.json', icon: 'fileCode', color: 'text-yellow-500' },
];

export const DATA_TYPES = {
  aadhaar: { label: 'Aadhaar Number', icon: 'fingerprint', category: 'Government ID' },
  pan: { label: 'PAN Number', icon: 'creditCard', category: 'Government ID' },
  email: { label: 'Email Address', icon: 'mail', category: 'Contact' },
  phone: { label: 'Phone Number', icon: 'phone', category: 'Contact' },
  credit_card: { label: 'Credit Card', icon: 'creditCard', category: 'Financial' },
  ssn: { label: 'SSN', icon: 'fingerprint', category: 'Government ID' },
  passport: { label: 'Passport Number', icon: 'bookOpen', category: 'Government ID' },
  dob: { label: 'Date of Birth', icon: 'calendar', category: 'Personal' },
  address: { label: 'Address', icon: 'mapPin', category: 'Personal' },
  ip_address: { label: 'IP Address', icon: 'globe', category: 'Technical' },
  bank_account: { label: 'Bank Account', icon: 'landmark', category: 'Financial' },
};

export const COMPLIANCE_THRESHOLDS = {
  GOOD: 80,
  WARNING: 50,
};

export const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low', 'info'];

export const SIDEBAR_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: 'LayoutDashboard' },
  { path: '/upload', label: 'Upload', icon: 'Upload' },
  { path: '/files', label: 'Files', icon: 'FileText' },
  { path: '/alerts', label: 'Alerts', icon: 'Bell' },
  { path: '/reports', label: 'Reports', icon: 'BarChart3' },
  { path: '/settings', label: 'Settings', icon: 'Settings' },
];

export const QUICK_ACTIONS = [
  { label: 'Upload File', path: '/upload', icon: 'Upload' },
  { label: 'View Alerts', path: '/alerts', icon: 'Bell' },
  { label: 'Generate Report', path: '/reports', icon: 'BarChart3' },
  { label: 'Scan Results', path: '/files', icon: 'Search' },
];

export const AI_SUGGESTIONS = [
  'How do I fix GDPR violations?',
  'What sensitive data is exposed?',
  'Generate ISO 27001 compliance report',
  'Show me security recommendations',
  'Explain my risk assessment',
  'How to encrypt PII data?',
  'Create compliance action plan',
  'Audit my cloud data privacy',
];
