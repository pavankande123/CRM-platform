import React, { useState, useEffect, useCallback } from 'react';
import { Package, Plus, Search, Tag, X, Loader2 } from 'lucide-react';
import { productService } from '../services/productService';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { useNotifications } from '../context/NotificationContext';
import type { Product } from '../types';

export const ProductsPage: React.FC = () => {
  const { addNotification } = useNotifications();
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({
    name: '',
    sku: '',
    category: 'Solar EPC',
    description: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadProducts = useCallback(async () => {
    setIsLoading(true);
    try {
      const items = await productService.getProducts({
        search: searchQuery.trim() || undefined,
      });
      setProducts(Array.isArray(items) ? items : []);
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to load products',
      });
      setProducts([]);
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, addNotification]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;

    setIsSubmitting(true);
    try {
      await productService.createProduct(form);
      addNotification({ type: 'success', message: `Product "${form.name}" added.` });
      setShowModal(false);
      setForm({ name: '', sku: '', category: 'Solar EPC', description: '' });
      loadProducts();
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to create product',
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
            <Package className="w-5 h-5 text-cyan-400" />
            Product & Service Catalog
          </h2>
          <p className="text-sm text-slate-400">
            Define standardized equipment packages and turnkey solutions.
          </p>
        </div>

        <Button
          variant="primary"
          icon={<Plus className="w-4 h-4" />}
          onClick={() => setShowModal(true)}
        >
          Add Product
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search products by title or SKU..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
        />
      </div>

      {/* Product List */}
      <Card>
        {isLoading ? (
          <div className="flex items-center justify-center p-12 text-slate-400 gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-cyan-500" />
            <span>Loading catalog...</span>
          </div>
        ) : (!products || products.length === 0) ? (
          <EmptyState
            title="No products configured"
            description="Add products to associate them with client projects and pipelines."
            actionLabel="Add Product"
            onAction={() => setShowModal(true)}
          />
        ) : (
          <div className="divide-y divide-slate-800/80">
            {(products || []).map((p) => (
              <div
                key={p.id}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-900/40 transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-200 text-sm">{p.name}</span>
                    {p.sku && (
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {p.sku}
                      </span>
                    )}
                    <Badge variant="neutral" size="sm">
                      {p.category}
                    </Badge>
                  </div>
                  {p.description && (
                    <p className="text-xs text-slate-400 max-w-2xl">{p.description}</p>
                  )}
                </div>

                <Badge variant={p.is_active ? 'success' : 'neutral'} size="sm">
                  {p.is_active ? 'Active' : 'Archived'}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* CREATE PRODUCT MODAL */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Tag className="w-5 h-5 text-cyan-400" />
                Add Product Offering
              </h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Product Title *</label>
                <input
                  type="text"
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. 50kW Commercial Solar Package"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">SKU / Code</label>
                  <input
                    type="text"
                    value={form.sku}
                    onChange={(e) => setForm({ ...form, sku: e.target.value })}
                    placeholder="ENX-SOLAR-050"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Category</label>
                  <select
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="Solar EPC">Solar EPC</option>
                    <option value="Rooftop Installation">Rooftop Installation</option>
                    <option value="Inverter Systems">Inverter Systems</option>
                    <option value="Maintenance & AMC">Maintenance & AMC</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Description</label>
                <textarea
                  rows={3}
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Specifications, scope, and technical notes..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button variant="secondary" onClick={() => setShowModal(false)} type="button">
                  Cancel
                </Button>
                <Button variant="primary" type="submit" isLoading={isSubmitting}>
                  Add Product
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
