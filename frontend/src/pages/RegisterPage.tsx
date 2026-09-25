import React, { useState } from 'react';
import { Zap, Lock, Mail, User, Building, ArrowRight, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';

interface RegisterPageProps {
  onSwitchToLogin: () => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ onSwitchToLogin }) => {
  const { register } = useAuth();
  const { showToast } = useNotification();
  const [orgName, setOrgName] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      await register({
        organization_name: orgName,
        full_name: fullName,
        email,
        password,
      });
      showToast('success', 'Tenant Registered', `Welcome to Enermax! Your tenant organization "${orgName}" is live.`);
    } catch (err: any) {
      const msg = err.message || 'Registration failed. Please check your inputs.';
      setError(msg);
      showToast('error', 'Registration Failed', msg);
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
          <p className="text-xs text-slate-400 mt-1">Multi-Tenant SaaS Foundation Setup</p>
        </div>

        {/* Form Container */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-md">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-white">Register Organization</h2>
            <p className="text-xs text-slate-400 mt-0.5">Provision an isolated tenant partition and administrator account</p>
          </div>

          {error && (
            <div className="p-3 mb-5 rounded-lg bg-rose-950/60 border border-rose-800/60 text-xs text-rose-300 font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Organization / Company Name"
              type="text"
              required
              placeholder="e.g. Enermax Systems India"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              leftIcon={<Building className="w-4 h-4" />}
            />

            <Input
              label="Admin Full Name"
              type="text"
              required
              placeholder="e.g. Karuna K"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              leftIcon={<User className="w-4 h-4" />}
            />

            <Input
              label="Admin Corporate Email"
              type="email"
              required
              placeholder="admin@enermax.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              leftIcon={<Mail className="w-4 h-4" />}
            />

            <Input
              label="Secure Password"
              type="password"
              required
              placeholder="Minimum 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              helperText="Argon2/Bcrypt salted cryptographic hash stored server-side."
              leftIcon={<Lock className="w-4 h-4" />}
            />

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isLoading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
              className="w-full mt-2"
            >
              Provision Tenant & Launch
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-800/80 text-center">
            <button
              type="button"
              onClick={onSwitchToLogin}
              className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Sign In</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
