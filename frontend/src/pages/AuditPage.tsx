import React, { useEffect, useState } from 'react';
import { ShieldCheck, RefreshCw, ChevronLeft, ChevronRight, Filter } from 'lucide-react';
import { auditService } from '../services/auditService';
import type { AuditLog } from '../types';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [actionFilter, setActionFilter] = useState<string>('');
  const [resourceFilter, setResourceFilter] = useState<string>('');

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const data = await auditService.getAuditLogs(
        page,
        15,
        actionFilter || undefined,
        resourceFilter || undefined
      );
      setLogs(data?.items || []);
      setTotal(data?.total || 0);
      setTotalPages(data?.total_pages || 1);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
      setLogs([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, actionFilter, resourceFilter]);

  const getActionBadgeVariant = (action: string) => {
    switch (action.toUpperCase()) {
      case 'LOGIN':
        return 'info';
      case 'REGISTER':
        return 'success';
      case 'USER_CREATE':
        return 'warning';
      case 'LOGOUT':
        return 'neutral';
      default:
        return 'neutral';
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <span>Immutable Audit Trail</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Tamper-resistant security and operational event log strictly scoped to your tenant.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={fetchLogs}
            isLoading={isLoading}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh Logs
          </Button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center gap-3 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Filter className="w-3.5 h-3.5 text-cyan-400" />
          <span>Filters:</span>
        </div>

        <select
          value={actionFilter}
          onChange={(e) => {
            setActionFilter(e.target.value);
            setPage(1);
          }}
          className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500 cursor-pointer"
        >
          <option value="">All Actions</option>
          <option value="LOGIN">LOGIN</option>
          <option value="REGISTER">REGISTER</option>
          <option value="USER_CREATE">USER_CREATE</option>
          <option value="LOGOUT">LOGOUT</option>
          <option value="ORGANIZATION_UPDATE">ORGANIZATION_UPDATE</option>
        </select>

        <select
          value={resourceFilter}
          onChange={(e) => {
            setResourceFilter(e.target.value);
            setPage(1);
          }}
          className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500 cursor-pointer"
        >
          <option value="">All Resources</option>
          <option value="auth">Auth</option>
          <option value="organization">Organization</option>
          <option value="user">User</option>
        </select>

        <span className="text-xs text-slate-500 ml-auto font-mono">
          Total Recorded: {total} events
        </span>
      </div>

      {/* Audit Logs Table */}
      <Card>
        {(!logs || logs.length === 0) && !isLoading ? (
          <EmptyState
            icon={<ShieldCheck className="w-6 h-6" />}
            title="No audit events found"
            description="No security or mutation events match the current filter criteria."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] uppercase tracking-wider text-slate-400 bg-slate-950/40 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-semibold">Timestamp (UTC)</th>
                  <th className="py-3 px-4 font-semibold">Action</th>
                  <th className="py-3 px-4 font-semibold">Resource</th>
                  <th className="py-3 px-4 font-semibold">Actor</th>
                  <th className="py-3 px-4 font-semibold">IP Address</th>
                  <th className="py-3 px-4 font-semibold">Metadata Payload</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {(logs || []).map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant={getActionBadgeVariant(log.action)} size="sm">
                        {log.action}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      <span className="text-cyan-400 font-semibold">{log.resource}</span>
                      {log.resource_id && (
                        <span className="text-[10px] text-slate-500 ml-1">({log.resource_id.substring(0, 8)}...)</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-sans">
                      {log.actor_email || 'System'}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {log.ip_address || '127.0.0.1'}
                    </td>
                    <td className="py-3 px-4 text-slate-400 max-w-xs truncate text-[11px]" title={log.metadata_json || ''}>
                      {log.metadata_json || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between pt-4 mt-4 border-t border-slate-800/80">
            <span className="text-xs text-slate-400">
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
