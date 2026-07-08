import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, Send, Sparkles, Bot, User, AlertCircle, Loader2, RefreshCw, Shield,
} from 'lucide-react';
import { aiService } from '../../services/aiService';
import toast from 'react-hot-toast';

const INITIAL_SUGGESTIONS = [
  'What compliance regulations apply to my data?',
  'How can I reduce PII exposure risk?',
  'Explain GDPR requirements for data processing',
  'Best practices for data encryption',
  'What is a DPIA and when do I need one?',
  'How to handle a data breach notification?',
];

const WELCOME_MESSAGE = {
  role: 'assistant',
  content: `👋 **Welcome to SecureCloud AI Assistant!**

I'm your privacy compliance expert. I can help you with:

- 🔒 **Data protection regulations** (GDPR, CCPA, HIPAA, etc.)
- 🛡️ **Security best practices** and compliance requirements
- 📋 **PII detection** and risk assessment guidance
- ✅ **Remediation strategies** for your privacy findings

Ask me anything about privacy compliance or data security!`,
};

export default function AIAssistant({ open, onClose }) {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (open) {
      scrollToBottom();
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [open, messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;

    setInput('');
    setError(null);
    const userMessage = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMessage]);
    setSending(true);

    try {
      const history = messages
        .filter((m) => m.role !== 'system')
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }));

      const result = await aiService.chat(text, history);
      const reply = result?.response || result?.reply || 'No response received.';
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
    } catch (err) {
      const isOffline = !err.response || err.code === 'ERR_NETWORK' || err.message?.includes('Network Error');
      if (isOffline) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content:
              '**AI Assistant is temporarily unavailable.**\n\nI cannot connect to the AI service right now. This could mean:\n\n- The backend server is not running\n- The AI service (Ollama) is down\n- There is a network issue\n\nPlease try again in a moment.',
          },
        ]);
      } else {
        const errMsg = err.response?.data?.detail || err.message || 'Failed to get response';
        setError(errMsg);
        toast.error(errMsg);
      }
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestion = (text) => {
    setInput(text);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const handleRetry = () => {
    setError(null);
    handleSend();
  };

  const formatMessage = (content) => {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br />')
      .replace(/^- (.*?)$/gm, '• $1');
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            initial={{ opacity: 0, y: 40, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 40, scale: 0.96 }}
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            className="fixed z-50 bottom-4 right-4 sm:bottom-6 sm:right-6
              w-[calc(100vw-32px)] sm:w-[420px] h-[560px] sm:h-[600px]
              max-h-[calc(100vh-80px)]
              bg-white dark:bg-gray-900 rounded-2xl shadow-2xl shadow-black/20
              border border-gray-200 dark:border-gray-700
              flex flex-col overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-800 bg-gradient-to-r from-cyber-50 to-indigo-50 dark:from-cyber-900/20 dark:to-indigo-900/20">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyber-500 to-cyber-600 flex items-center justify-center shadow-lg shadow-cyber-500/20">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white">AI Assistant</h3>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400">Privacy Compliance Expert</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-white/50 dark:hover:bg-gray-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 scrollbar-thin">
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                  className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  {/* Avatar */}
                  <div
                    className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-br from-cyber-400 to-cyber-500'
                        : 'bg-gradient-to-br from-cyber-600 to-indigo-600'
                    }`}
                  >
                    {msg.role === 'user' ? (
                      <User className="w-4 h-4 text-white" />
                    ) : (
                      <Sparkles className="w-4 h-4 text-white" />
                    )}
                  </div>

                  {/* Bubble */}
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-cyber-500 text-white rounded-tr-md'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-tl-md border border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    {msg.role === 'assistant' ? (
                      <span
                        className="prose prose-sm dark:prose-invert max-w-none"
                        dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}
                      />
                    ) : (
                      <span>{msg.content}</span>
                    )}
                  </div>
                </motion.div>
              ))}

              {/* Typing indicator */}
              {sending && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-3"
                >
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyber-600 to-indigo-600 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-tl-md px-4 py-3 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 bg-cyber-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-cyber-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-cyber-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Suggestions (shown at start) */}
              {messages.length === 1 && !sending && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className="mt-2"
                >
                  <p className="text-xs text-gray-400 dark:text-gray-500 mb-2 font-medium">
                    Try asking about:
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {INITIAL_SUGGESTIONS.map((suggestion, i) => (
                      <button
                        key={i}
                        onClick={() => handleSuggestion(suggestion)}
                        className="px-3 py-1.5 text-xs font-medium rounded-full
                          bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400
                          hover:bg-cyber-50 dark:hover:bg-cyber-900/20
                          hover:text-cyber-600 dark:hover:text-cyber-400
                          border border-gray-200 dark:border-gray-700
                          hover:border-cyber-300 dark:hover:border-cyber-700
                          transition-all duration-200"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Error bar */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mx-5 px-4 py-2.5 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 flex items-center gap-2 text-sm text-red-700 dark:text-red-400"
                >
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span className="flex-1 truncate">{error}</span>
                  <button onClick={handleRetry} className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors flex-shrink-0">
                    <RefreshCw className="w-3.5 h-3.5" />
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Input */}
            <div className="px-5 py-4 border-t border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/50">
              <div className="flex items-end gap-2">
                <div className="flex-1 relative">
                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about compliance, regulations, or security..."
                    rows={1}
                    disabled={sending}
                    className="w-full px-4 py-2.5 pr-10 bg-white dark:bg-gray-800
                      border border-gray-200 dark:border-gray-700
                      rounded-xl text-sm text-gray-900 dark:text-gray-100
                      placeholder-gray-400 dark:placeholder-gray-500
                      focus:ring-2 focus:ring-cyber-500/30 focus:border-cyber-500
                      focus:outline-none resize-none transition-all
                      disabled:opacity-50"
                    style={{ minHeight: '42px', maxHeight: '120px' }}
                    onInput={(e) => {
                      e.target.style.height = 'auto';
                      e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
                    }}
                  />
                </div>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleSend}
                  disabled={!input.trim() || sending}
                  className="p-2.5 rounded-xl bg-gradient-to-br from-cyber-500 to-cyber-600
                    text-white shadow-lg shadow-cyber-500/20
                    hover:from-cyber-400 hover:to-cyber-500
                    disabled:opacity-40 disabled:cursor-not-allowed
                    transition-all duration-200 flex-shrink-0"
                >
                  {sending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </motion.button>
              </div>
              <p className="text-[10px] text-gray-400 dark:text-gray-600 mt-1.5 text-center">
                AI responses are generated by Llama 3 and may not be accurate. Verify critical info.
              </p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
