import { useState } from 'react';
import { API_BASE_URL } from "../utils/constants";
import { Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  Shield,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Cloud,
  Globe,
  Users,
} from 'lucide-react';

function ParticleField() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {Array.from({ length: 20 }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-cyber-400/30 rounded-full"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [0, -30, 0],
            opacity: [0, 1, 0],
            scale: [0, 1, 0],
          }}
          transition={{
            duration: 3 + Math.random() * 4,
            repeat: Infinity,
            delay: Math.random() * 3,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  );
}

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showEmailLogin, setShowEmailLogin] = useState(false);
  const [errors, setErrors] = useState({});

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const handleGoogleSignIn = () => {
    // Use relative URL so it works in all environments:
    // - Vite dev: proxied by vite.config.js to backend
    // - Docker/nginx: proxied by nginx to backend
    // - ngrok: proxied by nginx to backend
    // - Production: proxied by reverse proxy to backend
    import { API_BASE_URL } from "../utils/constants";

// ...

window.location.assign(`${API_BASE_URL}/auth/google/login`);

  const validate = () => {
    const errs = {};
    if (!form.email.trim()) errs.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = 'Invalid email format';
    if (!form.password) errs.password = 'Password is required';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      await login(form.email, form.password);
    } catch {
      // handled in AuthContext
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left - Hero/Illustration Side */}
      <div className="hidden lg:flex lg:w-1/2 relative auth-bg overflow-hidden flex-col justify-between p-12">
        <ParticleField />

        {/* Top logo area */}
        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyber-500 to-cyber-600 flex items-center justify-center shadow-lg shadow-cyber-500/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold text-white">SecureCloud</span>
              <span className="text-lg font-bold text-cyber-400"> AI</span>
            </div>
          </div>
        </div>

        {/* Center content */}
        <div className="relative z-10 max-w-lg">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl bg-gradient-to-br from-cyber-500/20 to-cyber-600/10 border border-cyber-500/20 backdrop-blur-sm flex items-center justify-center">
              <Shield className="w-12 h-12 sm:w-14 sm:h-14 text-cyber-400" />
            </div>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-4xl lg:text-5xl font-bold text-white leading-tight mt-6"
          >
            AI-Powered Cloud{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyber-400 to-indigo-300">
              Privacy Security
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="text-gray-400 text-lg mt-4 leading-relaxed"
          >
            Enterprise-grade data privacy compliance and security monitoring platform.
            Detect, analyze, and protect sensitive data across your cloud infrastructure.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.8 }}
            className="flex flex-wrap gap-6 mt-8"
          >
            {[
              { icon: Cloud, label: 'Cloud Native' },
              { icon: Globe, label: 'Global Compliance' },
              { icon: Users, label: 'Enterprise Ready' },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-gray-400">
                <item.icon className="w-4 h-4 text-cyber-400" />
                <span className="text-sm">{item.label}</span>
              </div>
            ))}
          </motion.div>
        </div>

        {/* Bottom trust bar */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="relative z-10 flex items-center gap-6"
        >
          {[
            { text: 'SOC 2 Type II Certified' },
            { text: 'GDPR Compliant' },
            { text: 'HIPAA Eligible' },
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-1.5 text-gray-500">
              <Shield className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-xs">{item.text}</span>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Right - Login Side */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-10 bg-white dark:bg-gray-900">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="w-full max-w-sm"
        >
          {/* Mobile logo */}
          <div className="lg:hidden flex flex-col items-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyber-500 to-cyber-600 flex items-center justify-center shadow-lg shadow-cyber-500/20 mb-3">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              SecureCloud <span className="text-cyber-500">AI</span>
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Enterprise Privacy Platform</p>
          </div>

          {/* Google Sign-In Button */}
          <button
            type="button"
            onClick={handleGoogleSignIn}
            className="w-full relative flex items-center justify-center gap-3 px-6 py-3.5 border-2 border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 transition-all duration-200 shadow-sm hover:shadow-md hover:bg-gray-50 dark:hover:bg-gray-750 active:scale-[0.98]"
          >
            <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            <span className="text-sm font-semibold text-gray-700 dark:text-gray-200">
              Continue with Google
            </span>
          </button>

          {/* OR Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200 dark:border-gray-700" />
            </div>
            <div className="relative flex justify-center">
              <span className="px-3 text-xs text-gray-400 bg-white dark:bg-gray-900">OR</span>
            </div>
          </div>

          {/* Microsoft Sign-In */}
          <button
            disabled
            className="w-full flex items-center justify-center gap-3 px-6 py-3.5 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 opacity-60 cursor-not-allowed transition-all duration-200"
          >
            <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 23 23">
              <rect x="1" y="1" width="10" height="10" fill="#f25022" />
              <rect x="12" y="1" width="10" height="10" fill="#7fba00" />
              <rect x="1" y="12" width="10" height="10" fill="#00a4ef" />
              <rect x="12" y="12" width="10" height="10" fill="#ffb900" />
            </svg>
            <span className="text-sm font-semibold text-gray-500 dark:text-gray-400">
              Continue with Microsoft
            </span>
          </button>

          {/* Use email instead */}
          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => setShowEmailLogin(!showEmailLogin)}
              className="inline-flex items-center gap-1 text-sm text-cyber-600 dark:text-cyber-400 hover:underline font-medium"
            >
              {showEmailLogin ? (
                <>Collapse email login <ChevronUp className="w-3.5 h-3.5" /></>
              ) : (
                <>Use email instead <ChevronDown className="w-3.5 h-3.5" /></>
              )}
            </button>
          </div>

          {/* Collapsible Email Login */}
          <motion.div
            initial={false}
            animate={{
              height: showEmailLogin ? 'auto' : 0,
              opacity: showEmailLogin ? 1 : 0,
            }}
            className="overflow-hidden"
          >
            <form onSubmit={handleSubmit} className="space-y-4 pt-4">
              {/* Email */}
              <div>
                <label htmlFor="email" className="label">Email Address</label>
                <div className="input-group">
                  <Mail className="input-icon" />
                  <input
                    id="email"
                    type="email"
                    className={`input-with-icon ${errors.email ? 'input-error' : ''}`}
                    placeholder="you@company.com"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    disabled={loading}
                    autoComplete="email"
                  />
                </div>
                {errors.email && (
                  <motion.p
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-red-500 text-xs mt-1.5"
                  >
                    {errors.email}
                  </motion.p>
                )}
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="label">Password</label>
                <div className="input-group">
                  <Lock className="input-icon" />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    className={`input-with-icon pr-10 ${errors.password ? 'input-error' : ''}`}
                    placeholder="Enter your password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    disabled={loading}
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && (
                  <motion.p
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-red-500 text-xs mt-1.5"
                  >
                    {errors.password}
                  </motion.p>
                )}
              </div>

              {/* Submit */}
              <motion.button
                type="submit"
                disabled={loading}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                className="btn-primary w-full py-3"
              >
                {loading ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Signing in...
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    Sign In
                    <ArrowRight className="w-4 h-4" />
                  </div>
                )}
              </motion.button>
            </form>
          </motion.div>

          {/* Footer */}
          <p className="text-xs text-center text-gray-400 dark:text-gray-500 mt-8">
            Protected by enterprise-grade encryption and security controls
          </p>
        </motion.div>
      </div>
    </div>
  );
}
