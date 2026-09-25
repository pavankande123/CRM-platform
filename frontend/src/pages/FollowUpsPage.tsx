import React, { useState, useEffect, useCallback } from 'react';
import {
  Clock,
  Plus,
  AlertCircle,
  Calendar,
  CheckCircle,
  X,
  Loader2,
  Building,
  FolderGit2,
} from 'lucide-react';
import { followUpService } from '../services/followUpService';
import { customerService } from '../services/customerService';
import { projectService } from '../services/projectService';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { useNotifications } from '../context/NotificationContext';
import type { FollowUp, FollowUpCreate, Customer, Project } from '../types';

export const FollowUpsPage: React.FC = () => {
  const { addNotification } = useNotifications();
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [viewFilter, setViewFilter] = useState<'all' | 'today' | 'overdue' | 'completed'>('today');

  // References for dropdowns
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);

  // Create Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<FollowUpCreate>({
    customer_id: '',
    project_id: '',
    title: '',
    description: '',
    due_date: new Date(Date.now() + 3600 * 1000 * 2).toISOString().slice(0, 16),
    priority: 'high',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Complete Modal
  const [completingId, setCompletingId] = useState<string | null>(null);
  const [completeNotes, setCompleteNotes] = useState('');
  const [isCompleting, setIsCompleting] = useState(false);

  useEffect(() => {
    const loadRefs = async () => {
      try {
        const [cRes, pRes] = await Promise.all([
          customerService.getCustomers({ pageSize: 100 }),
          projectService.getProjects({ pageSize: 100 }),
        ]);
        setCustomers(cRes?.items || []);
        setProjects(pRes?.items || []);
        if (cRes?.items?.[0]) {
          setCreateForm((prev) => ({ ...prev, customer_id: cRes.items[0].id }));
        }
      } catch (err) {
        console.error('Failed to load refs', err);
      }
    };
    loadRefs();
  }, []);

  const loadFollowUps = useCallback(async () => {
    setIsLoading(true);
    try {
      let params: { status?: string; today_only?: boolean; overdue_only?: boolean } = {};
      if (viewFilter === 'today') {
        params = { today_only: true, status: 'pending' };
      } else if (viewFilter === 'overdue') {
        params = { overdue_only: true, status: 'pending' };
      } else if (viewFilter === 'completed') {
        params = { status: 'completed' };
      } else {
        params = { status: 'pending' };
      }

      const res = await followUpService.getFollowUps({
        ...params,
        pageSize: 50,
      });
      setFollowUps(res?.items || []);
      setTotalCount(res?.total || 0);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to load follow-ups',
      });
      setFollowUps([]);
    } finally {
      setIsLoading(false);
    }
  }, [viewFilter, addNotification]);

  useEffect(() => {
    loadFollowUps();
  }, [loadFollowUps]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.title.trim() || !createForm.customer_id) {
      addNotification({ type: 'warning', message: 'Title and Customer are required.' });
      return;
    }

    setIsSubmitting(true);
    try {
      await followUpService.createFollowUp({
        ...createForm,
        due_date: new Date(createForm.due_date).toISOString(),
        project_id: createForm.project_id || undefined,
      });
      addNotification({ type: 'success', message: 'Follow-up task scheduled.' });
      setShowCreateModal(false);
      setCreateForm({
        customer_id: customers[0]?.id || '',
        project_id: '',
        title: '',
        description: '',
        due_date: new Date(Date.now() + 3600 * 1000 * 2).toISOString().slice(0, 16),
        priority: 'high',
      });
      loadFollowUps();
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to create follow-up',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleComplete = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!completingId) return;

    setIsCompleting(true);
    try {
      await followUpService.completeFollowUp(completingId, completeNotes.trim() || undefined);
      addNotification({ type: 'success', message: 'Follow-up marked as completed.' });
      setCompletingId(null);
      setCompleteNotes('');
      loadFollowUps();
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to complete task',
      });
    } finally {
      setIsCompleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Clock className="w-5 h-5 text-cyan-400" />
            Operator Follow-ups
          </h2>
          <p className="text-sm text-slate-400">
            Total of {totalCount} scheduled follow-ups across customers and projects.
          </p>
        </div>

        <Button
          variant="primary"
          icon={<Plus className="w-4 h-4" />}
          onClick={() => setShowCreateModal(true)}
        >
          Schedule Follow-up
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        {[
          { id: 'today', label: "Today's Schedule", icon: <Calendar className="w-4 h-4" /> },
          { id: 'overdue', label: 'Overdue Attention', icon: <AlertCircle className="w-4 h-4 text-rose-400" /> },
          { id: 'all', label: 'All Pending', icon: <Clock className="w-4 h-4" /> },
          { id: 'completed', label: 'Completed Archive', icon: <CheckCircle className="w-4 h-4 text-emerald-400" /> },
        ].map((tab) => {
          const active = viewFilter === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setViewFilter(tab.id as typeof viewFilter)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* List */}
      <Card>
        {isLoading ? (
          <div className="flex items-center justify-center p-12 text-slate-400 gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-cyan-500" />
            <span>Loading follow-ups...</span>
          </div>
        ) : (!followUps || followUps.length === 0) ? (
          <EmptyState
            title={
              viewFilter === 'overdue'
                ? 'No overdue follow-ups!'
                : viewFilter === 'today'
                ? 'No follow-ups due today'
                : 'No follow-up tasks'
            }
            description="You are completely up-to-date with customer and project follow-ups."
            actionLabel="Schedule Follow-up"
            onAction={() => setShowCreateModal(true)}
          />
        ) : (
          <div className="divide-y divide-slate-800/80">
            {(followUps || []).map((f) => (
              <div
                key={f.id}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-900/40 transition-colors"
              >
                <div className="space-y-1.5 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-200 text-sm">{f.title}</span>
                    <Badge
                      variant={
                        f.priority === 'urgent'
                          ? 'error'
                          : f.priority === 'high'
                          ? 'warning'
                          : 'neutral'
                      }
                      size="sm"
                    >
                      {f.priority.toUpperCase()}
                    </Badge>
                    {f.is_overdue && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 uppercase">
                        OVERDUE
                      </span>
                    )}
                    {f.is_today && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 uppercase">
                        TODAY
                      </span>
                    )}
                  </div>

                  {f.description && (
                    <p className="text-xs text-slate-400 leading-relaxed max-w-2xl">{f.description}</p>
                  )}

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-1">
                    <span className="flex items-center gap-1.5 text-slate-400">
                      <Building className="w-3.5 h-3.5 text-slate-500" />
                      {f.customer_name || 'Customer'}
                    </span>
                    {f.project_name && (
                      <span className="flex items-center gap-1.5 text-slate-400">
                        <FolderGit2 className="w-3.5 h-3.5 text-slate-500" />
                        {f.project_name}
                      </span>
                    )}
                    <span className="flex items-center gap-1.5 font-mono">
                      <Calendar className="w-3.5 h-3.5 text-slate-500" />
                      Due: {new Date(f.due_date).toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {f.status === 'pending' ? (
                    <button
                      onClick={() => setCompletingId(f.id)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/15 text-emerald-400 hover:bg-emerald-600/30 text-xs font-semibold transition-colors"
                    >
                      <CheckCircle className="w-4 h-4" />
                      <span>Complete Task</span>
                    </button>
                  ) : (
                    <span className="text-xs text-emerald-400 flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" />
                      Completed
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* COMPLETE MODAL */}
      {completingId && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-emerald-400" />
                Complete Follow-up Task
              </h3>
              <button onClick={() => setCompletingId(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleComplete} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Outcome / Call Notes
                </label>
                <textarea
                  rows={3}
                  value={completeNotes}
                  onChange={(e) => setCompleteNotes(e.target.value)}
                  placeholder="e.g. Spoke with client. Quotation accepted, site visit confirmed for Friday."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button variant="secondary" onClick={() => setCompletingId(null)} type="button">
                  Cancel
                </Button>
                <Button variant="primary" type="submit" isLoading={isCompleting}>
                  Confirm Completion
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CREATE MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg shadow-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Clock className="w-5 h-5 text-cyan-400" />
                Schedule Follow-up Task
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Task Title *</label>
                <input
                  type="text"
                  required
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  placeholder="e.g. Call regarding quotation revision"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Customer *</label>
                  <select
                    required
                    value={createForm.customer_id}
                    onChange={(e) => setCreateForm({ ...createForm, customer_id: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="">Select Customer</option>
                    {(customers || []).map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Associated Project</label>
                  <select
                    value={createForm.project_id || ''}
                    onChange={(e) => setCreateForm({ ...createForm, project_id: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="">None (Customer General)</option>
                    {(projects || [])
                      .filter((p) => !createForm.customer_id || p.customer_id === createForm.customer_id)
                      .map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.project_number})
                        </option>
                      ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Due Date & Time *</label>
                  <input
                    type="datetime-local"
                    required
                    value={createForm.due_date}
                    onChange={(e) => setCreateForm({ ...createForm, due_date: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Priority</label>
                  <select
                    value={createForm.priority}
                    onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Description / Talking Points</label>
                <textarea
                  rows={3}
                  value={createForm.description || ''}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  placeholder="Detail items to discuss during call or visit..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <Button variant="secondary" onClick={() => setShowCreateModal(false)} type="button">
                  Cancel
                </Button>
                <Button variant="primary" type="submit" isLoading={isSubmitting}>
                  Schedule
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
