import React, { useState, useEffect, useRef } from 'react';
import {
  LayoutDashboard,
  Users,
  FolderGit2,
  Clock,
  Receipt,
  Package,
  ShieldCheck,
  Building2,
  Users2,
  LogOut,
  Zap,
  Activity,
  Layers,
  ChevronRight,
  Search,
  X,
  Loader2,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { healthService } from '../../services/healthService';
import { searchService } from '../../services/dashboardService';
import { Badge } from '../common/Badge';
import type { SearchResult } from '../../types';

export type MainNavView =
  | 'dashboard'
  | 'customers'
  | 'projects'
  | 'followups'
  | 'payments'
  | 'products'
  | 'audit'
  | 'users'
  | 'tenant';

interface AppShellProps {
  currentView: MainNavView;
  onNavigate: (view: MainNavView) => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentView,
  onNavigate,
  children,
}) => {
  const { user, organization, logout } = useAuth();
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  // Global search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

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
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  // Debounced search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await searchService.search(searchQuery.trim(), 8);
        setSearchResults(res?.results || []);
        setShowSearchResults(true);
      } catch (err) {
        console.error('Search error', err);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Click outside search
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSearchResults(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearchResultClick = (result: SearchResult) => {
    setShowSearchResults(false);
    setSearchQuery('');
    if (result.entity_type === 'customer') {
      onNavigate('customers');
    } else if (result.entity_type === 'project') {
      onNavigate('projects');
    } else if (result.entity_type === 'product') {
      onNavigate('products');
    }
  };

  const crmNavItems = [
    { id: 'dashboard', label: 'Command Center', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'customers', label: 'Customers & Contacts', icon: <Users className="w-4 h-4" /> },
    { id: 'projects', label: 'Projects & Pipeline', icon: <FolderGit2 className="w-4 h-4" /> },
    { id: 'followups', label: 'Operator Follow-ups', icon: <Clock className="w-4 h-4" /> },
    { id: 'payments', label: 'Payments & Financials', icon: <Receipt className="w-4 h-4" /> },
    { id: 'products', label: 'Product Catalog', icon: <Package className="w-4 h-4" /> },
  ] as const;

  const adminNavItems = [
    { id: 'audit', label: 'Security Audit Trail', icon: <ShieldCheck className="w-4 h-4" /> },
    { id: 'users', label: 'User Directory', icon: <Users2 className="w-4 h-4" /> },
    { id: 'tenant', label: 'Tenant Profile', icon: <Building2 className="w-4 h-4" /> },
  ] as const;

  return (
    <div className="min-h-screen bg-[#0b0f19] flex text-slate-100 font-sans selection:bg-cyan-500/30">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-950/90 border-r border-slate-800/80 flex flex-col justify-between shrink-0">
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
                  CRM v2
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Core Operator Platform</p>
            </div>
          </div>

          {/* Active Tenant Partition Pill */}
          <div className="px-4 py-3 mx-3 my-4 rounded-xl bg-slate-900/90 border border-slate-800">
            <div className="flex items-center gap-2 text-xs text-slate-400 font-medium mb-1">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>Isolated Tenant</span>
            </div>
            <p className="text-sm font-semibold text-slate-200 truncate" title={organization?.name}>
              {organization?.name || 'Default Organization'}
            </p>
            <div className="flex items-center gap-1.5 mt-1.5 text-[10px] text-slate-500 font-mono">
              <span>tier: {organization?.tier || 'standard'}</span>
            </div>
          </div>

          {/* Core CRM Navigation */}
          <div className="px-3 mb-2">
            <span className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Core CRM Modules
            </span>
          </div>
          <nav className="px-3 space-y-1 mb-6">
            {crmNavItems.map((item) => {
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

          {/* Admin & Security Section */}
          <div className="px-3 mb-2">
            <span className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Platform & Security
            </span>
          </div>
          <nav className="px-3 space-y-1">
            {adminNavItems.map((item) => {
              const active = currentView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2 rounded-lg text-xs font-medium transition-all ${
                    active
                      ? 'bg-slate-800 text-slate-200 border border-slate-700'
                      : 'text-slate-500 hover:text-slate-300 hover:bg-slate-900/40'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    {item.icon}
                    <span>{item.label}</span>
                  </div>
                  {active && <ChevronRight className="w-3.5 h-3.5 text-slate-400" />}
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
        {/* Top Header with Global Search */}
        <header className="h-16 px-8 border-b border-slate-800/80 bg-slate-950/40 backdrop-blur-md flex items-center justify-between sticky top-0 z-20 gap-4">
          {/* Global Search Bar */}
          <div ref={searchRef} className="relative w-full max-w-md">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => {
                  if ((searchResults || []).length > 0) setShowSearchResults(true);
                }}
                placeholder="Search customers, phones, projects, or products..."
                className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-8 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
              />
              {isSearching ? (
                <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin absolute right-3 top-1/2 -translate-y-1/2" />
              ) : searchQuery ? (
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setSearchResults([]);
                    setShowSearchResults(false);
                  }}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              ) : null}
            </div>

            {/* Floating Search Results Dropdown */}
            {showSearchResults && (
              <div className="absolute left-0 right-0 mt-2 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden z-50">
                <div className="p-2 border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                  <span>Found {(searchResults || []).length} matches</span>
                  <span className="text-[10px] text-slate-500">PostgreSQL search</span>
                </div>
                {(searchResults || []).length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-500 italic">
                    No matching records found in this tenant.
                  </div>
                ) : (
                  <div className="max-h-72 overflow-y-auto divide-y divide-slate-800/60">
                    {(searchResults || []).map((r) => (
                      <div
                        key={`${r.entity_type}-${r.id}`}
                        onClick={() => handleSearchResultClick(r)}
                        className="p-3 hover:bg-slate-800/60 cursor-pointer transition-colors flex items-center justify-between gap-3"
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-xs text-slate-200 truncate">
                              {r.title}
                            </span>
                            <Badge
                              variant={
                                r.entity_type === 'customer'
                                  ? 'info'
                                  : r.entity_type === 'project'
                                  ? 'warning'
                                  : 'neutral'
                              }
                              size="sm"
                            >
                              {r.entity_type.toUpperCase()}
                            </Badge>
                          </div>
                          {r.subtitle && (
                            <p className="text-[11px] text-slate-400 truncate mt-0.5">{r.subtitle}</p>
                          )}
                          {r.details && (
                            <p className="text-[10px] text-slate-500 truncate">{r.details}</p>
                          )}
                        </div>
                        <ExternalLink className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center gap-4">
            {/* System Status Pill */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs">
              <Activity className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-400">Gateway:</span>
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
              {user?.role_name || 'Operator'}
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
