import React, { useEffect, useState } from 'react';
import { Users, UserPlus, RefreshCw, X } from 'lucide-react';
import { userService } from '../services/userService';
import type { User } from '../types';
import { useNotification } from '../context/NotificationContext';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { EmptyState } from '../components/common/EmptyState';

export const UsersPage: React.FC = () => {
  const { showToast } = useNotification();
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  // New User Form State
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [roleName, setRoleName] = useState('operator');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const data = await userService.getUsers();
      setUsers(data);
    } catch (err: any) {
      showToast('error', 'Failed to load users', err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      setFormError('Password must be at least 8 characters long.');
      return;
    }
    setFormError(null);
    setIsSubmitting(true);

    try {
      await userService.createUser({
        full_name: fullName,
        email,
        password,
        role_name: roleName,
      });
      showToast('success', 'User Created', `User ${fullName} (${roleName}) was added to your organization.`);
      setShowModal(false);
      setFullName('');
      setEmail('');
      setPassword('');
      fetchUsers();
    } catch (err: any) {
      setFormError(err.message || 'Failed to create user');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Users className="w-5 h-5 text-cyan-400" />
            <span>Organization User Directory</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Manage users and operators scoped strictly to your tenant workspace.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={fetchUsers}
            isLoading={isLoading}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowModal(true)}
            leftIcon={<UserPlus className="w-3.5 h-3.5" />}
          >
            Add Operator
          </Button>
        </div>
      </div>

      {/* Users List */}
      <Card>
        {users.length === 0 && !isLoading ? (
          <EmptyState
            icon={<Users className="w-6 h-6" />}
            title="No users found"
            description="No users are currently registered in this organization."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] uppercase tracking-wider text-slate-400 bg-slate-950/40 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-semibold">User</th>
                  <th className="py-3 px-4 font-semibold">Role</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Created Date</th>
                  <th className="py-3 px-4 font-semibold">User ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-cyan-400">
                          {u.full_name ? u.full_name[0].toUpperCase() : 'U'}
                        </div>
                        <div>
                          <p className="font-semibold text-slate-200">{u.full_name}</p>
                          <p className="text-[11px] text-slate-400">{u.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant={u.role_name === 'admin' ? 'info' : 'neutral'} size="sm">
                        {u.role_name || 'operator'}
                      </Badge>
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant={u.is_active ? 'success' : 'error'} size="sm" dot>
                        {u.is_active ? 'Active' : 'Deactivated'}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-500 text-[11px] truncate max-w-[120px]" title={u.id}>
                      {u.id}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Add User Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <UserPlus className="w-4 h-4 text-cyan-400" />
                <span>Add Tenant User</span>
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-white transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 mb-4 rounded-lg bg-rose-950/60 border border-rose-800/60 text-xs text-rose-300">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateUser} className="space-y-4">
              <Input
                label="Full Name"
                required
                placeholder="e.g. Ramesh Patel"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />

              <Input
                label="Corporate Email"
                type="email"
                required
                placeholder="ramesh@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />

              <Input
                label="Temporary Password"
                type="password"
                required
                placeholder="Minimum 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />

              <div className="space-y-1">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Assigned RBAC Role
                </label>
                <select
                  value={roleName}
                  onChange={(e) => setRoleName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500 cursor-pointer"
                >
                  <option value="operator">Operator (Standard CRM Operator)</option>
                  <option value="viewer">Viewer (Read-Only Access)</option>
                  <option value="admin">Administrator (Full Access)</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800 mt-6">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSubmitting}
                >
                  Create User
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
