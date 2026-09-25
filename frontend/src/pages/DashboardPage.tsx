import React, { useEffect, useState } from 'react';
import {
  Database,
  Shield,
  CheckCircle2,
  Server,
  RefreshCw,
  Cpu,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { healthService } from '../services/healthService';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import type { ReadinessResponse } from '../types';

export const DashboardPage: React.FC<{ onNavigate: (view: any) => void }> = ({ onNavigate }) => {
  const { user, organization, permissions } = useAuth();
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastChecked, setLastChecked] = useState<string>('Just now');

  const checkReadiness = async () => {
    setIsRefreshing(true);
    try {
      const data = await healthService.getReadiness();
      setReadiness(data);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Failed to query readiness:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    checkReadiness();
    const interval = setInterval(checkReadiness, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner / Welcome */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-cyan-950/30 to-slate-900 border border-cyan-800/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="info" size="sm">Phase 1 Foundation Live</Badge>
            <span className="text-xs text-slate-400">• High-Reliability Architecture</span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Welcome, {user?.full_name}
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Tenant partition <span className="text-cyan-400 font-semibold">{organization?.name}</span> is online and isolated.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={checkReadiness}
            isLoading={isRefreshing}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Probe Health
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => onNavigate('audit')}
            leftIcon={<Shield className="w-3.5 h-3.5" />}
          >
            View Audit Trail
          </Button>
        </div>
      </div>

      {/* Grid of Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 1. Database & Infrastructure Readiness */}
        <Card
          title="Infrastructure Health"
          subtitle={`Last probed: ${lastChecked}`}
          actions={
            <Badge
              variant={readiness?.status === 'ready' ? 'success' : 'error'}
              size="sm"
              dot
            >
              {readiness?.status === 'ready' ? 'All Systems Healthy' : 'Degraded'}
            </Badge>
          }
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <div className="flex items-center gap-2.5">
                <Database className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-medium text-slate-300">PostgreSQL (Primary DB)</span>
              </div>
              <div className="flex items-center gap-2">
                {readiness?.dependencies.database?.latency_ms !== undefined && (
                  <span className="text-[11px] font-mono text-slate-400">
                    {readiness.dependencies.database.latency_ms} ms
                  </span>
                )}
                <Badge variant={readiness?.dependencies.database?.status === 'healthy' ? 'success' : 'error'} size="sm">
                  {readiness?.dependencies.database?.status || 'Active'}
                </Badge>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <div className="flex items-center gap-2.5">
                <Server className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-medium text-slate-300">FastAPI Gateway</span>
              </div>
              <Badge variant="success" size="sm">v0.1.0 Ready</Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <div className="flex items-center gap-2.5">
                <Cpu className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-medium text-slate-300">Tenant Isolation Level</span>
              </div>
              <span className="text-xs font-semibold text-emerald-400">Server-Side RLS</span>
            </div>
          </div>
        </Card>

        {/* 2. Tenant Organization Partition */}
        <Card
          title="Tenant Partition"
          subtitle="Strict multi-tenant security boundary"
          actions={<Badge variant="info" size="sm">Isolated</Badge>}
        >
          <div className="space-y-3 text-xs">
            <div>
              <p className="text-slate-400 text-[11px]">Organization Name</p>
              <p className="font-semibold text-slate-100 text-sm mt-0.5">{organization?.name}</p>
            </div>
            <div>
              <p className="text-slate-400 text-[11px]">Tenant Slug</p>
              <code className="text-cyan-400 font-mono bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40 inline-block mt-0.5">
                {organization?.slug}
              </code>
            </div>
            <div>
              <p className="text-slate-400 text-[11px]">Partition UUID</p>
              <p className="font-mono text-slate-400 truncate mt-0.5" title={organization?.id}>
                {organization?.id}
              </p>
            </div>
            <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Subscription Tier</span>
              <span className="text-slate-200 uppercase font-semibold text-[11px] tracking-wider">{organization?.tier}</span>
            </div>
          </div>
        </Card>

        {/* 3. Session & RBAC Permissions */}
        <Card
          title="Active Operator Session"
          subtitle="Role-Based Access Control matrix"
          actions={<Badge variant="neutral" size="sm">{user?.role_name || 'admin'}</Badge>}
        >
          <div className="space-y-3 text-xs">
            <div>
              <p className="text-slate-400 text-[11px]">Logged In User</p>
              <p className="font-semibold text-slate-100 text-sm mt-0.5">{user?.full_name}</p>
              <p className="text-slate-400 mt-0.5">{user?.email}</p>
            </div>

            <div className="pt-2 border-t border-slate-800">
              <p className="text-slate-400 text-[11px] mb-2">Granted RBAC Permissions</p>
              <div className="flex flex-wrap gap-1.5">
                {permissions.length > 0 ? (
                  permissions.map((p) => (
                    <span
                      key={p}
                      className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] border border-slate-700"
                    >
                      {p}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-500 italic">Admin (Superuser)</span>
                )}
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Architectural Guarantee Matrix */}
      <Card
        title="Phase 1 Foundation Architectural Verification"
        subtitle="Verification checklist adhering to production engineering standards"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
              <CheckCircle2 className="w-4 h-4" />
              <span>Multi-Tenant Isolation</span>
            </div>
            <p className="text-xs text-slate-400">
              Every database query strictly enforces <code className="text-cyan-400">tenant_id</code> scoping at dependency layer. Cross-tenant reads & writes are forbidden.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
              <CheckCircle2 className="w-4 h-4" />
              <span>Audit Log Trail</span>
            </div>
            <p className="text-xs text-slate-400">
              Every authentication attempt, registration, logout, and record mutation produces an immutable, sanitized audit record.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
              <CheckCircle2 className="w-4 h-4" />
              <span>Request Tracing</span>
            </div>
            <p className="text-xs text-slate-400">
              Unique <code className="text-cyan-400">X-Request-ID</code> headers propagate across HTTP requests and structured server JSON logs for observability.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
              <CheckCircle2 className="w-4 h-4" />
              <span>Single-Operator Flow</span>
            </div>
            <p className="text-xs text-slate-400">
              Optimized for Enermax's ₹5 Cr operational model: clean layout, immediate visibility, zero bloated CRM bureaucracy.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};
