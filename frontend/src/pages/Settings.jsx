import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  User, Lock, Bell, Shield, Cloud, Info, Save, Eye, EyeOff, Check,
  Key, Smartphone, Globe, Server, Mail, Loader2,
  ChevronRight, ExternalLink, Monitor, Moon, Sun, LogOut,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../context/ThemeContext';
import { authService } from '../services/authService';
import toast from 'react-hot-toast';

const TABS = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'security', label: 'Security', icon: Lock },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'integrations', label: 'Integrations', icon: Cloud },
  { id: 'about', label: 'About', icon: Info },
];

const INTEGRATIONS = [
  {
    id: 'gcp',
    name: 'Google Cloud Platform',
    description: 'Cloud DLP, Pub/Sub, and Cloud Storage integration',
    icon: Globe,
    connected: true,
    color: 'from-blue-500 to-cyan-500',
  },
  {
    id: 'aws',
    name: 'AWS',
    description: 'Macie, S3, and GuardDuty integration',
    icon: Server,
    connected: false,
    color: 'from-orange-500 to-yellow-500',
  },
  {
    id: 'azure',
    name: 'Azure',
    description: 'Purview, Sentinel, and Blob Storage integration',
    icon: Monitor,
    connected: false,
    color: 'from-blue-600 to-indigo-600',
  },
  {
    id: 'ollama',
    name: 'Ollama AI',
    description: 'Local AI model for compliance analysis & recommendations',
    icon: Monitor,
    connected: true,
    color: 'from-green-500 to-emerald-600',
  },
];

