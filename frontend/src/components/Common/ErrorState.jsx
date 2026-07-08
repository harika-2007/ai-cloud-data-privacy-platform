import { motion } from 'framer-motion';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function ErrorState({ message = 'Something went wrong', onRetry, title }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center py-16 gap-5"
    >
      <div className="relative">
        <div className="absolute inset-0 rounded-full bg-red-500/10 animate-ping" />
        <div className="relative w-16 h-16 bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/20 rounded-full flex items-center justify-center">
          <AlertTriangle className="w-7 h-7 text-red-500" />
        </div>
      </div>
      <div className="text-center max-w-sm">
        {title && <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">{title}</h3>}
        <p className="text-gray-500 dark:text-gray-400 text-sm">{message}</p>
      </div>
      {onRetry && (
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onRetry}
          className="btn-primary text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </motion.button>
      )}
    </motion.div>
  );
}
