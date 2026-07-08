import { TrendingUp, TrendingDown } from 'lucide-react';

export default function StatsCard({ icon: Icon, label, value, color = 'cyber', trend, format = 'number' }) {
  const colorMap = {
    cyber: 'bg-cyber-100 dark:bg-cyber-900/30 text-cyber-600 dark:text-cyber-400',
    green: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400',
    orange: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400',
    red: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
    purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
  };

  const formatValue = (val) => {
    if (format === 'percentage') return `${Math.round(val)}%`;
    if (format === 'currency') return `$${val?.toLocaleString()}`;
    return val?.toLocaleString() ?? '0';
  };

  return (
    <div className="card flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl ${colorMap[color] || colorMap.cyber} flex items-center justify-center flex-shrink-0`}>
        {Icon && <Icon className="w-6 h-6" />}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{label}</p>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">{formatValue(value)}</p>
        {trend !== undefined && (
          <p className={`inline-flex items-center gap-1 text-xs ${trend >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
            {trend >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {Math.abs(trend)}%
          </p>
        )}
      </div>
    </div>
  );
}
