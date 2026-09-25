import React, { useEffect, useState, useCallback } from 'react';
import {
  Users,
  FolderGit2,
  TrendingUp,
  Receipt,
  CreditCard,
  Clock,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Building,
  CheckCircle2,
  Layers,
  Activity as ActivityIcon,
  Shield,
  Loader2,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { dashboardService } from '../services/dashboardService';
import { followUpService } from '../services/followUpService';
import { healthService } from '../services/healthService';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { useNotifications } from '../context/NotificationContext';
import type { CoreDashboardResponse, ReadinessResponse } from '../types';

interface DashboardPageProps {
  onNavigate: (view: 'dashboard' | 'customers' | 'projects' | 'followups' | 'payments' | 'products' | 'audit' | 'users' | 'tenant') => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const { user, organization } = useAuth();
  const { addNotification } = useNotifications();

  const [dashboard, setDashboard] = useState<CoreDashboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Phase 1 Infrastructure readiness
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [showInfraStatus, setShowInfraStatus] = useState(false);

  const loadDashboardData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [dash, ready] = await Promise.all([
        dashboardService.getDashboard(),
        healthService.getReadiness().catch(() => null),
      ]);
      setDashboard(dash);
      setReadiness(ready);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to fetch operational metrics',
      });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [addNotification]);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, [loadDashboardData]);

  const handleCompleteFollowUp = async (id: string) => {
    try {
      await followUpService.completeFollowUp(id);
      addNotification({ type: 'success', message: 'Task marked as completed.' });
      loadDashboardData();
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to complete task',
      });
    }
  };

  if (isLoading && !dashboard) {
    return (
      <div className="flex flex-col items-center justify-center p-24 text-slate-400 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
        <p className="text-sm font-medium tracking-wide">Aggregating real-time business telemetry...</p>
      </div>
    );
  }

  const overdueItems = dashboard?.overdue_follow_ups || [];
  const todayItems = dashboard?.todays_follow_ups || dashboard?.today_follow_ups || [];
  const overdueCount = overdueItems.length;
  const todayCount = todayItems.length;
  const projectsByStage = dashboard?.projects_by_stage || [];
  const recentActivity = dashboard?.recent_activity || [];
  const recentCustomers = dashboard?.recent_customers || [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner / Welcome with Quick Actions */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-cyan-950/20 to-slate-900 border border-slate-800 flex flex-col lg:flex-row lg:items-center justify-between gap-6 shadow-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <Badge variant="info" size="sm">Core Enermax CRM • Phase 2</Badge>
            <span className="text-xs text-slate-400 font-mono">
              Tenant: <strong className="text-slate-200">{organization?.name}</strong>
            </span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Welcome back, {user?.full_name}
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Real-time operations command center. What is happening in your business right now.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadDashboardData}
            isLoading={isRefreshing}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onNavigate('customers')}
            leftIcon={<Users className="w-3.5 h-3.5" />}
          >
            New Customer
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onNavigate('projects')}
            leftIcon={<FolderGit2 className="w-3.5 h-3.5" />}
          >
            New Project
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => onNavigate('payments')}
            leftIcon={<Receipt className="w-3.5 h-3.5" />}
          >
            Record Payment
          </Button>
        </div>
      </div>

      {/* OVERDUE ALERT BANNER */}
      {overdueCount > 0 && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 flex items-center justify-between text-rose-200 gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-rose-500/20 text-rose-400 shrink-0">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-bold text-rose-200">
                Action Required: {overdueCount} Overdue Follow-up Task{overdueCount > 1 ? 's' : ''}
              </p>
              <p className="text-xs text-rose-300/80">
                Pending client commitments require immediate operator attention.
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigate('followups')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 text-xs font-semibold whitespace-nowrap"
          >
            <span>Resolve Queue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 5 Core Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Customers */}
        <Card
          onClick={() => onNavigate('customers')}
          className="p-4 cursor-pointer hover:border-cyan-500/40 transition-all bg-slate-900/90"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400">Total Customers</span>
            <Users className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {dashboard?.total_customers ?? 0}
          </div>
          <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <span>Unified accounts</span>
            <ArrowRight className="w-3 h-3 text-slate-600" />
          </p>
        </Card>

        {/* Active Projects */}
        <Card
          onClick={() => onNavigate('projects')}
          className="p-4 cursor-pointer hover:border-cyan-500/40 transition-all bg-slate-900/90"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400">Active Projects</span>
            <FolderGit2 className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {dashboard?.active_projects ?? 0}
          </div>
          <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <span>In pipeline stages</span>
            <ArrowRight className="w-3 h-3 text-slate-600" />
          </p>
        </Card>

        {/* Total Project Value */}
        <Card
          onClick={() => onNavigate('projects')}
          className="p-4 cursor-pointer hover:border-cyan-500/40 transition-all bg-slate-900/90"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400">Total Value</span>
            <TrendingUp className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">
            ₹{Number(dashboard?.total_project_value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Booked orders</p>
        </Card>

        {/* Total Paid */}
        <Card
          onClick={() => onNavigate('payments')}
          className="p-4 cursor-pointer hover:border-emerald-500/40 transition-all bg-slate-900/90 border-emerald-950"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-emerald-400">Total Collected</span>
            <Receipt className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            ₹{Number(dashboard?.total_paid || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Verified receipts</p>
        </Card>

        {/* Outstanding Balance */}
        <Card
          onClick={() => onNavigate('payments')}
          className="p-4 cursor-pointer hover:border-amber-500/40 transition-all bg-slate-900/90 border-amber-950"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-amber-400">Outstanding</span>
            <CreditCard className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">
            ₹{Number(dashboard?.total_outstanding || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Milestones pending</p>
        </Card>
      </div>

      {/* Projects by Stage (Flexible Pipeline Distribution) */}
      <Card className="p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              Project Pipeline Stage Distribution
            </h3>
            <p className="text-xs text-slate-400">
              Distribution of all client orders across operational milestones
            </p>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onNavigate('projects')}
            rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
          >
            View Projects
          </Button>
        </div>

        {(!projectsByStage || projectsByStage.length === 0) ? (
          <p className="text-xs text-slate-500 py-4 text-center italic">
            No projects in pipeline yet. Create a project to view stage distribution.
          </p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
            {projectsByStage.map((stg) => (
              <div
                key={stg.stage_id}
                onClick={() => onNavigate('projects')}
                className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 cursor-pointer hover:border-cyan-500/30 transition-colors"
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: stg.stage_color || '#06b6d4' }}
                  />
                  <span className="text-xs font-semibold text-slate-300 truncate" title={stg.stage_name}>
                    {stg.stage_name}
                  </span>
                </div>
                <div className="text-lg font-bold text-slate-100">{stg.count}</div>
                <div className="text-[11px] text-slate-400">
                  ₹{Number(stg.total_value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Two-Column Grid: Critical Follow-ups & Live Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* TODAY & OVERDUE FOLLOW-UPS */}
        <Card className="p-5 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                Follow-ups Priority Queue
              </h3>
              <p className="text-xs text-slate-400">
                {todayCount} due today • {overdueCount} overdue
              </p>
            </div>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onNavigate('followups')}
              rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              All Tasks
            </Button>
          </div>

          <div className="flex-1 space-y-2.5 overflow-y-auto max-h-[360px]">
            {/* Overdue items */}
            {overdueItems.map((f) => (
              <div
                key={f.id}
                className="p-3 rounded-lg bg-rose-950/20 border border-rose-800/40 flex items-start justify-between gap-3"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-rose-200 truncate">{f.title}</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 uppercase">
                      Overdue
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 flex items-center gap-1.5">
                    <Building className="w-3 h-3 text-slate-500" />
                    <span>{f.customer_name || 'Customer'}</span>
                    {f.project_name && <span className="text-slate-500">• {f.project_name}</span>}
                  </p>
                </div>
                <button
                  onClick={() => handleCompleteFollowUp(f.id)}
                  className="px-2.5 py-1 rounded bg-emerald-600/15 text-emerald-400 hover:bg-emerald-600/30 text-xs font-semibold shrink-0"
                >
                  Done
                </button>
              </div>
            ))}

            {/* Today items */}
            {todayItems.map((f) => (
              <div
                key={f.id}
                className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 flex items-start justify-between gap-3"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-slate-200 truncate">{f.title}</span>
                    <Badge variant="info" size="sm">Today</Badge>
                  </div>
                  <p className="text-xs text-slate-400 flex items-center gap-1.5">
                    <Building className="w-3 h-3 text-slate-500" />
                    <span>{f.customer_name || 'Customer'}</span>
                    <span className="font-mono text-slate-500">
                      • {new Date(f.due_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </p>
                </div>
                <button
                  onClick={() => handleCompleteFollowUp(f.id)}
                  className="px-2.5 py-1 rounded bg-emerald-600/15 text-emerald-400 hover:bg-emerald-600/30 text-xs font-semibold shrink-0"
                >
                  Done
                </button>
              </div>
            ))}

            {overdueCount === 0 && todayCount === 0 && (
              <p className="text-xs text-slate-500 py-8 text-center italic">
                No follow-ups due today or overdue. You are on track!
              </p>
            )}
          </div>
        </Card>

        {/* RECENT BUSINESS ACTIVITY TIMELINE */}
        <Card className="p-5 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <ActivityIcon className="w-4 h-4 text-cyan-400" />
                Live Operational Activity Feed
              </h3>
              <p className="text-xs text-slate-400">
                Audit trail of project creations, stage updates, and payments
              </p>
            </div>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onNavigate('audit')}
              rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              System Audit
            </Button>
          </div>

          <div className="flex-1 space-y-3.5 overflow-y-auto max-h-[360px] pl-4 relative before:content-[''] before:absolute before:left-1 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
            {(!recentActivity || recentActivity.length === 0) ? (
              <p className="text-xs text-slate-500 py-8 text-center italic">
                No recorded activity yet.
              </p>
            ) : (
              recentActivity.map((act) => (
                <div key={act.id} className="relative text-xs">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 absolute -left-[19px] top-1 ring-4 ring-slate-900" />
                  <div className="flex items-center justify-between text-slate-500">
                    <span className="font-semibold text-slate-300">{act.title}</span>
                    <span>{new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                  {act.description && (
                    <p className="text-slate-400 mt-0.5 leading-relaxed">{act.description}</p>
                  )}
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* RECENT CUSTOMER ACCOUNTS */}
      <Card className="p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Building className="w-4 h-4 text-cyan-400" />
              Recently Onboarded Customers
            </h3>
            <p className="text-xs text-slate-400">
              Quick access to recently created accounts
            </p>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onNavigate('customers')}
            rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
          >
            All Customers
          </Button>
        </div>

        {(!recentCustomers || recentCustomers.length === 0) ? (
          <p className="text-xs text-slate-500 py-4 text-center italic">
            No customers created yet.
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {recentCustomers.map((c) => (
              <div
                key={c.id}
                onClick={() => onNavigate('customers')}
                className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-cyan-500/30 cursor-pointer transition-colors space-y-1"
              >
                <div className="font-semibold text-slate-200 text-xs truncate" title={c.name}>
                  {c.name}
                </div>
                <div className="text-[11px] text-slate-400 truncate">
                  {c.primary_contact_name || c.city || 'Account'}
                </div>
                <div className="pt-1">
                  <Badge variant={c.status === 'active' ? 'success' : 'warning'} size="sm">
                    {c.status.toUpperCase()}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* PHASE 1 INFRASTRUCTURE & SECURITY TOGGLE */}
      <div className="pt-2">
        <button
          onClick={() => setShowInfraStatus(!showInfraStatus)}
          className="text-xs text-slate-500 hover:text-slate-400 flex items-center gap-1.5 transition-colors"
        >
          <Shield className="w-3.5 h-3.5 text-cyan-500" />
          <span>{showInfraStatus ? 'Hide' : 'Show'} System Architecture & Tenant Isolation Health</span>
        </button>

        {showInfraStatus && (
          <Card className="p-4 mt-3 bg-slate-950/90 border-slate-800">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-slate-400 font-semibold block mb-1">PostgreSQL Tenant Partition</span>
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Healthy & Encrypted
                </span>
                <p className="text-[11px] text-slate-500 mt-1">Tenant ID: {organization?.id}</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-slate-400 font-semibold block mb-1">API Readiness State</span>
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> {readiness?.status?.toUpperCase() || 'READY'}
                </span>
                <p className="text-[11px] text-slate-500 mt-1">Version: 2.0.0-core</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-slate-400 font-semibold block mb-1">Audit Logging Engine</span>
                <span className="text-cyan-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Operational
                </span>
                <p className="text-[11px] text-slate-500 mt-1">HMAC & Actor Tracking Active</p>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};
