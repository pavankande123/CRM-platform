import React, { useState } from 'react';
import { Building2, Save } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { apiRequest } from '../services/apiClient';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';

export const TenantPage: React.FC = () => {
  const { organization, refreshProfile } = useAuth();
  const { showToast } = useNotification();
  const [orgName, setOrgName] = useState(organization?.name || '');
  const [isSaving, setIsSaving] = useState(false);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgName.trim()) return;

    setIsSaving(true);
    try {
      await apiRequest('/tenants/me', {
        method: 'PATCH',
        body: JSON.stringify({ name: orgName.trim() }),
      });
      await refreshProfile();
      showToast('success', 'Tenant Updated', 'Organization name updated successfully.');
    } catch (err: any) {
      showToast('error', 'Update Failed', err.message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Building2 className="w-5 h-5 text-cyan-400" />
          <span>Tenant Organization Configuration</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Review tenant isolation metadata and manage organization settings.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Card title="Organization Profile">
            <form onSubmit={handleUpdate} className="space-y-4">
              <Input
                label="Organization Display Name"
                required
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                helperText="Updating this name will record an audit trail event."
              />

              <Input
                label="Tenant URL Slug"
                disabled
                value={organization?.slug || ''}
                helperText="Slug is permanently anchored for subdomains and routing."
              />

              <div className="pt-2">
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSaving}
                  leftIcon={<Save className="w-3.5 h-3.5" />}
                >
                  Save Changes
                </Button>
              </div>
            </form>
          </Card>
        </div>

        <div className="space-y-6">
          <Card title="Tenant Partition Security">
            <div className="space-y-4 text-xs">
              <div>
                <p className="text-slate-400 text-[11px]">Partition UUID</p>
                <code className="text-[11px] font-mono text-cyan-400 break-all block mt-0.5">
                  {organization?.id}
                </code>
              </div>

              <div>
                <p className="text-slate-400 text-[11px]">Subscription Tier</p>
                <p className="text-slate-200 font-semibold uppercase mt-0.5">
                  {organization?.tier || 'standard'}
                </p>
              </div>

              <div>
                <p className="text-slate-400 text-[11px]">Tenant Status</p>
                <div className="mt-1">
                  <Badge variant={organization?.is_active ? 'success' : 'error'} size="sm" dot>
                    {organization?.is_active ? 'Active & Healthy' : 'Suspended'}
                  </Badge>
                </div>
              </div>

              <div>
                <p className="text-slate-400 text-[11px]">Created At</p>
                <p className="text-slate-300 font-mono mt-0.5">
                  {organization?.created_at ? new Date(organization.created_at).toLocaleDateString() : '—'}
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
