import { motion } from 'framer-motion';
import { Shield, Loader2 } from 'lucide-react';

export default function Loading({ fullScreen = false, message = 'Loading...' }) {
  const content = (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center gap-4"
    >
      <div className="relative">
        <div className="absolute inset-0 rounded-full bg-cyber-500/20 animate-ping" />
        <div className="relative w-14 h-14 rounded-full bg-gradient-to-br from-cyber-500 to-cyber-600 flex items-center justify-center shadow-lg shadow-cyber-500/25">
          <Shield className="w-6 h-6 text-white" />
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Loader2 className="w-4 h-4 text-cyber-500 animate-spin" />
        <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">{message}</p>
      </div>
    </motion.div>
  );

  if (fullScreen) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface dark:bg-surface-dark">
        {content}
      </div>
    );
  }

  return <div className="py-16 flex justify-center">{content}</div>;
}
