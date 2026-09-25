import React, { useState, useEffect, useCallback } from 'react';
import {
  Sliders,
  GitBranch,
  Database,
  Filter,
  Cpu,
  CheckSquare,
  Plus,
  RefreshCw,
  Trash2,
  Play,
  RotateCcw,
  Check,
} from 'lucide-react';
import { useNotification } from '../context/NotificationContext';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { EmptyState } from '../components/common/EmptyState';
import {
  pipelineConfigService,
  customFieldService,
  savedViewService,
  workflowService,
  approvalService,
} from '../services/configService';
import type {
  Pipeline,
  PipelineStage,
  CustomField,
  CustomFieldEntityType,
  CustomFieldType,
  SavedView,
  ViewEntityType,
  FilterOperator,
  WorkflowDefinition,
  WorkflowExecution,
  WorkflowActionType,
  ApprovalRequest,
} from '../types';

type SettingsTab = 'pipelines' | 'custom_fields' | 'views' | 'workflows' | 'approvals';

export const SettingsPage: React.FC = () => {
  const { showToast } = useNotification();
  const [activeTab, setActiveTab] = useState<SettingsTab>('pipelines');
  const [isLoading, setIsLoading] = useState(false);

  // -------------------------------------------------------------
  // 1. PIPELINE STATE
  // -------------------------------------------------------------
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
  const [isStageModalOpen, setIsStageModalOpen] = useState(false);
  const [newStageName, setNewStageName] = useState('');
  const [newStageColor, setNewStageColor] = useState('#06b6d4');
  const [isWonStage, setIsWonStage] = useState(false);
  const [isLostStage, setIsLostStage] = useState(false);

  // -------------------------------------------------------------
  // 2. CUSTOM FIELDS STATE
  // -------------------------------------------------------------
  const [customFields, setCustomFields] = useState<CustomField[]>([]);
  const [cfEntityFilter, setCfEntityFilter] = useState<CustomFieldEntityType>('project');
  const [isFieldModalOpen, setIsFieldModalOpen] = useState(false);
  const [cfName, setCfName] = useState('');
  const [cfDisplayName, setCfDisplayName] = useState('');
  const [cfType, setCfType] = useState<CustomFieldType>('text');
  const [cfRequired, setCfRequired] = useState(false);
  const [cfSearchable, setCfSearchable] = useState(true);
  const [cfOptionsStr, setCfOptionsStr] = useState('');

  // -------------------------------------------------------------
  // 3. SAVED VIEWS STATE
  // -------------------------------------------------------------
  const [savedViews, setSavedViews] = useState<SavedView[]>([]);
  const [viewEntityFilter, setViewEntityFilter] = useState<ViewEntityType>('project');
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [viewName, setViewName] = useState('');
  const [viewFilterField, setViewFilterField] = useState('status');
  const [viewFilterOp, setViewFilterOp] = useState<FilterOperator>('=');
  const [viewFilterVal, setViewFilterVal] = useState('active');
  const [viewShared, setViewShared] = useState(true);
  const [viewSortBy, setViewSortBy] = useState('created_at');
  const [previewResult, setPreviewResult] = useState<Record<string, unknown>[] | null>(null);
  const [previewViewName, setPreviewViewName] = useState<string>('');

  // -------------------------------------------------------------
  // 4. WORKFLOW ENGINE STATE
  // -------------------------------------------------------------
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [wfSubTab, setWfSubTab] = useState<'definitions' | 'history'>('definitions');
  const [isWfModalOpen, setIsWfModalOpen] = useState(false);
  const [wfName, setWfName] = useState('');
  const [wfDescription, setWfDescription] = useState('');
  const [wfTrigger, setWfTrigger] = useState('project.stage_changed');
  const [wfCondField, setWfCondField] = useState('stage_name');
  const [wfCondOp, setWfCondOp] = useState('=');
  const [wfCondVal, setWfCondVal] = useState('Approval');
  const [wfActionType, setWfActionType] = useState<WorkflowActionType>('create_follow_up');
  const [wfActionTitle, setWfActionTitle] = useState('Verify approval requirements');
  const [wfActionDueDays, setWfActionDueDays] = useState(2);

  // -------------------------------------------------------------
  // 5. APPROVALS STATE
  // -------------------------------------------------------------
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [selectedApproval, setSelectedApproval] = useState<ApprovalRequest | null>(null);
  const [decisionModalOpen, setDecisionModalOpen] = useState(false);
  const [decisionChoice, setDecisionChoice] = useState<'approved' | 'rejected'>('approved');
  const [decisionComment, setDecisionComment] = useState('');

  // =============================================================
  // DATA LOADERS
  // =============================================================
  const loadPipelines = useCallback(async () => {
    try {
      const data = await pipelineConfigService.getPipelines();
      setPipelines(data);
      if (data.length > 0 && !selectedPipeline) {
        setSelectedPipeline(data[0]);
      } else if (selectedPipeline) {
        const refreshed = data.find((p) => p.id === selectedPipeline.id);
        if (refreshed) setSelectedPipeline(refreshed);
      }
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Failed loading pipelines', e.message);
    }
  }, [selectedPipeline, showToast]);

  const loadCustomFields = useCallback(async () => {
    try {
      const data = await customFieldService.getCustomFields(cfEntityFilter);
      setCustomFields(data);
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Failed loading custom fields', e.message);
    }
  }, [cfEntityFilter, showToast]);

  const loadSavedViews = useCallback(async () => {
    try {
      const data = await savedViewService.getViews(viewEntityFilter);
      setSavedViews(data);
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Failed loading saved views', e.message);
    }
  }, [viewEntityFilter, showToast]);

  const loadWorkflows = useCallback(async () => {
    try {
      const [wfData, execData] = await Promise.all([
        workflowService.getWorkflows(),
        workflowService.getExecutions(undefined, 30),
      ]);
      setWorkflows(wfData);
      setExecutions(execData);
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Failed loading workflows', e.message);
    }
  }, [showToast]);

  const loadApprovals = useCallback(async () => {
    try {
      const data = await approvalService.getApprovals();
      setApprovals(data);
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Failed loading approvals', e.message);
    }
  }, [showToast]);

  useEffect(() => {
    setIsLoading(true);
    const init = async () => {
      if (activeTab === 'pipelines') await loadPipelines();
      if (activeTab === 'custom_fields') await loadCustomFields();
      if (activeTab === 'views') await loadSavedViews();
      if (activeTab === 'workflows') await loadWorkflows();
      if (activeTab === 'approvals') await loadApprovals();
      setIsLoading(false);
    };
    init();
  }, [activeTab, loadPipelines, loadCustomFields, loadSavedViews, loadWorkflows, loadApprovals]);

  // =============================================================
  // HANDLERS: PIPELINES
  // =============================================================
  const handleCreateStage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPipeline || !newStageName.trim()) return;

    try {
      const order = (selectedPipeline.stages || []).length + 1;
      await pipelineConfigService.createStage(selectedPipeline.id, {
        name: newStageName.trim(),
        order,
        color: newStageColor,
        is_closed_won: isWonStage,
        is_closed_lost: isLostStage,
        is_active: true,
      });
      showToast('success', 'Stage Created', `Stage "${newStageName}" added to pipeline.`);
      setIsStageModalOpen(false);
      setNewStageName('');
      setIsWonStage(false);
      setIsLostStage(false);
      await loadPipelines();
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Create Stage Failed', e.message);
    }
  };

  const handleDeactivateStage = async (stage: PipelineStage) => {
    if (!selectedPipeline) return;
    if (!confirm(`Are you sure you want to deactivate stage "${stage.name}"? Historical project stage records will remain safely preserved.`)) {
      return;
    }
    try {
      await pipelineConfigService.deactivateStage(selectedPipeline.id, stage.id);
      showToast('success', 'Stage Deactivated', `Stage "${stage.name}" is now inactive.`);
      await loadPipelines();
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Failed to deactivate stage', e.message);
    }
  };

  // =============================================================
  // HANDLERS: CUSTOM FIELDS
  // =============================================================
  const handleCreateField = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cfDisplayName.trim()) return;

    const rawSlug = cfName.trim()
      ? cfName.trim().toLowerCase().replace(/[^a-z0-9_]/g, '_')
      : cfDisplayName.trim().toLowerCase().replace(/[^a-z0-9_]/g, '_');

    const options = cfType === 'select' && cfOptionsStr.trim()
      ? cfOptionsStr.split(',').map((s) => s.trim()).filter(Boolean)
      : undefined;

    try {
      await customFieldService.createCustomField({
        entity_type: cfEntityFilter,
        field_name: rawSlug,
        display_name: cfDisplayName.trim(),
        field_type: cfType,
        is_required: cfRequired,
        is_searchable: cfSearchable,
        options,
        is_active: true,
      });
      showToast('success', 'Custom Field Created', `Added field "${cfDisplayName}" for ${cfEntityFilter}.`);
      setIsFieldModalOpen(false);
      setCfDisplayName('');
      setCfName('');
      setCfOptionsStr('');
      await loadCustomFields();
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Failed creating custom field', e.message);
    }
  };

  const handleDeactivateField = async (field: CustomField) => {
    if (!confirm(`Deactivate custom field "${field.display_name}"? Existing saved values are retained safely.`)) {
      return;
    }
    try {
      await customFieldService.deactivateCustomField(field.id);
      showToast('success', 'Field Deactivated', `Field "${field.display_name}" deactivated.`);
      await loadCustomFields();
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Deactivation Failed', e.message);
    }
  };

  // =============================================================
  // HANDLERS: SAVED VIEWS
  // =============================================================
  const handleCreateView = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!viewName.trim()) return;

    try {
      await savedViewService.createView({
        name: viewName.trim(),
        entity_type: viewEntityFilter,
        filters: [
          {
            field: viewFilterField.trim(),
            operator: viewFilterOp,
            value: viewFilterVal.trim(),
          },
        ],
        sort_by: viewSortBy,
        sort_direction: 'desc',
        is_shared: viewShared,
      });
      showToast('success', 'Saved View Created', `View "${viewName}" saved successfully.`);
      setIsViewModalOpen(false);
      setViewName('');
      await loadSavedViews();
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Create View Failed', e.message);
    }
  };

  const handleDeleteView = async (view: SavedView) => {
    if (!confirm(`Delete saved view "${view.name}"?`)) return;
    try {
      await savedViewService.deleteView(view.id);
      showToast('success', 'View Deleted', `Saved view removed.`);
      await loadSavedViews();
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Delete Failed', e.message);
    }
  };

  const handleExecutePreview = async (view: SavedView) => {
    try {
      setPreviewViewName(view.name);
      const res = await savedViewService.executeView(view.id, 1, 10);
      setPreviewResult(res.items);
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Preview Failed', e.message);
    }
  };

  // =============================================================
  // HANDLERS: WORKFLOWS
  // =============================================================
  const handleCreateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!wfName.trim()) return;

    try {
      const actions = [];
      if (wfActionType === 'create_follow_up') {
        actions.push({
          action_type: wfActionType,
          parameters: {
            title: wfActionTitle,
            days_from_now: Number(wfActionDueDays) || 1,
            priority: 'high',
          },
        });
      } else if (wfActionType === 'create_notification') {
        actions.push({
          action_type: wfActionType,
          parameters: {
            title: `Alert: ${wfName}`,
            message: `Automated workflow notification triggered by ${wfTrigger}`,
            notification_type: 'info',
          },
        });
      } else {
        actions.push({
          action_type: wfActionType,
          parameters: {
            notes: `Automated action execution from workflow ${wfName}`,
          },
        });
      }

      await workflowService.createWorkflow({
        name: wfName.trim(),
        description: wfDescription.trim() || undefined,
        trigger_event: wfTrigger,
        conditions: [
          {
            field: wfCondField.trim(),
            operator: wfCondOp,
            value: wfCondVal.trim(),
          },
        ],
        actions,
        is_active: true,
      });

      showToast('success', 'Workflow Created', `Automation rule "${wfName}" activated.`);
      setIsWfModalOpen(false);
      setWfName('');
      setWfDescription('');
      await loadWorkflows();
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Create Workflow Failed', e.message);
    }
  };

  const handleToggleWorkflow = async (wf: WorkflowDefinition) => {
    try {
      if (wf.is_active) {
        await workflowService.deactivateWorkflow(wf.id);
        showToast('info', 'Workflow Deactivated', `Workflow "${wf.name}" is now disabled.`);
      } else {
        await workflowService.activateWorkflow(wf.id);
        showToast('success', 'Workflow Activated', `Workflow "${wf.name}" is now listening for events.`);
      }
      await loadWorkflows();
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Toggle Failed', e.message);
    }
  };

  const handleRetryExecution = async (execId: string) => {
    try {
      await workflowService.retryExecution(execId);
      showToast('success', 'Retry Initiated', 'Workflow execution has been retried.');
      await loadWorkflows();
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Retry Failed', e.message);
    }
  };

  // =============================================================
  // HANDLERS: APPROVALS
  // =============================================================
  const handleDecideApproval = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApproval) return;

    try {
      await approvalService.decideApproval(selectedApproval.id, {
        decision: decisionChoice,
        comments: decisionComment.trim() || undefined,
      });
      showToast('success', 'Decision Recorded', `Approval request marked as ${decisionChoice}.`);
      setDecisionModalOpen(false);
      setSelectedApproval(null);
      setDecisionComment('');
      await loadApprovals();
    } catch (err: unknown) {
      const e = err as Error;
      showToast('error', 'Decision Failed', e.message);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <Sliders className="w-6 h-6 text-cyan-400" />
            <h1 className="text-xl font-bold tracking-tight text-white">Platform Settings & Automation</h1>
            <span className="text-[10px] bg-cyan-950 text-cyan-400 font-semibold px-2 py-0.5 rounded border border-cyan-800/60">
              Phase 3
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Configure pipeline stages, tenant custom fields, saved views, and declarative workflow automation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              if (activeTab === 'pipelines') loadPipelines();
              if (activeTab === 'custom_fields') loadCustomFields();
              if (activeTab === 'views') loadSavedViews();
              if (activeTab === 'workflows') loadWorkflows();
              if (activeTab === 'approvals') loadApprovals();
            }}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('pipelines')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'pipelines'
              ? 'bg-cyan-600/15 text-cyan-400 border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <GitBranch className="w-4 h-4" />
          <span>Pipelines & Stages</span>
        </button>

        <button
          onClick={() => setActiveTab('custom_fields')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'custom_fields'
              ? 'bg-cyan-600/15 text-cyan-400 border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>Custom Fields</span>
        </button>

        <button
          onClick={() => setActiveTab('views')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'views'
              ? 'bg-cyan-600/15 text-cyan-400 border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <Filter className="w-4 h-4" />
          <span>Saved Views</span>
        </button>

        <button
          onClick={() => setActiveTab('workflows')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'workflows'
              ? 'bg-cyan-600/15 text-cyan-400 border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <Cpu className="w-4 h-4" />
          <span>Workflow Engine</span>
        </button>

        <button
          onClick={() => setActiveTab('approvals')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'approvals'
              ? 'bg-cyan-600/15 text-cyan-400 border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <CheckSquare className="w-4 h-4" />
          <span>Approvals</span>
        </button>
      </div>

      {/* ========================================================= */}
      {/* 1. PIPELINES TAB */}
      {/* ========================================================= */}
      {activeTab === 'pipelines' && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Pipeline Selector List */}
          <div className="space-y-4">
            <Card title="Available Pipelines">
              <div className="space-y-2 mt-2">
                {pipelines.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setSelectedPipeline(p)}
                    className={`w-full text-left p-3 rounded-xl border transition-all ${
                      selectedPipeline?.id === p.id
                        ? 'bg-cyan-950/30 border-cyan-500/40 text-cyan-300 shadow-sm'
                        : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs">{p.name}</span>
                      {p.is_default && (
                        <Badge variant="info" size="sm">Default</Badge>
                      )}
                    </div>
                    {p.description && (
                      <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{p.description}</p>
                    )}
                    <div className="flex items-center gap-1.5 mt-2 text-[10px] text-slate-500">
                      <span>{(p.stages || []).length} stages</span>
                      <span>•</span>
                      <span>{p.is_active ? 'Active' : 'Inactive'}</span>
                    </div>
                  </button>
                ))}
              </div>
            </Card>
          </div>

          {/* Selected Pipeline Stages Editor */}
          <div className="md:col-span-3 space-y-4">
            {selectedPipeline ? (
              <Card
                title={`Stages in "${selectedPipeline.name}"`}
                actions={
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setIsStageModalOpen(true)}
                    leftIcon={<Plus className="w-3.5 h-3.5" />}
                  >
                    Add Stage
                  </Button>
                }
              >
                <p className="text-xs text-slate-400 mb-4">
                  Configure execution order, milestone colors, and close conditions. Deactivating a stage guarantees complete data preservation for historical projects.
                </p>

                <div className="space-y-2.5">
                  {(selectedPipeline.stages || []).map((stage, idx) => (
                    <div
                      key={stage.id}
                      className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between gap-4 transition-colors hover:border-slate-700"
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-6 h-6 rounded-full bg-slate-800 text-[11px] font-mono text-slate-400 flex items-center justify-center border border-slate-700">
                          {stage.order || idx + 1}
                        </span>
                        <div
                          className="w-3.5 h-3.5 rounded-full shrink-0 shadow-sm"
                          style={{ backgroundColor: stage.color || '#06b6d4' }}
                        />
                        <div>
                          <p className="text-xs font-semibold text-slate-200">{stage.name}</p>
                          <div className="flex items-center gap-2 mt-1">
                            {stage.is_closed_won && (
                              <Badge variant="success" size="sm">Closed Won</Badge>
                            )}
                            {stage.is_closed_lost && (
                              <Badge variant="error" size="sm">Closed Lost</Badge>
                            )}
                            {stage.is_active === false && (
                              <Badge variant="neutral" size="sm">Deactivated</Badge>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {stage.is_active !== false && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeactivateStage(stage)}
                            className="text-slate-400 hover:text-rose-400"
                            title="Deactivate Stage (Historical Data Preserved)"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            ) : (
              <EmptyState
                icon={<GitBranch className="w-8 h-8 text-slate-500" />}
                title="No Pipeline Selected"
                description="Select a pipeline on the left to configure stages."
              />
            )}
          </div>
        </div>
      )}

      {/* Add Stage Modal */}
      {isStageModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <Plus className="w-4 h-4 text-cyan-400" />
              <span>Add Stage to {selectedPipeline?.name}</span>
            </h3>

            <form onSubmit={handleCreateStage} className="space-y-4">
              <Input
                label="Stage Name"
                required
                placeholder="e.g., Quotation Sent"
                value={newStageName}
                onChange={(e) => setNewStageName(e.target.value)}
              />

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Stage Color Accent
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="color"
                    value={newStageColor}
                    onChange={(e) => setNewStageColor(e.target.value)}
                    className="w-10 h-8 rounded border border-slate-700 bg-transparent cursor-pointer"
                  />
                  <span className="text-xs font-mono text-slate-400">{newStageColor}</span>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-800">
                <label className="flex items-center gap-2.5 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isWonStage}
                    onChange={(e) => {
                      setIsWonStage(e.target.checked);
                      if (e.target.checked) setIsLostStage(false);
                    }}
                    className="rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
                  />
                  <span>Mark as Closed Won Milestone</span>
                </label>

                <label className="flex items-center gap-2.5 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isLostStage}
                    onChange={(e) => {
                      setIsLostStage(e.target.checked);
                      if (e.target.checked) setIsWonStage(false);
                    }}
                    className="rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
                  />
                  <span>Mark as Closed Lost Milestone</span>
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <Button variant="ghost" size="sm" onClick={() => setIsStageModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  Add Stage
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 2. CUSTOM FIELDS TAB */}
      {/* ========================================================= */}
      {activeTab === 'custom_fields' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            {/* Entity selector tabs */}
            <div className="flex items-center gap-2 bg-slate-900 p-1 rounded-xl border border-slate-800 w-fit">
              {(['project', 'customer', 'product'] as CustomFieldEntityType[]).map((ent) => (
                <button
                  key={ent}
                  onClick={() => setCfEntityFilter(ent)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
                    cfEntityFilter === ent
                      ? 'bg-cyan-600/20 text-cyan-300 border border-cyan-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {ent} Fields
                </button>
              ))}
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsFieldModalOpen(true)}
              leftIcon={<Plus className="w-3.5 h-3.5" />}
            >
              Add Custom Field
            </Button>
          </div>

          <Card title={`${cfEntityFilter.toUpperCase()} Custom Fields`}>
            {customFields.length === 0 ? (
              <EmptyState
                icon={<Database className="w-8 h-8 text-slate-500" />}
                title={`No Custom Fields for ${cfEntityFilter}`}
                description="Add tenant-specific metadata fields without schema alterations."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold text-[10px]">
                    <tr>
                      <th className="p-3">Display Name</th>
                      <th className="p-3">Field Key</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Required</th>
                      <th className="p-3">Searchable</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {customFields.map((f) => (
                      <tr key={f.id} className="hover:bg-slate-900/40">
                        <td className="p-3 font-semibold text-slate-200">{f.display_name}</td>
                        <td className="p-3 font-mono text-[11px] text-cyan-400">{f.field_name}</td>
                        <td className="p-3">
                          <Badge variant="info" size="sm">{f.field_type}</Badge>
                        </td>
                        <td className="p-3 text-slate-400">
                          {f.is_required ? <Check className="w-3.5 h-3.5 text-cyan-400" /> : '—'}
                        </td>
                        <td className="p-3 text-slate-400">
                          {f.is_searchable ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : '—'}
                        </td>
                        <td className="p-3">
                          <Badge variant={f.is_active ? 'success' : 'neutral'} size="sm">
                            {f.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </td>
                        <td className="p-3 text-right">
                          {f.is_active && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeactivateField(f)}
                              className="text-slate-500 hover:text-rose-400"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Add Custom Field Modal */}
      {isFieldModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <Database className="w-4 h-4 text-cyan-400" />
              <span>New {cfEntityFilter.toUpperCase()} Custom Field</span>
            </h3>

            <form onSubmit={handleCreateField} className="space-y-4">
              <Input
                label="Display Label"
                required
                placeholder="e.g., Installation Capacity (kW)"
                value={cfDisplayName}
                onChange={(e) => setCfDisplayName(e.target.value)}
              />

              <Input
                label="Database Key (Auto-slugged)"
                placeholder="e.g., installation_capacity"
                value={cfName}
                onChange={(e) => setCfName(e.target.value)}
                helperText="Identifier used in workflow expressions and filters."
              />

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Field Type
                </label>
                <select
                  value={cfType}
                  onChange={(e) => setCfType(e.target.value as CustomFieldType)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="text">Text (Single Line)</option>
                  <option value="number">Number (Integer / Decimal)</option>
                  <option value="currency">Currency (INR / Amount)</option>
                  <option value="date">Date (YYYY-MM-DD)</option>
                  <option value="boolean">Boolean (Yes / No Toggle)</option>
                  <option value="select">Dropdown Select (Enumeration)</option>
                </select>
              </div>

              {cfType === 'select' && (
                <Input
                  label="Select Options (Comma-separated)"
                  required
                  placeholder="e.g., Commercial, Industrial, Residential"
                  value={cfOptionsStr}
                  onChange={(e) => setCfOptionsStr(e.target.value)}
                  helperText="Options available in the selection menu."
                />
              )}

              <div className="flex items-center gap-6 pt-2">
                <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={cfRequired}
                    onChange={(e) => setCfRequired(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
                  />
                  <span>Mandatory Field</span>
                </label>

                <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={cfSearchable}
                    onChange={(e) => setCfSearchable(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
                  />
                  <span>Indexed for Search</span>
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <Button variant="ghost" size="sm" onClick={() => setIsFieldModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  Create Field
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 3. SAVED VIEWS TAB */}
      {/* ========================================================= */}
      {activeTab === 'views' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2 bg-slate-900 p-1 rounded-xl border border-slate-800 w-fit">
              {(['project', 'customer', 'payment', 'follow_up'] as ViewEntityType[]).map((ent) => (
                <button
                  key={ent}
                  onClick={() => setViewEntityFilter(ent)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
                    viewEntityFilter === ent
                      ? 'bg-cyan-600/20 text-cyan-300 border border-cyan-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {ent.replace('_', ' ')} Views
                </button>
              ))}
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsViewModalOpen(true)}
              leftIcon={<Plus className="w-3.5 h-3.5" />}
            >
              New Saved View
            </Button>
          </div>

          <Card title={`Saved Views for ${viewEntityFilter.toUpperCase()}`}>
            {savedViews.length === 0 ? (
              <EmptyState
                icon={<Filter className="w-8 h-8 text-slate-500" />}
                title={`No Saved Views for ${viewEntityFilter}`}
                description="Create tenant-scoped custom filters and column views."
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {savedViews.map((v) => (
                  <div
                    key={v.id}
                    className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition-colors"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-xs text-slate-200">{v.name}</span>
                        {v.is_shared && (
                          <Badge variant="info" size="sm">Shared</Badge>
                        )}
                      </div>

                      <div className="space-y-1.5 text-[11px] text-slate-400 mt-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 font-mono">
                        {(v.filters || []).map((f, i) => (
                          <div key={i} className="flex items-center justify-between">
                            <span className="text-cyan-400">{f.field}</span>
                            <span className="text-amber-400">{f.operator}</span>
                            <span className="text-slate-200 truncate max-w-[120px]">{String(f.value)}</span>
                          </div>
                        ))}
                      </div>

                      <div className="flex items-center gap-2 mt-3 text-[10px] text-slate-500">
                        <span>sort: {v.sort_by || 'created_at'} ({v.sort_direction})</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-800/80">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleExecutePreview(v)}
                        leftIcon={<Play className="w-3 h-3 text-cyan-400" />}
                      >
                        Preview Query
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteView(v)}
                        className="text-slate-500 hover:text-rose-400"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Preview Modal */}
          {previewResult !== null && (
            <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 space-y-4 shadow-2xl">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                    <Play className="w-4 h-4 text-cyan-400" />
                    <span>Preview Results: {previewViewName} ({previewResult.length} records)</span>
                  </h3>
                  <Button variant="ghost" size="sm" onClick={() => setPreviewResult(null)}>
                    Close
                  </Button>
                </div>

                <div className="max-h-80 overflow-y-auto bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300">
                  <pre>{JSON.stringify(previewResult, null, 2)}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add View Modal */}
      {isViewModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <Filter className="w-4 h-4 text-cyan-400" />
              <span>Create Saved View ({viewEntityFilter})</span>
            </h3>

            <form onSubmit={handleCreateView} className="space-y-4">
              <Input
                label="View Name"
                required
                placeholder="e.g., Active High Priority Projects"
                value={viewName}
                onChange={(e) => setViewName(e.target.value)}
              />

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Filter Condition
                </p>

                <div className="grid grid-cols-3 gap-2">
                  <Input
                    label="Field"
                    placeholder="field name"
                    value={viewFilterField}
                    onChange={(e) => setViewFilterField(e.target.value)}
                  />

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Operator</label>
                    <select
                      value={viewFilterOp}
                      onChange={(e) => setViewFilterOp(e.target.value as FilterOperator)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2 py-2 text-xs text-slate-200"
                    >
                      <option value="=">=</option>
                      <option value="!=">!=</option>
                      <option value=">">&gt;</option>
                      <option value=">=">&gt;=</option>
                      <option value="<">&lt;</option>
                      <option value="<=">&lt;=</option>
                      <option value="contains">contains</option>
                    </select>
                  </div>

                  <Input
                    label="Value"
                    placeholder="filter value"
                    value={viewFilterVal}
                    onChange={(e) => setViewFilterVal(e.target.value)}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="Sort By Field"
                  value={viewSortBy}
                  onChange={(e) => setViewSortBy(e.target.value)}
                />
                <div className="pt-6">
                  <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={viewShared}
                      onChange={(e) => setViewShared(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
                    />
                    <span>Share across Tenant</span>
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <Button variant="ghost" size="sm" onClick={() => setIsViewModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  Save View
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 4. WORKFLOW ENGINE TAB */}
      {/* ========================================================= */}
      {activeTab === 'workflows' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2 bg-slate-900 p-1 rounded-xl border border-slate-800 w-fit">
              <button
                onClick={() => setWfSubTab('definitions')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  wfSubTab === 'definitions'
                    ? 'bg-cyan-600/20 text-cyan-300 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Automation Rules ({workflows.length})
              </button>
              <button
                onClick={() => setWfSubTab('history')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  wfSubTab === 'history'
                    ? 'bg-cyan-600/20 text-cyan-300 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Execution Audit Log ({executions.length})
              </button>
            </div>

            {wfSubTab === 'definitions' && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsWfModalOpen(true)}
                leftIcon={<Plus className="w-3.5 h-3.5" />}
              >
                Create Workflow Rule
              </Button>
            )}
          </div>

          {wfSubTab === 'definitions' ? (
            <Card title="Configured Automation Rules">
              {workflows.length === 0 ? (
                <EmptyState
                  icon={<Cpu className="w-8 h-8 text-slate-500" />}
                  title="No Workflows Defined"
                  description="Set up automatic follow-ups and notifications triggered by project or payment events."
                />
              ) : (
                <div className="space-y-3">
                  {workflows.map((wf) => (
                    <div
                      key={wf.id}
                      className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-colors hover:border-slate-700"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2.5">
                          <span className="font-semibold text-xs text-slate-200">{wf.name}</span>
                          <Badge variant="info" size="sm">{wf.trigger_event}</Badge>
                          <Badge variant={wf.is_active ? 'success' : 'neutral'} size="sm">
                            {wf.is_active ? 'Active' : 'Disabled'}
                          </Badge>
                        </div>
                        {wf.description && (
                          <p className="text-[11px] text-slate-400">{wf.description}</p>
                        )}
                        <div className="flex items-center gap-4 text-[10px] text-slate-500 pt-1">
                          <span>Conditions: {(wf.conditions || []).length}</span>
                          <span>•</span>
                          <span>Actions: {(wf.actions || []).length}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          variant={wf.is_active ? 'secondary' : 'primary'}
                          size="sm"
                          onClick={() => handleToggleWorkflow(wf)}
                        >
                          {wf.is_active ? 'Disable' : 'Enable'}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          ) : (
            <Card title="Workflow Execution Trail & Failure Recovery">
              {executions.length === 0 ? (
                <EmptyState
                  icon={<RotateCcw className="w-8 h-8 text-slate-500" />}
                  title="No Workflow Executions Recorded"
                  description="When business events occur, workflow execution records appear here."
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold text-[10px]">
                      <tr>
                        <th className="p-3">Trigger Event</th>
                        <th className="p-3">Entity ID</th>
                        <th className="p-3">Status</th>
                        <th className="p-3">Retries</th>
                        <th className="p-3">Started At</th>
                        <th className="p-3">Error / Diagnostics</th>
                        <th className="p-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                      {executions.map((ex) => (
                        <tr key={ex.id} className="hover:bg-slate-900/40">
                          <td className="p-3 text-cyan-400">{ex.trigger_event}</td>
                          <td className="p-3 text-slate-400 truncate max-w-[120px]">{ex.entity_id}</td>
                          <td className="p-3">
                            <Badge
                              variant={
                                ex.status === 'completed'
                                  ? 'success'
                                  : ex.status === 'failed'
                                  ? 'error'
                                  : ex.status === 'retrying'
                                  ? 'warning'
                                  : 'neutral'
                              }
                              size="sm"
                            >
                              {ex.status}
                            </Badge>
                          </td>
                          <td className="p-3 text-slate-300">{ex.retry_count}</td>
                          <td className="p-3 text-slate-400 text-[10px]">
                            {new Date(ex.started_at).toLocaleTimeString()}
                          </td>
                          <td className="p-3 text-rose-400 truncate max-w-[180px]">
                            {ex.error_message || '—'}
                          </td>
                          <td className="p-3 text-right">
                            {ex.status === 'failed' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRetryExecution(ex.id)}
                                leftIcon={<RotateCcw className="w-3 h-3" />}
                              >
                                Retry
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          )}
        </div>
      )}

      {/* Add Workflow Modal */}
      {isWfModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>New Declarative Workflow Rule</span>
            </h3>

            <form onSubmit={handleCreateWorkflow} className="space-y-4">
              <Input
                label="Rule Name"
                required
                placeholder="e.g., Auto-create Follow-up on Stage Approval"
                value={wfName}
                onChange={(e) => setWfName(e.target.value)}
              />

              <Input
                label="Description"
                placeholder="e.g., Triggers a 2-day verification follow-up task"
                value={wfDescription}
                onChange={(e) => setWfDescription(e.target.value)}
              />

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Trigger Event
                </label>
                <select
                  value={wfTrigger}
                  onChange={(e) => setWfTrigger(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="project.stage_changed">Project Stage Changed</option>
                  <option value="project.created">Project Created</option>
                  <option value="customer.created">Customer Created</option>
                  <option value="payment.created">Payment Created</option>
                  <option value="follow_up.completed">Follow-up Completed</option>
                </select>
              </div>

              {/* Condition Section */}
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Condition (Evaluated on Event)
                </p>
                <div className="grid grid-cols-3 gap-2">
                  <Input
                    label="Field"
                    value={wfCondField}
                    onChange={(e) => setWfCondField(e.target.value)}
                  />
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Op</label>
                    <select
                      value={wfCondOp}
                      onChange={(e) => setWfCondOp(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2 py-2 text-xs text-slate-200"
                    >
                      <option value="=">=</option>
                      <option value="!=">!=</option>
                      <option value=">">&gt;</option>
                      <option value="contains">contains</option>
                    </select>
                  </div>
                  <Input
                    label="Value"
                    value={wfCondVal}
                    onChange={(e) => setWfCondVal(e.target.value)}
                  />
                </div>
              </div>

              {/* Action Section */}
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Automated Action
                </p>
                <select
                  value={wfActionType}
                  onChange={(e) => setWfActionType(e.target.value as WorkflowActionType)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200"
                >
                  <option value="create_follow_up">Create Operator Follow-up</option>
                  <option value="create_notification">Generate In-app Notification</option>
                  <option value="add_activity">Log Timeline Activity</option>
                </select>

                {wfActionType === 'create_follow_up' && (
                  <div className="grid grid-cols-3 gap-2">
                    <div className="col-span-2">
                      <Input
                        label="Follow-up Title"
                        value={wfActionTitle}
                        onChange={(e) => setWfActionTitle(e.target.value)}
                      />
                    </div>
                    <Input
                      label="Days Due"
                      type="number"
                      value={String(wfActionDueDays)}
                      onChange={(e) => setWfActionDueDays(Number(e.target.value))}
                    />
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <Button variant="ghost" size="sm" onClick={() => setIsWfModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  Activate Rule
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 5. APPROVALS TAB */}
      {/* ========================================================= */}
      {activeTab === 'approvals' && (
        <div className="space-y-6">
          <Card title="Approvals Governance Inbox">
            {approvals.length === 0 ? (
              <EmptyState
                icon={<CheckSquare className="w-8 h-8 text-slate-500" />}
                title="No Pending Approvals"
                description="Workflow approvals requested for projects or payments will show up here."
              />
            ) : (
              <div className="divide-y divide-slate-800/60">
                {approvals.map((appr) => (
                  <div
                    key={appr.id}
                    className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-900/40 transition-colors"
                  >
                    <div>
                      <div className="flex items-center gap-2.5">
                        <span className="font-semibold text-xs text-slate-200 uppercase">
                          {appr.approval_type} ({appr.entity_type})
                        </span>
                        <Badge
                          variant={
                            appr.status === 'approved'
                              ? 'success'
                              : appr.status === 'rejected'
                              ? 'error'
                              : 'warning'
                          }
                          size="sm"
                        >
                          {appr.status}
                        </Badge>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1 font-mono">
                        Target Record ID: {appr.entity_id}
                      </p>
                      {appr.decision_comments && (
                        <p className="text-xs text-slate-300 italic mt-1 bg-slate-950 p-2 rounded border border-slate-850">
                          &quot;{appr.decision_comments}&quot;
                        </p>
                      )}
                      <div className="flex items-center gap-3 text-[10px] text-slate-500 mt-2">
                        <span>Requested: {new Date(appr.requested_at).toLocaleString()}</span>
                        {appr.decided_at && (
                          <span>• Decided: {new Date(appr.decided_at).toLocaleString()}</span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {appr.status === 'pending' && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => {
                            setSelectedApproval(appr);
                            setDecisionModalOpen(true);
                          }}
                        >
                          Review & Decide
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Decision Modal */}
      {decisionModalOpen && selectedApproval && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <CheckSquare className="w-4 h-4 text-cyan-400" />
              <span>Record Approval Decision</span>
            </h3>

            <form onSubmit={handleDecideApproval} className="space-y-4">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-xs font-semibold text-emerald-400 cursor-pointer">
                  <input
                    type="radio"
                    name="decision"
                    value="approved"
                    checked={decisionChoice === 'approved'}
                    onChange={() => setDecisionChoice('approved')}
                    className="text-emerald-500 focus:ring-emerald-500"
                  />
                  <span>Approve</span>
                </label>

                <label className="flex items-center gap-2 text-xs font-semibold text-rose-400 cursor-pointer">
                  <input
                    type="radio"
                    name="decision"
                    value="rejected"
                    checked={decisionChoice === 'rejected'}
                    onChange={() => setDecisionChoice('rejected')}
                    className="text-rose-500 focus:ring-rose-500"
                  />
                  <span>Reject</span>
                </label>
              </div>

              <Input
                label="Comments / Rationale"
                placeholder="e.g., Quotation and credit verification approved."
                value={decisionComment}
                onChange={(e) => setDecisionComment(e.target.value)}
              />

              <div className="flex justify-end gap-3 pt-3">
                <Button variant="ghost" size="sm" onClick={() => setDecisionModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  Confirm Decision
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
