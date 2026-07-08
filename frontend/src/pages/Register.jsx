import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';
import {
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Shield,
  ArrowRight,
  ArrowLeft,
  Building2,
  Briefcase,
  Cloud,
  Check,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

function PasswordStrength({ password }) {
  const checks = [
    { label: '8+ characters', test: password.length >= 8 },
    { label: 'Uppercase', test: /[A-Z]/.test(password) },
    { label: 'Lowercase', test: /[a-z]/.test(password) },
    { label: 'Number', test: /\d/.test(password) },
    { label: 'Special char', test: /[!@#$%^&*(),.?":{}|<>]/.test(password) },
  ];
  const score = checks.filter((c) => c.test).length;
  const width = (score / 5) * 100;

  const getColor = () => {
    if (width <= 40) return 'bg-red-500';
    if (width <= 60) return 'bg-yellow-500';
    if (width <= 80) return 'bg-cyber-500';
    return 'bg-emerald-500';
  };

  return (
    <div className="space-y-2 mt-2">
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
              i <= score ? getColor() : 'bg-gray-200 dark:bg-gray-700'
            }`}
          />
        ))}
      </div>
      <div className="grid grid-cols-2 gap-1">
        {checks.map((check, i) => (
          <div
            key={i}
            className={`flex items-center gap-1.5 text-xs transition-colors duration-300 ${
              check.test ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-400 dark:text-gray-500'
            }`}
          >
            <Check className={`w-3 h-3 ${check.test ? 'text-emerald-500' : 'text-gray-300 dark:text-gray-600'}`} />
            {check.label}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Register() {
  const { register, isAuthenticated } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    company: '',
    department: '',
    role: '',
    cloudProvider: '',
    projectName: '',
  });

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: '' }));
  };

  const validateStep = () => {
    const errs = {};
    if (step === 1) {
      if (!form.name.trim()) errs.name = 'Required';
      else if (form.name.trim().length < 2) errs.name = 'Min 2 characters';
      if (!form.email.trim()) errs.email = 'Required';
      else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = 'Invalid email';
    }
    if (step === 2) {
      if (!form.password) errs.password = 'Required';
      else if (form.password.length < 8) errs.password = 'Min 8 characters';
      else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(form.password)) errs.password = 'Needs uppercase, lowercase, number';
      if (form.password !== form.confirmPassword) errs.confirmPassword = 'Passwords do not match';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const nextStep = () => {
    if (validateStep()) setStep((s) => s + 1);
  };

  const prevStep = () => setStep((s) => s - 1);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (step === 1 || step === 2) {
      nextStep();
      return;
    }
    setLoading(true);
    try {
      await register(form.name.trim(), form.email.trim(), form.password);
    } catch {
      // handled in AuthContext
    } finally {
      setLoading(false);
    }
  };

  const roles = [
    { value: 'security_analyst', label: 'Security Analyst' },
    { value: 'compliance_officer', label: 'Compliance Officer' },
    { value: 'developer', label: 'Developer' },
    { value: 'manager', label: 'Manager' },
    { value: 'admin', label: 'Admin' },
  ];

  const cloudProviders = [
    { value: 'aws', label: 'AWS' },
    { value: 'gcp', label: 'Google Cloud' },
    { value: 'azure', label: 'Azure' },
    { value: 'multi', label: 'Multi-Cloud' },
    { value: 'on_prem', label: 'On-Premises' },
    { value: 'none', label: 'Not Sure' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-950 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-cyber-500 to-cyber-600 shadow-lg shadow-cyber-500/20 mb-4">
            <Shield className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Create Account</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Set up your security workspace</p>
        </div>

        {/* Steps indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300 ${
                  step >= s
                    ? 'bg-cyber-500 text-white shadow-sm shadow-cyber-500/30'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500'
                }`}
              >
                {step > s ? <Check className="w-4 h-4" /> : s}
              </div>
              {s < 3 && (
                <div className={`w-12 h-0.5 mx-1 transition-colors duration-300 ${
                  step > s ? 'bg-cyber-500' : 'bg-gray-200 dark:bg-gray-700'
                }`} />
              )}
            </div>
          ))}
        </div>

        {/* Form Card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-8">
          <form onSubmit={handleSubmit}>
            <AnimatePresence mode="wait">
              {/* Step 1: Basic Info */}
              {step === 1 && (
                <motion.div
                  key="step1"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-5"
                >
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Account Details</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Enter your basic information</p>
                  </div>

                  <div>
                    <label className="label">Full Name</label>
                    <div className="input-group">
                      <User className="input-icon" />
                      <input
                        type="text"
                        className={`input-with-icon ${errors.name ? 'input-error' : ''}`}
                        placeholder="John Doe"
                        value={form.name}
                        onChange={(e) => updateField('name', e.target.value)}
                        disabled={loading}
                        autoComplete="name"
                      />
                    </div>
                    {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
                  </div>

                  <div>
                    <label className="label">Email Address</label>
                    <div className="input-group">
                      <Mail className="input-icon" />
                      <input
                        type="email"
                        className={`input-with-icon ${errors.email ? 'input-error' : ''}`}
                        placeholder="you@company.com"
                        value={form.email}
                        onChange={(e) => updateField('email', e.target.value)}
                        disabled={loading}
                        autoComplete="email"
                      />
                    </div>
                    {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email}</p>}
                  </div>

                  <div className="pt-2">
                    <button
                      type="button"
                      onClick={nextStep}
                      className="btn-primary w-full flex items-center justify-center gap-2"
                    >
                      Continue <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              )}

              {/* Step 2: Password */}
              {step === 2 && (
                <motion.div
                  key="step2"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-5"
                >
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Secure Your Account</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Create a strong password</p>
                  </div>

                  <div>
                    <label className="label">Password</label>
                    <div className="input-group">
                      <Lock className="input-icon" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        className={`input-with-icon pr-10 ${errors.password ? 'input-error' : ''}`}
                        placeholder="Create a strong password"
                        value={form.password}
                        onChange={(e) => updateField('password', e.target.value)}
                        disabled={loading}
                        autoComplete="new-password"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        tabIndex={-1}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password}</p>}
                    <PasswordStrength password={form.password} />
                  </div>

                  <div>
                    <label className="label">Confirm Password</label>
                    <div className="input-group">
                      <Lock className="input-icon" />
                      <input
                        type="password"
                        className={`input-with-icon ${errors.confirmPassword ? 'input-error' : ''}`}
                        placeholder="Repeat your password"
                        value={form.confirmPassword}
                        onChange={(e) => updateField('confirmPassword', e.target.value)}
                        disabled={loading}
                        autoComplete="new-password"
                      />
                    </div>
                    {errors.confirmPassword && <p className="text-red-500 text-xs mt-1">{errors.confirmPassword}</p>}
                  </div>

                  <div className="flex gap-3 pt-2">
                    <button type="button" onClick={prevStep} className="btn-secondary flex-1">
                      <ArrowLeft className="w-4 h-4" /> Back
                    </button>
                    <button type="button" onClick={nextStep} className="btn-primary flex-1">
                      Continue <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              )}

              {/* Step 3: Organization Info */}
              {step === 3 && (
                <motion.div
                  key="step3"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-5"
                >
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-cyber-500" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Almost there!</h3>
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Set up your workspace</p>

                  <div>
                    <label className="label">Company / Organization</label>
                    <div className="input-group">
                      <Building2 className="input-icon" />
                      <input
                        type="text"
                        className="input-with-icon"
                        placeholder="Acme Corp"
                        value={form.company}
                        onChange={(e) => updateField('company', e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="label">Department</label>
                      <div className="input-group">
                        <Briefcase className="input-icon" />
                        <input
                          type="text"
                          className="input-with-icon"
                          placeholder="Engineering"
                          value={form.department}
                          onChange={(e) => updateField('department', e.target.value)}
                        />
                      </div>
                    </div>
                    <div>
                      <label className="label">Role</label>
                      <select
                        className="input-field"
                        value={form.role}
                        onChange={(e) => updateField('role', e.target.value)}
                      >
                        <option value="">Select...</option>
                        {roles.map((r) => (
                          <option key={r.value} value={r.value}>{r.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="label">Cloud Provider</label>
                    <div className="grid grid-cols-3 gap-2">
                      {cloudProviders.map((cp) => (
                        <button
                          key={cp.value}
                          type="button"
                          onClick={() => updateField('cloudProvider', cp.value)}
                          className={`p-3 rounded-xl text-sm font-medium border transition-all duration-200 ${
                            form.cloudProvider === cp.value
                              ? 'bg-cyber-50 dark:bg-cyber-900/20 border-cyber-300 dark:border-cyber-700 text-cyber-700 dark:text-cyber-400'
                              : 'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300'
                          }`}
                        >
                          <Cloud className={`w-4 h-4 mx-auto mb-1 ${
                            form.cloudProvider === cp.value ? 'text-cyber-500' : 'text-gray-400'
                          }`} />
                          {cp.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-3 pt-2">
                    <button type="button" onClick={prevStep} className="btn-secondary flex-1">
                      <ArrowLeft className="w-4 h-4" /> Back
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="btn-primary flex-1"
                    >
                      {loading ? (
                        <div className="flex items-center gap-2">
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          Creating...
                        </div>
                      ) : (
                        <span className="flex items-center justify-center gap-2">
                          Create Account <ChevronRight className="w-4 h-4" />
                        </span>
                      )}
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </form>

          {/* Login link */}
          <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-6 pt-4 border-t border-gray-100 dark:border-gray-700">
            Already have an account?{' '}
            <Link to="/login" className="text-cyber-600 dark:text-cyber-400 hover:underline font-semibold">
              Sign in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
