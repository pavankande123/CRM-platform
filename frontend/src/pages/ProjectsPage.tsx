import React, { useState, useEffect, useCallback } from 'react';
import {
  FolderGit2,
  Plus,
  Search,
  ArrowRight,
  TrendingUp,
  Receipt,
  Building,
  X,
  Loader2,
} from 'lucide-react';
import { projectService, pipelineService } from '../services/projectService';
import { customerService } from '../services/customerService';
import { productService } from '../services/productService';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { useNotifications } from '../context/NotificationContext';
import type {
  Project,
  ProjectDetail,
  ProjectCreate,
  Pipeline,
  Customer,
  Product,
} from '../types';

export const ProjectsPage: React.FC = () => {
  const { addNotification } = useNotifications();
  const [projects, setProjects] = useState<Project[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStageId, setSelectedStageId] = useState('');

  // Dropdown reference data
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  // Project Detail Drawer
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [projectDetail, setProjectDetail] = useState<ProjectDetail | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  // Advance Stage Modal
  const [stageModalProject, setStageModalProject] = useState<Project | null>(null);
  const [targetStageId, setTargetStageId] = useState('');
  const [stageNotes, setStageNotes] = useState('');
  const [isAdvancing, setIsAdvancing] = useState(false);

  // Create Project Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<ProjectCreate>({
    name: '',
    customer_id: '',
    product_id: '',
    pipeline_id: '',
    stage_id: '',
    value: 500000,
    currency: 'INR',
    priority: 'medium',
    expected_completion_date: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load Reference Data (Pipelines, Customers, Products)
  useEffect(() => {
    const fetchRefs = async () => {
      try {
        const [pipes, custs, prods] = await Promise.all([
          pipelineService.getPipelines(),
          customerService.getCustomers({ pageSize: 100 }),
          productService.getProducts({ is_active: true }),
        ]);
        setPipelines(pipes || []);
        setCustomers(custs?.items || []);
        setProducts(prods || []);

        // Pre-select default pipeline if available
        const defPipe = (pipes || []).find((p) => p.is_default) || (pipes || [])[0];
        if (defPipe) {
          setCreateForm((prev) => ({
            ...prev,
            pipeline_id: defPipe.id,
            stage_id: defPipe.stages?.[0]?.id || '',
          }));
        }
      } catch (err) {
        console.error('Failed to load reference data', err);
      }
    };
    fetchRefs();
  }, []);

  const loadProjects = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await projectService.getProjects({
        search: searchQuery.trim() || undefined,
        stage_id: selectedStageId || undefined,
        pageSize: 50,
      });
      setProjects(res?.items || []);
      setTotalCount(res?.total || 0);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to load projects',
      });
      setProjects([]);
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, selectedStageId, addNotification]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const loadProjectDetail = async (id: string) => {
    setSelectedProjectId(id);
    setIsDetailLoading(true);
    try {
      const detail = await projectService.getProject(id);
      setProjectDetail(detail);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to load project detail',
      });
    } finally {
      setIsDetailLoading(false);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.name.trim() || !createForm.customer_id) {
      addNotification({ type: 'warning', message: 'Please provide project name and customer.' });
      return;
    }

    setIsSubmitting(true);
    try {
      const payload: ProjectCreate = {
        name: createForm.name.trim(),
        customer_id: createForm.customer_id,
        value: Number(createForm.value) || 0,
        currency: createForm.currency || 'INR',
        priority: createForm.priority || 'medium',
        product_id: createForm.product_id?.trim() || undefined,
        pipeline_id: createForm.pipeline_id?.trim() || undefined,
        stage_id: createForm.stage_id?.trim() || undefined,
        expected_completion_date: createForm.expected_completion_date?.trim() || undefined,
      };
      const newProj = await projectService.createProject(payload);
      addNotification({
        type: 'success',
        message: `Project ${newProj.project_number} (${newProj.name}) created.`,
      });
      setShowCreateModal(false);
      loadProjects();
      loadProjectDetail(newProj.id);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to create project',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const openAdvanceModal = (p: Project, e: React.MouseEvent) => {
    e.stopPropagation();
    setStageModalProject(p);
    // Find next stage in project's pipeline if possible
    const currentPipe = pipelines.find((pipe) => pipe.id === p.pipeline_id);
    if (currentPipe && currentPipe.stages) {
      const currentIndex = currentPipe.stages.findIndex((s) => s.id === p.stage_id);
      const nextStage = currentPipe.stages[currentIndex + 1];
      setTargetStageId(nextStage?.id || currentPipe.stages[0]?.id || '');
    }
    setStageNotes('');
  };

  const handleAdvanceStage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stageModalProject || !targetStageId) return;

    setIsAdvancing(true);
    try {
      await projectService.changeStage(stageModalProject.id, targetStageId, stageNotes.trim());
      addNotification({
        type: 'success',
        message: `Stage updated for ${stageModalProject.project_number}.`,
      });
      setStageModalProject(null);
      loadProjects();
      if (selectedProjectId === stageModalProject.id) {
        loadProjectDetail(stageModalProject.id);
      }
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to change stage',
      });
    } finally {
      setIsAdvancing(false);
    }
  };

  // Pipeline stages for the filter
  const activePipeline = pipelines[0];

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <FolderGit2 className="w-5 h-5 text-cyan-400" />
            Projects & Pipeline
          </h2>
          <p className="text-sm text-slate-400">
            {totalCount} total operational projects tracked.
          </p>
        </div>

        <Button
          variant="primary"
          icon={<Plus className="w-4 h-4" />}
          onClick={() => setShowCreateModal(true)}
        >
          New Project
        </Button>
      </div>

      {/* Visual Pipeline Stage Badges */}
      {activePipeline && activePipeline.stages && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Active Pipeline: {activePipeline.name}
            </span>
            <span className="text-xs text-slate-500">{activePipeline.stages?.length || 0} Stages</span>
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            <button
              onClick={() => setSelectedStageId('')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                selectedStageId === ''
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                  : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              All Stages
            </button>
            {(activePipeline.stages || []).map((stg) => {
              const active = selectedStageId === stg.id;
              return (
                <button
                  key={stg.id}
                  onClick={() => setSelectedStageId(stg.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors flex items-center gap-1.5 ${
                    active
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                      : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: stg.color || '#06b6d4' }}
                  />
                  <span>{stg.name}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search by project name, project number (e.g. ENX-PRJ-), or customer..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
        />
      </div>

      {/* Project Table */}
      <Card>
        {isLoading ? (
          <div className="flex items-center justify-center p-12 text-slate-400 gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-cyan-500" />
            <span>Loading projects...</span>
          </div>
        ) : (!projects || projects.length === 0) ? (
          <EmptyState
            title="No projects found"
            description="Create a new project or select a different pipeline stage filter."
            actionLabel="Create Project"
            onAction={() => setShowCreateModal(true)}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  <th className="py-3 px-4">Project ID</th>
                  <th className="py-3 px-4">Project Name & Customer</th>
                  <th className="py-3 px-4">Current Stage</th>
                  <th className="py-3 px-4">Project Value</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-sm">
                {(projects || []).map((p) => (
                  <tr
                    key={p.id}
                    onClick={() => loadProjectDetail(p.id)}
                    className={`cursor-pointer transition-colors ${
                      selectedProjectId === p.id ? 'bg-cyan-950/20' : 'hover:bg-slate-900/60'
                    }`}
                  >
                    <td className="py-3.5 px-4 font-mono text-xs text-cyan-400 font-semibold">
                      {p.project_number}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-200">
                      <div>{p.name}</div>
                      <div className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                        <Building className="w-3.5 h-3.5 text-slate-500" />
                        <span>{p.customer_name || 'Customer'}</span>
                        {p.product_name && (
                          <span className="text-slate-500">• {p.product_name}</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border"
                        style={{
                          borderColor: `${p.stage_color || '#06b6d4'}40`,
                          backgroundColor: `${p.stage_color || '#06b6d4'}15`,
                          color: p.stage_color || '#06b6d4',
                        }}
                      >
                        <span
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ backgroundColor: p.stage_color || '#06b6d4' }}
                        />
                        {p.stage_name || 'Initial'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-200">
                      ₹{Number(p.value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3.5 px-4">
                      <Badge
                        variant={p.priority === 'urgent' ? 'error' : p.priority === 'high' ? 'warning' : 'neutral'}
                        size="sm"
                      >
                        {p.priority.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={(e) => openAdvanceModal(p, e)}
                          className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded bg-cyan-600/15 text-cyan-400 hover:bg-cyan-600/30 transition-colors"
                        >
                          <span>Move Stage</span>
                          <ArrowRight className="w-3.5 h-3.5" />
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

      {/* PROJECT DETAIL DRAWER */}
      {selectedProjectId && (
        <div className="fixed inset-y-0 right-0 w-full sm:w-[680px] bg-slate-950 border-l border-slate-800 z-40 shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-right duration-200">
          {/* Header */}
          <div className="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-900/60">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-xs font-bold text-cyan-400">
                  {projectDetail?.project_number}
                </span>
                <span
                  className="px-2 py-0.5 rounded text-xs font-semibold"
                  style={{
                    backgroundColor: `${projectDetail?.stage_color || '#06b6d4'}20`,
                    color: projectDetail?.stage_color || '#06b6d4',
                  }}
                >
                  {projectDetail?.stage_name}
                </span>
              </div>
              <h3 className="text-xl font-bold text-slate-100">{projectDetail?.name}</h3>
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                <Building className="w-3.5 h-3.5 text-slate-500" />
                <span>Customer: <strong>{projectDetail?.customer_name}</strong></span>
                {projectDetail?.product_name && (
                  <span>• Product: <strong>{projectDetail?.product_name}</strong></span>
                )}
              </p>
            </div>

            <button
              onClick={() => {
                setSelectedProjectId(null);
                setProjectDetail(null);
              }}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 p-6 overflow-y-auto space-y-6">
            {isDetailLoading ? (
              <div className="flex items-center justify-center p-12 text-slate-400 gap-2">
                <Loader2 className="w-5 h-5 animate-spin text-cyan-500" />
                <span>Loading project details...</span>
              </div>
            ) : !projectDetail ? null : (
              <>
                {/* Financial Progress Card */}
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <TrendingUp className="w-4 h-4 text-cyan-400" />
                      Financial Summary
                    </span>
                    <button
                      onClick={(e) => openAdvanceModal(projectDetail, e)}
                      className="text-cyan-400 hover:underline flex items-center gap-1"
                    >
                      Advance Stage <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="grid grid-cols-3 gap-3 pt-1">
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                      <div className="text-[11px] text-slate-500">Contract Value</div>
                      <div className="text-base font-bold text-slate-100">
                        ₹{Number(projectDetail.value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                      <div className="text-[11px] text-emerald-500 font-semibold">Total Paid</div>
                      <div className="text-base font-bold text-emerald-400">
                        ₹{Number(projectDetail.total_paid).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                      <div className="text-[11px] text-amber-500 font-semibold">Outstanding</div>
                      <div className="text-base font-bold text-amber-400">
                        ₹{Number(projectDetail.outstanding_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Stage Transition History Timeline */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <FolderGit2 className="w-4 h-4 text-cyan-400" />
                    Stage Transition History (Audit Trail)
                  </h4>

                  <div className="relative pl-6 space-y-4 before:content-[''] before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                    {((projectDetail?.stage_history) || []).map((h) => (
                      <div key={h.id} className="relative">
                        <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 absolute -left-[21px] top-1 ring-4 ring-slate-950" />
                        <div className="text-xs text-slate-500">
                          {new Date(h.changed_at).toLocaleString()}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          {h.from_stage_name ? (
                            <span className="text-xs text-slate-400">
                              {h.from_stage_name} <ArrowRight className="inline w-3 h-3 text-slate-500 mx-1" />
                            </span>
                          ) : null}
                          <span className="font-semibold text-slate-200 text-sm">
                            {h.to_stage_name}
                          </span>
                        </div>
                        {h.notes && (
                          <p className="text-xs text-slate-300 mt-1 bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
                            {h.notes}
                          </p>
                        )}
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Recorded by: {h.changed_by_name || 'Operator'}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Payments Section */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <Receipt className="w-4 h-4 text-cyan-400" />
                    Project Payments
                  </h4>

                  {(!projectDetail?.payments || projectDetail.payments.length === 0) ? (
                    <EmptyState
                      title="No payments recorded"
                      description="Payment receipts recorded for this project will be listed here."
                    />
                  ) : (
                    <div className="grid gap-2.5">
                      {((projectDetail?.payments) || []).map((pm) => (
                        <div
                          key={pm.id}
                          className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between"
                        >
                          <div>
                            <div className="font-mono text-xs text-slate-400">{pm.payment_number}</div>
                            <div className="font-bold text-slate-100 text-sm">
                              ₹{Number(pm.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </div>
                            <div className="text-xs text-slate-500">
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
              </>
            )}
          </div>
        </div>
      )}

      {/* ADVANCE STAGE MODAL */}
      {stageModalProject && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-lg font-bold text-slate-100">Advance Project Stage</h3>
                <p className="text-xs text-slate-400">{stageModalProject.name} ({stageModalProject.project_number})</p>
              </div>
              <button onClick={() => setStageModalProject(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAdvanceStage} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Target Pipeline Stage *</label>
                <select
                  required
                  value={targetStageId}
                  onChange={(e) => setTargetStageId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  {(pipelines
                    .find((pipe) => pipe.id === stageModalProject.pipeline_id)
                    ?.stages || []).map((stg) => (
                      <option key={stg.id} value={stg.id}>
                        {stg.name}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Transition Notes / Site Report (Audit Log)
                </label>
                <textarea
                  rows={3}
                  value={stageNotes}
                  onChange={(e) => setStageNotes(e.target.value)}
                  placeholder="e.g. Site visit conducted successfully. Structural roof load approved."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button variant="secondary" onClick={() => setStageModalProject(null)} type="button">
                  Cancel
                </Button>
                <Button variant="primary" type="submit" isLoading={isAdvancing}>
                  Confirm Stage Transition
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CREATE PROJECT MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg shadow-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <FolderGit2 className="w-5 h-5 text-cyan-400" />
                Initialize New Project
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Project Name *</label>
                <input
                  type="text"
                  required
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  placeholder="e.g. 500kW Rooftop Solar Installation"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Customer / Account *</label>
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
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Product Offering</label>
                  <select
                    value={createForm.product_id || ''}
                    onChange={(e) => setCreateForm({ ...createForm, product_id: e.target.value || undefined })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="">Select Product</option>
                    {(products || []).map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Pipeline Workflow</label>
                  <select
                    value={createForm.pipeline_id}
                    onChange={(e) => {
                      const pipe = (pipelines || []).find((p) => p.id === e.target.value);
                      setCreateForm({
                        ...createForm,
                        pipeline_id: e.target.value,
                        stage_id: pipe?.stages?.[0]?.id || '',
                      });
                    }}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    {(pipelines || []).map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} {p.is_default ? '(Default)' : ''}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Contract Value (INR) *</label>
                  <input
                    type="number"
                    required
                    value={createForm.value}
                    onChange={(e) => setCreateForm({ ...createForm, value: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
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
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Expected Completion</label>
                  <input
                    type="date"
                    value={createForm.expected_completion_date || ''}
                    onChange={(e) => setCreateForm({ ...createForm, expected_completion_date: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <Button variant="secondary" onClick={() => setShowCreateModal(false)} type="button">
                  Cancel
                </Button>
                <Button variant="primary" type="submit" isLoading={isSubmitting}>
                  Create Project
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
