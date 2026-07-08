import { motion } from 'framer-motion';
import { SEVERITY_CLASSES } from '../../utils/constants';

export default function StatusBadge({ status, type = 'default', dot = false }) {
  const normalizedStatus = (status || '').toLowerCase();

  const scanStatusMap = {
    pending: { class: 'badge bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600', dot: 'bg-gray-400' },
    in_progress: { class: 'badge-info', dot: 'bg-blue-500 animate-pulse-slow' },
    processing: { class: 'badge-info', dot: 'bg-blue-500 animate-pulse-slow' },
    completed: { class: 'badge-low', dot: 'bg-green-500' },
    failed: { class: 'badge-critical', dot: 'bg-red-500' },
  };

  if (type === 'severity' || type === 'risk') {
    const classes = SEVERITY_CLASSES[normalizedStatus] || SEVERITY_CLASSES.info;
    return (
      <motion.span
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`badge ${classes}`}
      >
        {dot && <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${classes.includes('red') ? 'bg-red-500' : classes.includes('orange') ? 'bg-orange-500' : classes.includes('yellow') ? 'bg-yellow-500' : classes.includes('green') ? 'bg-green-500' : 'bg-blue-500'}`} />}
        {status}
      </motion.span>
    );
  }

  if (type === 'scan') {
    const scan = scanStatusMap[normalizedStatus] || { class: 'badge bg-gray-100 text-gray-600', dot: 'bg-gray-400' };
    const displayLabel = normalizedStatus === 'in_progress' ? 'Processing' : status;
    return (
      <motion.span
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`badge ${scan.class}`}
      >
        <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${scan.dot}`} />
        {displayLabel}
      </motion.span>
    );
  }

  return (
    <span className="badge bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600">
      {status}
    </span>
  );
}
