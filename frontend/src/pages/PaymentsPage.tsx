import React, { useState, useEffect, useCallback } from 'react';
import {
  Receipt,
  Plus,
  TrendingUp,
  CreditCard,
  Building,
  Calendar,
  X,
  Loader2,
  FileCheck,
} from 'lucide-react';
import { paymentService } from '../services/paymentService';
import { projectService } from '../services/projectService';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { useNotifications } from '../context/NotificationContext';
import type { Payment, PaymentCreate, PaymentSummary, Project } from '../types';

export const PaymentsPage: React.FC = () => {
  const { addNotification } = useNotifications();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  // Financial summary
  const [summary, setSummary] = useState<PaymentSummary>({
    total_project_value: '0.00',
    total_paid: '0.00',
    total_outstanding: '0.00',
    payment_count: 0,
  });

  // Projects reference for modal
  const [projects, setProjects] = useState<Project[]>([]);

  // Create Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<PaymentCreate>({
    project_id: '',
    amount: 100000,
    currency: 'INR',
    payment_date: new Date().toISOString().split('T')[0],
    payment_method: 'bank_transfer',
    reference_number: '',
    notes: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const res = await projectService.getProjects({ pageSize: 100 });
        setProjects(res.items);
        if (res.items[0]) {
          setCreateForm((prev) => ({ ...prev, project_id: res.items[0].id }));
        }
      } catch (err) {
        console.error('Failed to load projects', err);
      }
    };
    loadProjects();
  }, []);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [payRes, sumRes] = await Promise.all([
        paymentService.getPayments({ pageSize: 50 }),
        paymentService.getSummary(),
      ]);
      setPayments(payRes.items);
      setTotalCount(payRes.total);
      setSummary(sumRes);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to load payments',
      });
    } finally {
      setIsLoading(false);
    }
  }, [addNotification]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreatePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.project_id || !createForm.amount) {
      addNotification({ type: 'warning', message: 'Project and Amount are required.' });
      return;
    }

    setIsSubmitting(true);
    try {
      const p = await paymentService.createPayment({
        ...createForm,
        amount: Number(createForm.amount),
      });
      addNotification({
        type: 'success',
        message: `Payment receipt ${p.payment_number} (₹${Number(p.amount).toLocaleString('en-IN')}) recorded.`,
      });
      setShowCreateModal(false);
      loadData();
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to record payment',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Receipt className="w-5 h-5 text-cyan-400" />
            Financial & Payment Tracking
          </h2>
          <p className="text-sm text-slate-400">
            {totalCount} verified payments recorded. Real-time collected revenue and project receivables.
          </p>
        </div>

        <Button
          variant="primary"
          icon={<Plus className="w-4 h-4" />}
          onClick={() => setShowCreateModal(true)}
        >
          Record Payment
        </Button>
      </div>

      {/* Financial Balance Summary Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-5 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Total Contracted Value
            </span>
            <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-100">
            ₹{Number(summary.total_project_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-xs text-slate-500 mt-1">Across all operational projects</p>
        </Card>

        <Card className="p-5 bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950/20 border-emerald-900/40">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
              Total Revenue Collected
            </span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <FileCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            ₹{Number(summary.total_paid).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-xs text-slate-500 mt-1">{summary.payment_count} verified receipts</p>
        </Card>

        <Card className="p-5 bg-gradient-to-br from-slate-900 via-slate-900 to-amber-950/20 border-amber-900/40">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
              Total Outstanding Receivables
            </span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <CreditCard className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-amber-400">
            ₹{Number(summary.total_outstanding).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-xs text-slate-500 mt-1">Pending milestone collections</p>
        </Card>
      </div>

      {/* Payment Receipts Table */}
      <Card>
        {isLoading ? (
          <div className="flex items-center justify-center p-12 text-slate-400 gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-cyan-500" />
            <span>Loading payments...</span>
          </div>
        ) : payments.length === 0 ? (
          <EmptyState
            title="No payment receipts"
            description="Record payments received from clients to update your accounts and project balance."
            actionLabel="Record Payment"
            onAction={() => setShowCreateModal(true)}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  <th className="py-3 px-4">Receipt Number</th>
                  <th className="py-3 px-4">Customer & Project</th>
                  <th className="py-3 px-4">Amount Received</th>
                  <th className="py-3 px-4">Payment Method & Date</th>
                  <th className="py-3 px-4">Reference / UTR</th>
                  <th className="py-3 px-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-sm">
                {payments.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono text-xs text-cyan-400 font-semibold">
                      {p.payment_number}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-slate-200">{p.customer_name || 'Customer'}</div>
                      <div className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                        <Building className="w-3 h-3 text-slate-500" />
                        <span>{p.project_name} ({p.project_number})</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-emerald-400">
                      ₹{Number(p.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      <div className="capitalize">{p.payment_method.replace('_', ' ')}</div>
                      <div className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                        <Calendar className="w-3 h-3" />
                        <span>{p.payment_date}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-400">
                      {p.reference_number || '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Badge variant="success" size="sm">
                        {p.status.toUpperCase()}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* RECORD PAYMENT MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg shadow-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Receipt className="w-5 h-5 text-cyan-400" />
                Record Customer Payment
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePayment} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Target Project *</label>
                <select
                  required
                  value={createForm.project_id}
                  onChange={(e) => setCreateForm({ ...createForm, project_id: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="">Select Project</option>
                  {projects.map((pr) => (
                    <option key={pr.id} value={pr.id}>
                      {pr.name} ({pr.project_number}) — {pr.customer_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Amount (INR) *</label>
                  <input
                    type="number"
                    required
                    value={createForm.amount}
                    onChange={(e) => setCreateForm({ ...createForm, amount: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Payment Date *</label>
                  <input
                    type="date"
                    required
                    value={createForm.payment_date}
                    onChange={(e) => setCreateForm({ ...createForm, payment_date: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Payment Method</label>
                  <select
                    value={createForm.payment_method}
                    onChange={(e) => setCreateForm({ ...createForm, payment_method: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="bank_transfer">Bank Transfer (NEFT/RTGS)</option>
                    <option value="cheque">Cheque</option>
                    <option value="upi">UPI</option>
                    <option value="cash">Cash</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Transaction Ref / UTR</label>
                  <input
                    type="text"
                    value={createForm.reference_number || ''}
                    onChange={(e) => setCreateForm({ ...createForm, reference_number: e.target.value })}
                    placeholder="e.g. UTR12345678"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Receipt Notes</label>
                <textarea
                  rows={2}
                  value={createForm.notes || ''}
                  onChange={(e) => setCreateForm({ ...createForm, notes: e.target.value })}
                  placeholder="e.g. 20% advance milestone paid against initial design approval"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <Button variant="secondary" onClick={() => setShowCreateModal(false)} type="button">
                  Cancel
                </Button>
                <Button variant="primary" type="submit" isLoading={isSubmitting}>
                  Record Receipt
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
