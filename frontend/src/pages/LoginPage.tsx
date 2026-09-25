import React, { useState } from 'react';
import { Zap, Lock, Mail, ArrowRight, Building } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';

interface LoginPageProps {
  onSwitchToRegister: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onSwitchToRegister }) => {
  const { login } = useAuth();
  const { showToast } = useNotification();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [orgSlug, setOrgSlug] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login({
        email,
        password,
        organization_slug: orgSlug.trim() || undefined,
      });
      showToast('success', 'Authentication Successful', 'Welcome back to Enermax CRM.');
    } catch (err: any) {
      const msg = err.message || 'Invalid credentials or connection error.';
      setError(msg);
      showToast('error', 'Authentication Failed', msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] flex items-center justify-center p-6 text-slate-100 selection:bg-cyan-500/30">
      <div className="max-w-md w-full">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-600 to-sky-400 mx-auto flex items-center justify-center text-white shadow-xl shadow-cyan-500/20 mb-4">
            <Zap className="w-6 h-6 fill-white text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">ENERMAX CRM</h1>
          <p className="text-xs text-slate-400 mt-1">Enterprise-Grade SaaS Platform • Phase 1 Foundation</p>
        </div>

        {/* Form Container */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-md">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-white">Sign In</h2>
            <p className="text-xs text-slate-400 mt-0.5">Enter your credentials to access your tenant workspace</p>
          </div>

          {error && (
            <div className="p-3 mb-5 rounded-lg bg-rose-950/60 border border-rose-800/60 text-xs text-rose-300 font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Corporate Email"
              type="email"
              required
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              leftIcon={<Mail className="w-4 h-4" />}
            />

            <Input
              label="Password"
              type="password"
              required
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              leftIcon={<Lock className="w-4 h-4" />}
            />

            <Input
              label="Tenant Slug (Optional)"
              type="text"
              placeholder="e.g. enermax-solar"
              value={orgSlug}
              onChange={(e) => setOrgSlug(e.target.value)}
              helperText="Only required if your email exists in multiple tenant organizations."
              leftIcon={<Building className="w-4 h-4" />}
            />

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isLoading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
              className="w-full mt-2"
            >
              Sign In to Tenant
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-800/80 text-center">
            <p className="text-xs text-slate-400">
              New organization?{' '}
              <button
                type="button"
                onClick={onSwitchToRegister}
                className="text-cyan-400 hover:text-cyan-300 font-semibold transition-colors cursor-pointer"
              >
                Register Tenant Workspace
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
