import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  ShieldCheck,
  Building2,
  Users,
  LogOut,
  Zap,
  Activity,
  Layers,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { healthService } from '../../services/healthService';
import { Badge } from '../common/Badge';

interface AppShellProps {
  currentView: 'dashboard' | 'audit' | 'users' | 'tenant';
  onNavigate: (view: 'dashboard' | 'audit' | 'users' | 'tenant') => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentView,
  onNavigate,
  children,
}) => {
  const { user, organization, logout } = useAuth();
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const health = await healthService.getHealth();
        setIsBackendHealthy(health.status === 'ok');
      } catch {
        setIsBackendHealthy(false);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'dashboard', label: 'Overview & Health', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'audit', label: 'Audit Trail', icon: <ShieldCheck className="w-4 h-4" /> },
    { id: 'users', label: 'User Directory', icon: <Users className="w-4 h-4" /> },
    { id: 'tenant', label: 'Tenant Profile', icon: <Building2 className="w-4 h-4" /> },
  ] as const;

  return (
    <div className="min-h-screen bg-[#0b0f19] flex text-slate-100 font-sans selection:bg-cyan-500/30">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-950/80 border-r border-slate-800/80 flex flex-col justify-between shrink-0">
        <div>
          {/* Brand Header */}
          <div className="p-5 border-b border-slate-800/80 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-sky-400 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20">
              <Zap className="w-5 h-5 fill-white text-white" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight text-white">ENERMAX</span>
                <span className="text-[10px] bg-cyan-950 text-cyan-400 font-semibold px-1.5 py-0.5 rounded border border-cyan-800/60">
                  CRM
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Phase 1 Foundation</p>
            </div>
          </div>

          {/* Active Tenant Card */}
          <div className="px-4 py-3 mx-3 my-4 rounded-xl bg-slate-900/90 border border-slate-800">
            <div className="flex items-center gap-2 text-xs text-slate-400 font-medium mb-1">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>Active Tenant</span>
            </div>
            <p className="text-sm font-semibold text-slate-200 truncate" title={organization?.name}>
              {organization?.name || 'Default Organization'}
            </p>
            <div className="flex items-center gap-1.5 mt-2">
              <span className="text-[10px] text-slate-400 font-mono">slug: {organization?.slug}</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="px-3 space-y-1">
            {navItems.map((item) => {
              const active = currentView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    active
                      ? 'bg-cyan-600/15 text-cyan-400 border border-cyan-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {item.icon}
                    <span>{item.label}</span>
                  </div>
                  {active && <ChevronRight className="w-4 h-4 text-cyan-400" />}
                </button>
              );
            })}
          </nav>
        </div>

        {/* User Footer and Logout */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-semibold text-xs text-cyan-400 shrink-0">
                {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-200 truncate">{user?.full_name}</p>
                <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-900 transition-colors shrink-0"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="h-16 px-8 border-b border-slate-800/80 bg-slate-950/40 backdrop-blur-md flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold text-slate-100 capitalize">
              {navItems.find((n) => n.id === currentView)?.label || 'Enermax SaaS Platform'}
            </h1>
            <span className="text-xs text-slate-500 font-mono">/api/v1</span>
          </div>

          <div className="flex items-center gap-4">
            {/* System Status Pill */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs">
              <Activity className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-400">API Gateway:</span>
              {isBackendHealthy === null ? (
                <span className="text-slate-400">Checking...</span>
              ) : isBackendHealthy ? (
                <Badge variant="success" size="sm" dot>Live</Badge>
              ) : (
                <Badge variant="error" size="sm" dot>Degraded</Badge>
              )}
            </div>

            {/* Role Badge */}
            <Badge variant="info" size="md">
              {user?.role_name || 'Administrator'}
            </Badge>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 p-8 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
