import { useState, useEffect } from 'react';
import { Cpu, AlertTriangle, CheckCircle, Info, Target, RefreshCw, Star, Shield } from 'lucide-react';
import Loading from '../Common/Loading';
import ErrorState from '../Common/ErrorState';
import EmptyState from '../Common/EmptyState';
import StatusBadge from '../Common/StatusBadge';
import { aiService } from '../../services/aiService';

/**
 * Map severity to tailwind-card classes and icons.
 */
const SEVERITY_STYLES = {
  critical: {
    bg: 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800',
    icon: AlertTriangle,
    iconColor: 'text-red-500',
    labelColor: 'text-red-600 dark:text-red-400',
  },
  high: {
    bg: 'bg-orange-50 dark:bg-orange-900/10 border-orange-200 dark:border-orange-800',
    icon: AlertTriangle,
    iconColor: 'text-orange-500',
    labelColor: 'text-orange-600 dark:text-orange-400',
  },
  medium: {
    bg: 'bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-800',
    icon: Info,
    iconColor: 'text-yellow-500',
    labelColor: 'text-yellow-600 dark:text-yellow-400',
  },
  low: {
    bg: 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800',
    icon: CheckCircle,
    iconColor: 'text-green-500',
    labelColor: 'text-green-600 dark:text-green-400',
  },
};

const PRIORITY_RANK = { critical: 0, high: 1, medium: 2, low: 3 };

export default function AIRecommendations({ fileId, initialData = null }) {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(!initialData);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [isFallback, setIsFallback] = useState(false);

  // ---- Fetch on mount ----
  useEffect(() => {
    if (!fileId) return;
    // Only auto-fetch when the tab is first selected
    if (!initialData) {
      setLoading(true);
      fetchWithTimeout();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileId]);

  const fetchWithTimeout = async () => {
    try {
      const result = await aiService.getRecommendations(fileId);
      setData(result);
      setIsFallback(false);
      setError(null);
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Failed to generate recommendations';
      // If the backend returned a meaningful fallback (check for risk_summary),
      // treat it as data rather than an error
      if (err.response?.data?.risk_summary) {
        setData(err.response.data);
        setIsFallback(true);
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
      setGenerating(false);
    }
  };

  const fetchRecommendations = async () => {
    if (!fileId) return;
    setLoading(true);
    setError(null);
    setIsFallback(false);
    await fetchWithTimeout();
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    setIsFallback(false);
    try {
      const result = await aiService.getRecommendations(fileId);
      setData(result);
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Failed to generate recommendations';
      if (err.response?.data?.risk_summary) {
        setData(err.response.data);
        setIsFallback(true);
      } else {
        setError(message);
      }
    } finally {
      setGenerating(false);
    }
  };

  // ---- Loading state ----
  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="w-5 h-5 text-cyber-500" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">AI Recommendations</h3>
        </div>
        <Loading message="AI is analyzing your data..." />
      </div>
    );
  }

  // ---- Error state (no fallback data) ----
  if (error) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="w-5 h-5 text-cyber-500" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">AI Recommendations</h3>
        </div>
        <ErrorState message={error} onRetry={fetchRecommendations} />
        <div className="mt-4 text-center">
          <button onClick={handleGenerate} disabled={generating} className="btn-primary text-sm">
            {generating ? 'Generating...' : 'Try Again'}
          </button>
        </div>
      </div>
    );
  }

  // ---- No data / initial empty state ----
  if (!data) {
    return (
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyber-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">AI Recommendations</h3>
          </div>
        </div>
        <EmptyState
          title="No recommendations yet"
          description="Generate AI-powered compliance recommendations for this file"
          action={
            <button onClick={handleGenerate} disabled={generating} className="btn-primary text-sm">
              {generating ? 'Generating...' : 'Generate Recommendations'}
            </button>
          }
        />
      </div>
    );
  }

  // ---- Success / fallback state ----
  const summary = data.risk_summary || data.analysis_summary || data.summary || '';
  const impact = data.compliance_impact || data.business_impact || data.risk_impact || '';
  const actions = data.recommended_actions || data.actions || data.recommendations || [];
  const detailed = data.detailed_recommendations || [];

  // Sort detailed recommendations by priority
  const sortedDetailed = [...(detailed || [])].sort(
    (a, b) => (PRIORITY_RANK[a.priority] ?? 99) - (PRIORITY_RANK[b.priority] ?? 99),
  );

  return (
    <div className="card space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-cyber-500" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            AI Recommendations
            {isFallback && (
              <span className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                <Shield className="w-3 h-3" />
                Built-in
              </span>
            )}
          </h3>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="btn-ghost text-sm flex items-center gap-1.5"
        >
          <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
          {generating ? 'Generating...' : 'Regenerate'}
        </button>
      </div>

      {/* Fallback notice */}
      {isFallback && (
        <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 flex items-start gap-3">
          <Info className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-blue-700 dark:text-blue-300">
            AI model (Ollama) is not available. Showing built-in compliance recommendations
            based on detected data types. Enable Ollama with Llama 3 for deeper AI-powered analysis.
          </p>
        </div>
      )}

      {/* Risk Summary */}
      {summary && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-500" />
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Risk Summary</h4>
          </div>
          <div className="p-4 bg-orange-50 dark:bg-orange-900/10 border border-orange-200 dark:border-orange-800 rounded-lg">
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{summary}</p>
          </div>
        </div>
      )}

      {/* Compliance Impact */}
      {impact && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-red-500" />
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Compliance Impact</h4>
          </div>
          <div className="p-4 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{impact}</p>
          </div>
        </div>
      )}

      {/* Recommended Actions (simple strings from AI) */}
      {actions.length > 0 && actions.every(a => typeof a === 'string') && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Star className="w-4 h-4 text-yellow-500" />
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Recommended Actions</h4>
          </div>
          <div className="space-y-2">
            {actions.map((action, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 rounded-lg border bg-orange-50 dark:bg-orange-900/10 border-orange-200 dark:border-orange-800"
              >
                <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-gray-700 dark:text-gray-300">{action}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detailed Recommendations (structured objects from fallback) */}
      {sortedDetailed.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-indigo-500" />
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Detailed Remediation Steps</h4>
          </div>
          <div className="space-y-2">
            {sortedDetailed.map((item, index) => {
              const priority = item.priority || 'medium';
              const style = SEVERITY_STYLES[priority] || SEVERITY_STYLES.medium;
              const Icon = style.icon;

              return (
                <div key={index} className={`flex items-start gap-3 p-3 rounded-lg border ${style.bg}`}>
                  <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${style.iconColor}`} />
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        {item.category || item.finding?.split(' ').slice(0, 2).join(' ') || 'General'}
                      </span>
                      <span className={`text-[10px] font-bold uppercase ${style.labelColor}`}>
                        {priority}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                      {item.recommendation || item.text || ''}
                    </p>
                    {item.severity && (
                      <div className="mt-1">
                        <StatusBadge status={item.severity} type="severity" size="xs" />
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* AI Disclaimer */}
      <div className="pt-3 border-t border-gray-100 dark:border-gray-700/50">
        <p className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1.5">
          <Info className="w-3 h-3" />
          {isFallback
            ? 'Built-in compliance recommendations based on detected data types. Enable Ollama LLM for AI-powered analysis.'
            : 'AI-generated recommendations based on detected sensitive data patterns. Review before implementation.'}
        </p>
      </div>
    </div>
  );
}
