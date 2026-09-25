import React, { useState, useEffect, useCallback } from 'react';
import {
  Users,
  Plus,
  Search,
  Phone,
  Mail,
  MapPin,
  Building,
  UserCheck,
  FolderGit2,
  Receipt,
  Clock,
  FileText,
  MessageSquare,
  History,
  X,
  Loader2,
  Trash2,
  CheckCircle,
} from 'lucide-react';
import { customerService } from '../services/customerService';
import { noteService, documentService } from '../services/dashboardService';
import { followUpService } from '../services/followUpService';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { useNotifications } from '../context/NotificationContext';
import type { Customer, CustomerCreate, Contact } from '../types';

export const CustomersPage: React.FC = () => {
  const { addNotification } = useNotifications();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Selected customer for 360 view
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [activeTab, setActiveTab] = useState<'contacts' | 'projects' | 'payments' | 'followups' | 'notes' | 'documents' | 'activity'>('contacts');
  const [is360Loading, setIs360Loading] = useState(false);

  // New Customer Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<CustomerCreate>({
    name: '',
    customer_type: 'business',
    email: '',
    phone: '',
    city: '',
    state: '',
    status: 'lead',
    source: 'Website Enquiry',
    primary_contact_name: '',
    primary_contact_phone: '',
    primary_contact_designation: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Add Contact Modal
  const [showAddContactModal, setShowAddContactModal] = useState(false);
  const [contactForm, setContactForm] = useState({
    name: '',
    designation: '',
    email: '',
    phone: '',
    is_primary: false,
  });

  // Add Note State
  const [newNoteContent, setNewNoteContent] = useState('');
  const [isSavingNote, setIsSavingNote] = useState(false);

  // Add Document State
  const [showDocModal, setShowDocModal] = useState(false);
  const [docForm, setDocForm] = useState({
    file_name: '',
    file_type: 'application/pdf',
    file_size_bytes: 102400,
    document_category: 'quotation',
    storage_url: '',
  });

  const loadCustomers = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await customerService.getCustomers({
        search: searchQuery.trim() || undefined,
        status: statusFilter || undefined,
        pageSize: 50,
      });
      setCustomers(res.items);
      setTotalCount(res.total);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to load customers',
      });
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, statusFilter, addNotification]);

  useEffect(() => {
    loadCustomers();
  }, [loadCustomers]);

  const loadCustomer360 = async (id: string) => {
    setSelectedCustomerId(id);
    setIs360Loading(true);
    try {
      const data = await customerService.getCustomer(id);
      setSelectedCustomer(data);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to load customer details',
      });
    } finally {
      setIs360Loading(false);
    }
  };

  const handleCreateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.name.trim()) return;

    setIsSubmitting(true);
    try {
      const newCust = await customerService.createCustomer(createForm);
      addNotification({
        type: 'success',
        message: `Customer "${newCust.name}" created successfully.`,
      });
      setShowCreateModal(false);
      setCreateForm({
        name: '',
        customer_type: 'business',
        email: '',
        phone: '',
        city: '',
        state: '',
        status: 'lead',
        source: 'Website Enquiry',
        primary_contact_name: '',
        primary_contact_phone: '',
        primary_contact_designation: '',
      });
      loadCustomers();
      loadCustomer360(newCust.id);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to create customer',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddContact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomerId || !contactForm.name.trim()) return;

    try {
      await customerService.createContact(selectedCustomerId, contactForm);
      addNotification({
        type: 'success',
        message: `Contact "${contactForm.name}" added successfully.`,
      });
      setShowAddContactModal(false);
      setContactForm({ name: '', designation: '', email: '', phone: '', is_primary: false });
      loadCustomer360(selectedCustomerId);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to add contact',
      });
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomerId || !newNoteContent.trim()) return;

    setIsSavingNote(true);
    try {
      await noteService.createNote({
        customer_id: selectedCustomerId,
        content: newNoteContent.trim(),
      });
      setNewNoteContent('');
      addNotification({ type: 'success', message: 'Note saved.' });
      loadCustomer360(selectedCustomerId);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to save note',
      });
    } finally {
      setIsSavingNote(false);
    }
  };

  const handleAddDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomerId || !docForm.file_name.trim()) return;

    try {
      await documentService.createDocument({
        customer_id: selectedCustomerId,
        ...docForm,
      });
      setShowDocModal(false);
      setDocForm({
        file_name: '',
        file_type: 'application/pdf',
        file_size_bytes: 102400,
        document_category: 'quotation',
        storage_url: '',
      });
      addNotification({ type: 'success', message: 'Document metadata recorded.' });
      loadCustomer360(selectedCustomerId);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to record document',
      });
    }
  };

  const handleDeleteCustomer = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete customer "${name}"? This will delete all associated records.`)) {
      return;
    }
    try {
      await customerService.deleteCustomer(id);
      addNotification({ type: 'success', message: `Customer "${name}" removed.` });
      if (selectedCustomerId === id) {
        setSelectedCustomerId(null);
        setSelectedCustomer(null);
      }
      loadCustomers();
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to delete customer',
      });
    }
  };

  const handleCompleteFollowUp = async (id: string) => {
    try {
      await followUpService.completeFollowUp(id);
      addNotification({ type: 'success', message: 'Follow-up marked as completed.' });
      if (selectedCustomerId) {
        loadCustomer360(selectedCustomerId);
      }
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to complete follow-up',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-cyan-400" />
            Customers & Accounts
          </h2>
          <p className="text-sm text-slate-400">
            Total of {totalCount} registered accounts in organization.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            icon={<Plus className="w-4 h-4" />}
            onClick={() => setShowCreateModal(true)}
          >
            New Customer
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by company name, contact, phone, or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Statuses</option>
            <option value="lead">Lead</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Customers Table */}
      <Card>
        {isLoading ? (
          <div className="flex items-center justify-center p-12 text-slate-400 gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-cyan-500" />
            <span>Loading customers...</span>
          </div>
        ) : customers.length === 0 ? (
          <EmptyState
            title="No customers found"
            description="Create your first customer account or adjust your search filter."
            actionLabel="Add Customer"
            onAction={() => setShowCreateModal(true)}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  <th className="py-3 px-4">Customer Name</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Primary Contact</th>
                  <th className="py-3 px-4">Location</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-sm">
                {customers.map((c) => (
                  <tr
                    key={c.id}
                    onClick={() => loadCustomer360(c.id)}
                    className={`cursor-pointer transition-colors ${
                      selectedCustomerId === c.id ? 'bg-cyan-950/20' : 'hover:bg-slate-900/60'
                    }`}
                  >
                    <td className="py-3.5 px-4 font-medium text-slate-200">
                      <div className="flex items-center gap-2">
                        <Building className="w-4 h-4 text-slate-500 shrink-0" />
                        <div>
                          <div>{c.name}</div>
                          {c.email && <div className="text-xs text-slate-500">{c.email}</div>}
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 capitalize">
                      {c.customer_type}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      <div>{c.primary_contact_name || '—'}</div>
                      {c.primary_contact_phone && (
                        <div className="text-xs text-slate-500">{c.primary_contact_phone}</div>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">
                      {c.city ? `${c.city}${c.state ? `, ${c.state}` : ''}` : '—'}
                    </td>
                    <td className="py-3.5 px-4">
                      <Badge
                        variant={c.status === 'active' ? 'success' : c.status === 'lead' ? 'warning' : 'neutral'}
                        size="sm"
                      >
                        {c.status.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => loadCustomer360(c.id)}
                          className="px-2.5 py-1 text-xs font-medium rounded bg-cyan-600/15 text-cyan-400 hover:bg-cyan-600/30 transition-colors"
                        >
                          View 360
                        </button>
                        <button
                          onClick={() => handleDeleteCustomer(c.id, c.name)}
                          className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                          title="Delete customer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Customer 360 Drawer */}
      {selectedCustomerId && (
        <div className="fixed inset-y-0 right-0 w-full sm:w-[680px] bg-slate-950 border-l border-slate-800 z-40 shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-right duration-200">
          {/* 360 Drawer Header */}
          <div className="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-900/60">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">
                  Customer 360
                </span>
                <Badge
                  variant={selectedCustomer?.status === 'active' ? 'success' : 'warning'}
                  size="sm"
                >
                  {selectedCustomer?.status.toUpperCase() || 'LEAD'}
                </Badge>
              </div>
              <h3 className="text-xl font-bold text-slate-100">{selectedCustomer?.name}</h3>
              <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-slate-400">
                {selectedCustomer?.phone && (
                  <span className="flex items-center gap-1">
                    <Phone className="w-3.5 h-3.5 text-slate-500" />
                    {selectedCustomer.phone}
                  </span>
                )}
                {selectedCustomer?.email && (
                  <span className="flex items-center gap-1">
                    <Mail className="w-3.5 h-3.5 text-slate-500" />
                    {selectedCustomer.email}
                  </span>
                )}
                {selectedCustomer?.city && (
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-500" />
                    {selectedCustomer.city}, {selectedCustomer.state}
                  </span>
                )}
              </div>
            </div>

            <button
              onClick={() => {
                setSelectedCustomerId(null);
                setSelectedCustomer(null);
              }}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* 360 Navigation Tabs */}
          <div className="flex items-center gap-1 px-6 border-b border-slate-800 bg-slate-900/30 overflow-x-auto">
            {[
              { id: 'contacts', label: 'Contacts', icon: <UserCheck className="w-4 h-4" /> },
              { id: 'projects', label: 'Projects', icon: <FolderGit2 className="w-4 h-4" /> },
              { id: 'payments', label: 'Payments', icon: <Receipt className="w-4 h-4" /> },
              { id: 'followups', label: 'Follow-ups', icon: <Clock className="w-4 h-4" /> },
              { id: 'notes', label: 'Notes', icon: <MessageSquare className="w-4 h-4" /> },
              { id: 'documents', label: 'Documents', icon: <FileText className="w-4 h-4" /> },
              { id: 'activity', label: 'Activity', icon: <History className="w-4 h-4" /> },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex items-center gap-1.5 py-3 px-3 border-b-2 text-xs font-medium whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? 'border-cyan-400 text-cyan-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          {/* 360 Content Body */}
          <div className="flex-1 p-6 overflow-y-auto space-y-4">
            {is360Loading ? (
              <div className="flex items-center justify-center p-12 text-slate-400 gap-2">
                <Loader2 className="w-5 h-5 animate-spin text-cyan-500" />
                <span>Loading 360 data...</span>
              </div>
            ) : !selectedCustomer ? null : (
              <>
                {/* CONTACTS TAB */}
                {activeTab === 'contacts' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-slate-200">Authorized Contacts</h4>
                      <Button
                        size="sm"
                        variant="secondary"
                        icon={<Plus className="w-3.5 h-3.5" />}
                        onClick={() => setShowAddContactModal(true)}
                      >
                        Add Contact
                      </Button>
                    </div>

                    {(!selectedCustomer.contacts || selectedCustomer.contacts.length === 0) ? (
                      <EmptyState
                        title="No contacts listed"
                        description="Add people working at this organization for easy reference."
                      />
                    ) : (
                      <div className="grid gap-3">
                        {selectedCustomer.contacts.map((ct: Contact) => (
                          <div
                            key={ct.id}
                            className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between"
                          >
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-slate-200 text-sm">{ct.name}</span>
                                {ct.is_primary && (
                                  <Badge variant="info" size="sm">Primary</Badge>
                                )}
                              </div>
                              <p className="text-xs text-slate-400">{ct.designation || 'Staff'}</p>
                              <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                                {ct.phone && <span>Phone: {ct.phone}</span>}
                                {ct.email && <span>Email: {ct.email}</span>}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* PROJECTS TAB */}
                {activeTab === 'projects' && (
                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold text-slate-200">Customer Projects</h4>
                    {(!selectedCustomer.projects || selectedCustomer.projects.length === 0) ? (
                      <EmptyState
                        title="No active projects"
                        description="Create a project to initiate the pipeline workflow."
                      />
                    ) : (
                      <div className="grid gap-3">
                        {selectedCustomer.projects.map((p) => (
                          <div
                            key={p.id}
                            className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-2"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-mono text-xs text-cyan-400 font-semibold">
                                {p.project_number}
                              </span>
                              <Badge
                                variant={p.status === 'completed' ? 'success' : 'info'}
                                size="sm"
                              >
                                {p.stage_name || p.status}
                              </Badge>
                            </div>
                            <h5 className="font-semibold text-slate-100 text-sm">{p.name}</h5>
                            <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                              <span>Value: <strong className="text-slate-200">₹{Number(p.value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></span>
                              <span>Pipeline: {p.pipeline_name || 'Standard'}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* PAYMENTS TAB */}
                {activeTab === 'payments' && (
                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold text-slate-200">Recorded Payments</h4>
                    {(!selectedCustomer.payments || selectedCustomer.payments.length === 0) ? (
                      <EmptyState
                        title="No payment records"
                        description="Payments recorded against this customer's projects will appear here."
                      />
                    ) : (
                      <div className="grid gap-3">
                        {selectedCustomer.payments.map((pm) => (
                          <div
                            key={pm.id}
                            className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between"
                          >
                            <div>
                              <div className="font-mono text-xs text-slate-400">{pm.payment_number}</div>
                              <div className="font-bold text-slate-200 text-sm">
                                ₹{Number(pm.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                              </div>
                              <div className="text-xs text-slate-500 mt-0.5">
                                {pm.payment_date} • {pm.payment_method.toUpperCase()}
                                {pm.reference_number ? ` • Ref: ${pm.reference_number}` : ''}
                              </div>
                            </div>
                            <Badge variant="success" size="sm">
                              {pm.status.toUpperCase()}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* FOLLOWUPS TAB */}
                {activeTab === 'followups' && (
                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold text-slate-200">Follow-up Tasks</h4>
                    {(!selectedCustomer.follow_ups || selectedCustomer.follow_ups.length === 0) ? (
                      <EmptyState
                        title="No follow-ups scheduled"
                        description="Stay proactive by scheduling client calls and site visits."
                      />
                    ) : (
                      <div className="grid gap-3">
                        {selectedCustomer.follow_ups.map((f) => (
                          <div
                            key={f.id}
                            className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 flex items-start justify-between"
                          >
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-slate-200 text-sm">{f.title}</span>
                                <Badge
                                  variant={f.priority === 'urgent' ? 'error' : f.priority === 'high' ? 'warning' : 'neutral'}
                                  size="sm"
                                >
                                  {f.priority}
                                </Badge>
                              </div>
                              {f.description && (
                                <p className="text-xs text-slate-400">{f.description}</p>
                              )}
                              <div className="text-xs text-slate-500">
                                Due: {new Date(f.due_date).toLocaleString()}
                              </div>
                            </div>

                            {f.status === 'pending' ? (
                              <button
                                onClick={() => handleCompleteFollowUp(f.id)}
                                className="flex items-center gap-1 px-2.5 py-1 text-xs rounded bg-emerald-600/15 text-emerald-400 hover:bg-emerald-600/30"
                              >
                                <CheckCircle className="w-3.5 h-3.5" />
                                Mark Done
                              </button>
                            ) : (
                              <Badge variant="neutral" size="sm">Completed</Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* NOTES TAB */}
                {activeTab === 'notes' && (
                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold text-slate-200">Operator Notes</h4>
                    <form onSubmit={handleAddNote} className="space-y-2">
                      <textarea
                        value={newNoteContent}
                        onChange={(e) => setNewNoteContent(e.target.value)}
                        placeholder="Write a timestamped note regarding this account..."
                        rows={3}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                      />
                      <div className="flex justify-end">
                        <Button
                          size="sm"
                          variant="primary"
                          type="submit"
                          isLoading={isSavingNote}
                          disabled={!newNoteContent.trim()}
                        >
                          Save Note
                        </Button>
                      </div>
                    </form>

                    <div className="space-y-3 pt-2">
                      {(!selectedCustomer.notes_list || selectedCustomer.notes_list.length === 0) ? (
                        <p className="text-xs text-slate-500 italic">No notes recorded yet.</p>
                      ) : (
                        selectedCustomer.notes_list.map((n) => (
                          <div
                            key={n.id}
                            className="p-3 rounded-lg bg-slate-900 border border-slate-800/80 space-y-1.5"
                          >
                            <div className="flex items-center justify-between text-xs text-slate-500">
                              <span className="font-semibold text-slate-400">{n.author_name || 'Operator'}</span>
                              <span>{new Date(n.created_at).toLocaleString()}</span>
                            </div>
                            <p className="text-sm text-slate-300 whitespace-pre-wrap">{n.content}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}

                {/* DOCUMENTS TAB */}
                {activeTab === 'documents' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-slate-200">Attached Documents</h4>
                      <Button
                        size="sm"
                        variant="secondary"
                        icon={<Plus className="w-3.5 h-3.5" />}
                        onClick={() => setShowDocModal(true)}
                      >
                        Attach Metadata
                      </Button>
                    </div>

                    {(!selectedCustomer.documents || selectedCustomer.documents.length === 0) ? (
                      <EmptyState
                        title="No documents recorded"
                        description="Record quotation, agreement, or site inspection document metadata."
                      />
                    ) : (
                      <div className="grid gap-2.5">
                        {selectedCustomer.documents.map((d) => (
                          <div
                            key={d.id}
                            className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between"
                          >
                            <div className="flex items-center gap-3">
                              <FileText className="w-4 h-4 text-cyan-400 shrink-0" />
                              <div>
                                <p className="text-sm font-medium text-slate-200">{d.file_name}</p>
                                <p className="text-xs text-slate-500">
                                  {d.document_category.toUpperCase()} • {(d.file_size_bytes / 1024).toFixed(1)} KB
                                </p>
                              </div>
                            </div>
                            <span className="text-xs text-slate-500 font-mono">
                              {new Date(d.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* ACTIVITY TAB */}
                {activeTab === 'activity' && (
                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold text-slate-200">Timeline</h4>
                    {(!selectedCustomer.activities || selectedCustomer.activities.length === 0) ? (
                      <p className="text-xs text-slate-500 italic">No domain activity yet.</p>
                    ) : (
                      <div className="relative pl-6 space-y-4 before:content-[''] before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                        {selectedCustomer.activities.map((a) => (
                          <div key={a.id} className="relative">
                            <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 absolute -left-[21px] top-1 ring-4 ring-slate-950" />
                            <div className="text-xs text-slate-500">
                              {new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {new Date(a.created_at).toLocaleDateString()}
                            </div>
                            <p className="text-sm font-semibold text-slate-200">{a.title}</p>
                            {a.description && <p className="text-xs text-slate-400 mt-0.5">{a.description}</p>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* CREATE CUSTOMER MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg shadow-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Building className="w-5 h-5 text-cyan-400" />
                Register New Customer
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateCustomer} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Company / Customer Name *</label>
                <input
                  type="text"
                  required
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  placeholder="e.g. ABC Solar Industrial Park"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Customer Type</label>
                  <select
                    value={createForm.customer_type}
                    onChange={(e) => setCreateForm({ ...createForm, customer_type: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="business">Business</option>
                    <option value="commercial">Commercial</option>
                    <option value="individual">Individual</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Status</label>
                  <select
                    value={createForm.status}
                    onChange={(e) => setCreateForm({ ...createForm, status: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="lead">Lead</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Phone Number</label>
                  <input
                    type="text"
                    value={createForm.phone || ''}
                    onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
                    placeholder="+91 98765 43210"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Email Address</label>
                  <input
                    type="email"
                    value={createForm.email || ''}
                    onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                    placeholder="contact@company.com"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">City</label>
                  <input
                    type="text"
                    value={createForm.city || ''}
                    onChange={(e) => setCreateForm({ ...createForm, city: e.target.value })}
                    placeholder="Mumbai"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">State</label>
                  <input
                    type="text"
                    value={createForm.state || ''}
                    onChange={(e) => setCreateForm({ ...createForm, state: e.target.value })}
                    placeholder="Maharashtra"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              {/* Primary Contact Person Fields */}
              <div className="pt-3 border-t border-slate-800/80">
                <h4 className="text-xs font-semibold text-cyan-400 mb-2">Primary Contact Person</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Contact Name</label>
                    <input
                      type="text"
                      value={createForm.primary_contact_name || ''}
                      onChange={(e) => setCreateForm({ ...createForm, primary_contact_name: e.target.value })}
                      placeholder="e.g. Rajesh Sharma"
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Designation</label>
                    <input
                      type="text"
                      value={createForm.primary_contact_designation || ''}
                      onChange={(e) => setCreateForm({ ...createForm, primary_contact_designation: e.target.value })}
                      placeholder="Plant Director"
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <Button variant="secondary" onClick={() => setShowCreateModal(false)} type="button">
                  Cancel
                </Button>
                <Button variant="primary" type="submit" isLoading={isSubmitting}>
                  Create Customer
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ADD CONTACT MODAL */}
      {showAddContactModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-lg font-bold text-slate-100">Add New Contact</h3>
              <button onClick={() => setShowAddContactModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAddContact} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  value={contactForm.name}
                  onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                  placeholder="e.g. Amit Patel"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Designation</label>
                <input
                  type="text"
                  value={contactForm.designation}
                  onChange={(e) => setContactForm({ ...contactForm, designation: e.target.value })}
                  placeholder="e.g. Procurement Lead"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Phone</label>
                  <input
                    type="text"
                    value={contactForm.phone}
                    onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })}
                    placeholder="+91 9988776655"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Email</label>
                  <input
                    type="email"
                    value={contactForm.email}
                    onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                    placeholder="amit@company.com"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="primaryContactCheck"
                  checked={contactForm.is_primary}
                  onChange={(e) => setContactForm({ ...contactForm, is_primary: e.target.checked })}
                  className="rounded border-slate-800 text-cyan-500 focus:ring-0"
                />
                <label htmlFor="primaryContactCheck" className="text-xs text-slate-300">Set as primary contact</label>
              </div>
              <div className="flex justify-end gap-3 pt-3">
                <Button variant="secondary" onClick={() => setShowAddContactModal(false)} type="button">
                  Cancel
                </Button>
                <Button variant="primary" type="submit">
                  Save Contact
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ATTACH DOC MODAL */}
      {showDocModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-lg font-bold text-slate-100">Attach Document Metadata</h3>
              <button onClick={() => setShowDocModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAddDocument} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Document Title / File Name *</label>
                <input
                  type="text"
                  required
                  value={docForm.file_name}
                  onChange={(e) => setDocForm({ ...docForm, file_name: e.target.value })}
                  placeholder="e.g. Quotation_Revision_2.pdf"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Category</label>
                  <select
                    value={docForm.document_category}
                    onChange={(e) => setDocForm({ ...docForm, document_category: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="quotation">Quotation</option>
                    <option value="invoice">Invoice</option>
                    <option value="agreement">Agreement</option>
                    <option value="site_inspection">Site Inspection</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Size (Bytes)</label>
                  <input
                    type="number"
                    value={docForm.file_size_bytes}
                    onChange={(e) => setDocForm({ ...docForm, file_size_bytes: Number(e.target.value) })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Storage URL (optional)</label>
                <input
                  type="text"
                  value={docForm.storage_url}
                  onChange={(e) => setDocForm({ ...docForm, storage_url: e.target.value })}
                  placeholder="s3://enermax-docs/..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>
              <div className="flex justify-end gap-3 pt-3">
                <Button variant="secondary" onClick={() => setShowDocModal(false)} type="button">
                  Cancel
                </Button>
                <Button variant="primary" type="submit">
                  Attach
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