export default function Settings() {
  const { user, updateUser } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('profile');

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-3"
      >
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyber-100 to-cyber-50 dark:from-cyber-900/30 dark:to-cyber-800/20 flex items-center justify-center">
          <Shield className="w-5 h-5 text-cyber-600 dark:text-cyber-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Manage your account, security, and preferences</p>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex overflow-x-auto gap-1 p-1 bg-gray-100 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700/50">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`relative flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg whitespace-nowrap transition-all ${
                isActive
                  ? 'text-cyber-700 dark:text-cyber-300'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-white/50 dark:hover:bg-gray-700/30'
              }`}
            >
              {isActive && (
                <motion.div
                  layoutId="settings-tab-bg"
                  className="absolute inset-0 bg-white dark:bg-gray-700 rounded-lg shadow-sm"
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-2">
                <Icon className="w-4 h-4" />
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'profile' && <ProfileSettings user={user} updateUser={updateUser} />}
          {activeTab === 'security' && <SecuritySettings />}
          {activeTab === 'notifications' && <NotificationSettings />}
          {activeTab === 'integrations' && <IntegrationSettings />}
          {activeTab === 'about' && <AboutSettings />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

/* ========== Profile Tab ========== */
function ProfileSettings({ user, updateUser }) {
  const [profileForm, setProfileForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    company: user?.company || '',
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const result = await authService.updateProfile({ name: profileForm.name, company: profileForm.company });
      updateUser({ ...user, name: profileForm.name, company: result?.company || profileForm.company });
      toast.success('Profile updated successfully');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const initials = (profileForm.name || 'U').charAt(0).toUpperCase();
  const avatarColors = [
    'from-cyber-500 to-blue-600', 'from-purple-500 to-pink-500', 'from-emerald-500 to-teal-600',
    'from-orange-500 to-red-500', 'from-indigo-500 to-purple-600',
  ];
  const avatarColor = avatarColors[(user?.id || 0) % avatarColors.length];

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Profile Card */}
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
          <User className="w-4 h-4 text-cyber-500" />
          Profile Information
        </h3>

        <div className="flex flex-col sm:flex-row items-start gap-6 mb-8">
          {/* Avatar */}
          <div className="relative">
            <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${avatarColor} flex items-center justify-center shadow-lg`}>
              <span className="text-3xl font-bold text-white">{initials}</span>
            </div>
            <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full border-2 border-white dark:border-gray-800 flex items-center justify-center">
              <Check className="w-3 h-3 text-white" />
            </div>
          </div>

          <div className="flex-1 space-y-1">
            <p className="text-lg font-semibold text-gray-900 dark:text-white">{user?.name || 'User'}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">{user?.email}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className="px-2.5 py-0.5 bg-cyber-100 dark:bg-cyber-900/30 text-cyber-700 dark:text-cyber-400 text-xs font-medium rounded-full">
                {user?.role || 'User'}
              </span>
              <span className="text-xs text-gray-400 dark:text-gray-500">
                ID: {user?.id ? `${String(user.id).substring(0, 8)}...` : '—'}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Full Name</label>
            <input
              type="text"
              className="input-field"
              value={profileForm.name}
              onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
              required
              minLength={2}
              placeholder="Your full name"
            />
          </div>
          <div>
            <label className="label">Email Address</label>
            <div className="input-group">
              <Mail className="w-4 h-4 text-gray-400" />
              <input
                type="email"
                className="input-field pl-10 bg-gray-50 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                value={profileForm.email}
                disabled
              />
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Email cannot be changed</p>
          </div>
          <div>
            <label className="label">Company / Organization</label>
            <input
              type="text"
              className="input-field"
              value={profileForm.company}
              onChange={(e) => setProfileForm({ ...profileForm, company: e.target.value })}
              placeholder="Your organization"
            />
          </div>
          <div>
            <label className="label">Department</label>
            <select className="input-field" defaultValue="">
              <option value="" disabled>Select department</option>
              <option>Engineering</option>
              <option>Security</option>
              <option>Compliance</option>
              <option>DevOps</option>
              <option>IT</option>
              <option>Management</option>
            </select>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-gray-100 dark:border-gray-700/50 flex gap-3">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={saving || !profileForm.name.trim()}
            className="btn-primary"
          >
            {saving ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</>
            ) : (
              <><Save className="w-4 h-4" /> Save Changes</>
            )}
          </motion.button>
        </div>
      </div>
    </form>
  );
}

/* ========== Security Tab ========== */
function SecuritySettings() {
  const [pwdForm, setPwdForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [changing, setChanging] = useState(false);
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [errors, setErrors] = useState({});
  const [mfaEnabled, setMfaEnabled] = useState(false);

  const passwordStrength = (pwd) => {
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/(?=.*[a-z])/.test(pwd)) score++;
    if (/(?=.*[A-Z])/.test(pwd)) score++;
    if (/(?=.*\d)/.test(pwd)) score++;
    if (/(?=.*[!@#$%^&*])/.test(pwd)) score++;
    return score;
  };

  const validate = () => {
    const errs = {};
    if (!pwdForm.current_password) errs.current_password = 'Current password is required';
    if (!pwdForm.new_password) errs.new_password = 'New password is required';
    else if (pwdForm.new_password.length < 8) errs.new_password = 'Must be at least 8 characters';
    if (pwdForm.new_password !== pwdForm.confirm_password) errs.confirm_password = 'Passwords do not match';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setChanging(true);
    try {
      await authService.changePassword(pwdForm.current_password, pwdForm.new_password);
      toast.success('Password changed successfully');
      setPwdForm({ current_password: '', new_password: '', confirm_password: '' });
      setErrors({});
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setChanging(false);
    }
  };

  const strength = passwordStrength(pwdForm.new_password);
  const strengthLabel = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'][strength];
  const strengthColors = [
    'bg-red-500', 'bg-red-400', 'bg-yellow-500', 'bg-yellow-400', 'bg-green-400', 'bg-emerald-500',
  ];

  const checks = [
    { label: '8+ characters', test: pwdForm.new_password.length >= 8 },
    { label: 'Lowercase', test: /(?=.*[a-z])/.test(pwdForm.new_password) },
    { label: 'Uppercase', test: /(?=.*[A-Z])/.test(pwdForm.new_password) },
    { label: 'Number', test: /(?=.*\d)/.test(pwdForm.new_password) },
    { label: 'Special char', test: /(?=.*[!@#$%^&*])/.test(pwdForm.new_password) },
  ];

  return (
    <div className="space-y-6">
      {/* Password Change */}
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
          <Key className="w-4 h-4 text-cyber-500" />
          Change Password
        </h3>

        <form onSubmit={handleSubmit} className="max-w-lg space-y-4">
          <div>
            <label className="label">Current Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type={showCurrent ? 'text' : 'password'}
                className={`input-field pl-10 pr-10 ${errors.current_password ? 'input-error' : ''}`}
                value={pwdForm.current_password}
                onChange={(e) => setPwdForm({ ...pwdForm, current_password: e.target.value })}
                placeholder="Enter current password"
              />
              <button type="button" onClick={() => setShowCurrent(!showCurrent)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.current_password && <p className="text-red-500 text-xs mt-1">{errors.current_password}</p>}
          </div>

          <div>
            <label className="label">New Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type={showNew ? 'text' : 'password'}
                className={`input-field pl-10 pr-10 ${errors.new_password ? 'input-error' : ''}`}
                value={pwdForm.new_password}
                onChange={(e) => setPwdForm({ ...pwdForm, new_password: e.target.value })}
                placeholder="Enter new password"
              />
              <button type="button" onClick={() => setShowNew(!showNew)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {/* Strength bar */}
            {pwdForm.new_password.length > 0 && (
              <div className="mt-2">
                <div className="flex gap-1 mb-1.5">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className={`h-1.5 flex-1 rounded-full ${i <= strength ? strengthColors[strength] : 'bg-gray-200 dark:bg-gray-700'}`} />
                  ))}
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                  Strength: <span className="font-medium">{strengthLabel}</span>
                </p>
                <div className="flex flex-wrap gap-x-3 gap-y-1">
                  {checks.map((c) => (
                    <span key={c.label} className={`text-xs flex items-center gap-1 ${c.test ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-400 dark:text-gray-500'}`}>
                      <Check className={`w-3 h-3 ${c.test ? 'text-emerald-500' : 'text-gray-300 dark:text-gray-600'}`} />
                      {c.label}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {errors.new_password && <p className="text-red-500 text-xs mt-1">{errors.new_password}</p>}
          </div>

          <div>
            <label className="label">Confirm New Password</label>
            <input
              type="password"
              className={`input-field ${errors.confirm_password ? 'input-error' : ''}`}
              value={pwdForm.confirm_password}
              onChange={(e) => setPwdForm({ ...pwdForm, confirm_password: e.target.value })}
              placeholder="Confirm new password"
            />
            {errors.confirm_password && <p className="text-red-500 text-xs mt-1">{errors.confirm_password}</p>}
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={changing}
            className="btn-primary"
          >
            {changing ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Updating...</>
            ) : (
              <><Lock className="w-4 h-4" /> Update Password</>
            )}
          </motion.button>
        </form>
      </div>

      {/* Multi-Factor Auth */}
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Smartphone className="w-4 h-4 text-cyber-500" />
          Multi-Factor Authentication
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Add an extra layer of security to your account by requiring a verification code from your mobile device.
        </p>
        <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg ${mfaEnabled ? 'bg-emerald-100 dark:bg-emerald-900/30' : 'bg-gray-100 dark:bg-gray-700'} flex items-center justify-center`}>
              <Shield className={`w-5 h-5 ${mfaEnabled ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-400'}`} />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">Authenticator App</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {mfaEnabled ? 'Two-factor authentication is enabled' : 'Not yet configured'}
              </p>
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setMfaEnabled(!mfaEnabled)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
              mfaEnabled
                ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30'
                : 'btn-primary text-sm'
            }`}
          >
            {mfaEnabled ? 'Disable' : 'Enable'}
          </motion.button>
        </div>
      </div>

      {/* Active Sessions */}
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Monitor className="w-4 h-4 text-cyber-500" />
          Active Sessions
        </h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
            <div className="flex items-center gap-3">
              <Globe className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Chrome on Windows</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Current session · IP: 192.168.x.x</p>
              </div>
            </div>
            <span className="text-xs px-2 py-0.5 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 rounded-full font-medium">Active now</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
            <div className="flex items-center gap-3">
              <Monitor className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Safari on macOS</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Last active 2 days ago</p>
              </div>
            </div>
            <button className="text-xs text-red-500 hover:text-red-600 font-medium">Revoke</button>
          </div>
        </div>
        <button className="mt-3 text-sm text-cyber-600 dark:text-cyber-400 hover:underline font-medium">
          Revoke all other sessions
        </button>
      </div>
    </div>
  );
}

/* ========== Notifications Tab ========== */
function NotificationSettings() {
  const [notifications, setNotifications] = useState({
    email_alerts: true,
    critical_alerts: true,
    scan_completed: true,
    scan_failed: true,
    weekly_summary: false,
    monthly_report: true,
    product_updates: false,
  });

  const toggle = (key) => {
    setNotifications((prev) => ({ ...prev, [key]: !prev[key] }));
    toast.success(`Notification ${notifications[key] ? 'disabled' : 'enabled'}`);
  };

  const groups = [
    {
      title: 'Alert Notifications',
      items: [
        { key: 'email_alerts', label: 'Email Alerts', desc: 'Receive alert notifications via email' },
        { key: 'critical_alerts', label: 'Critical Alerts', desc: 'Instant push notifications for critical severity alerts' },
      ],
    },
    {
      title: 'Scan Notifications',
      items: [
        { key: 'scan_completed', label: 'Scan Completed', desc: 'Notify when a file scan completes successfully' },
        { key: 'scan_failed', label: 'Scan Failed', desc: 'Notify when a file scan encounters errors' },
      ],
    },
    {
      title: 'Report & Summary',
      items: [
        { key: 'weekly_summary', label: 'Weekly Summary', desc: 'Receive weekly compliance summary report' },
        { key: 'monthly_report', label: 'Monthly Report', desc: 'Receive monthly detailed compliance report' },
        { key: 'product_updates', label: 'Product Updates', desc: 'New features, updates, and security patches' },
      ],
    },
  ];

  return (
    <div className="space-y-6">
      {groups.map((group) => (
        <div key={group.title} className="card">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">{group.title}</h3>
          <div className="space-y-2">
            {group.items.map((item) => (
              <div
                key={item.key}
                className="flex items-center justify-between p-3.5 rounded-xl bg-gray-50 dark:bg-gray-800/30 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-gray-700/50 cursor-pointer"
                onClick={() => toggle(item.key)}
              >
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{item.label}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{item.desc}</p>
                </div>
                <div
                  className={`relative w-11 h-6 rounded-full transition-colors flex-shrink-0 ${
                    notifications[item.key] ? 'bg-cyber-500' : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                >
                  <div
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-md transition-transform ${
                      notifications[item.key] ? 'translate-x-5' : ''
                    }`}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ========== Integrations Tab ========== */
function IntegrationSettings() {
  const [connecting, setConnecting] = useState(null);

  const handleConnect = async (id) => {
    setConnecting(id);
    await new Promise((r) => setTimeout(r, 1500));
    setConnecting(null);
    toast.success(`${id.toUpperCase()} integration ${id === 'ollama' ? 'configured' : 'requested'}`);
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-1">Cloud Provider Integrations</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Connect your cloud providers to enable automated scanning and compliance monitoring.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {INTEGRATIONS.map((integration, idx) => {
            const Icon = integration.icon;
            return (
              <motion.div
                key={integration.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className={`p-5 rounded-xl border transition-all ${
                  integration.connected
                    ? 'bg-gradient-to-br from-emerald-50/50 to-white dark:from-emerald-900/10 dark:to-gray-800/50 border-emerald-200 dark:border-emerald-800/30'
                    : 'bg-white dark:bg-gray-800/50 border-gray-200 dark:border-gray-700/50 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${integration.color} flex items-center justify-center`}>
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  {integration.connected && (
                    <span className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                      <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                      Connected
                    </span>
                  )}
                </div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">{integration.name}</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 leading-relaxed">{integration.description}</p>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleConnect(integration.id)}
                  disabled={connecting === integration.id}
                  className={`w-full py-2 text-sm font-medium rounded-lg transition-all ${
                    integration.connected
                      ? 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                      : 'bg-gradient-to-r from-cyber-600 to-cyber-500 text-white hover:shadow-md'
                  }`}
                >
                  {connecting === integration.id ? (
                    <><Loader2 className="w-3 h-3 animate-spin inline mr-1" /> Connecting...</>
                  ) : integration.connected ? (
                    'Configure'
                  ) : (
                    'Connect'
                  )}
                </motion.button>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* API Keys */}
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Key className="w-4 h-4 text-cyber-500" />
          API Keys
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          API keys for programmatic access to the SecureCloud AI platform.
        </p>
        <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/30 border border-dashed border-gray-200 dark:border-gray-700 text-center">
          <Key className="w-8 h-8 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
          <p className="text-sm text-gray-500 dark:text-gray-400">No API keys generated yet</p>
          <button className="mt-2 text-sm text-cyber-600 dark:text-cyber-400 hover:underline font-medium">
            Generate API Key
          </button>
        </div>
      </div>
    </div>
  );
}

/* ========== About Tab ========== */
function AboutSettings() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="space-y-6">
      {/* App Info */}
      <div className="card">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyber-500 to-blue-600 flex items-center justify-center shadow-lg">
            <Shield className="w-7 h-7 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">SecureCloud AI</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">Enterprise Privacy Security Platform</p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Version', value: '1.0.0' },
            { label: 'Frontend', value: 'React 18 + Vite' },
            { label: 'Backend', value: 'FastAPI (Python)' },
            { label: 'Database', value: 'PostgreSQL 15' },
          ].map((item) => (
            <div key={item.label} className="p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 text-center">
              <p className="text-xs text-gray-500 dark:text-gray-400">{item.label}</p>
              <p className="text-sm font-semibold text-gray-900 dark:text-white mt-0.5">{item.value}</p>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
              {theme === 'dark' ? <Moon className="w-5 h-5 text-cyber-400" /> : <Sun className="w-5 h-5 text-amber-500" />}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">Theme Preference</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{theme === 'dark' ? 'Dark mode' : 'Light mode'}</p>
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={toggleTheme}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          >
            Toggle {theme === 'dark' ? 'Light' : 'Dark'}
          </motion.button>
        </div>
      </div>

      {/* Tech Stack */}
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">Technology Stack</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { label: 'Frontend', value: 'React 18, Vite, TailwindCSS, Framer Motion' },
            { label: 'Charts', value: 'Recharts, D3' },
            { label: 'Icons', value: 'Lucide React' },
            { label: 'Forms', value: 'React Hook Form' },
            { label: 'API Client', value: 'Axios, TanStack React Query' },
            { label: 'Auth', value: 'JWT (access + refresh tokens)' },
            { label: 'AI/ML', value: 'Ollama (Llama 3 / Qwen)' },
            { label: 'Cloud', value: 'Google Cloud Platform' },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2 p-2.5 rounded-lg bg-gray-50 dark:bg-gray-800/30">
              <ChevronRight className="w-3 h-3 text-cyber-500 flex-shrink-0" />
              <div>
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">{item.label}:</span>{' '}
                <span className="text-xs text-gray-700 dark:text-gray-300">{item.value}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Resources */}
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">Resources</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { label: 'API Documentation', desc: 'Swagger / OpenAPI docs', href: '#' },
            { label: 'Support', desc: 'Help center & contact', href: '#' },
            { label: 'Status Page', desc: 'System uptime & incidents', href: '#' },
          ].map((item) => (
            <a key={item.label} href={item.href}
              className="flex items-center justify-between p-3.5 rounded-xl bg-gray-50 dark:bg-gray-800/30 hover:bg-gray-100 dark:hover:bg-gray-800/50 border border-gray-100 dark:border-gray-700/30 transition-colors group"
            >
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-cyber-600 dark:group-hover:text-cyber-400 transition-colors">{item.label}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{item.desc}</p>
              </div>
              <ExternalLink className="w-4 h-4 text-gray-300 dark:text-gray-600 group-hover:text-cyber-500 transition-colors" />
            </a>
          ))}
        </div>
      </div>

      {/* Footer */}
      <p className="text-center text-xs text-gray-400 dark:text-gray-600">
        &copy; {new Date().getFullYear()} SecureCloud AI. All rights reserved.
      </p>
    </div>
  );
}
