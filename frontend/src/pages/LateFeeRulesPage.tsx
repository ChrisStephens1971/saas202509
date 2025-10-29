/**
 * Late Fee Rules Page
 *
 * Configure and manage late fee rules
 */

import { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, AlertCircle } from 'lucide-react';
import {
  getLateFeeRules,
  createLateFeeRule,
  updateLateFeeRule,
  deleteLateFeeRule,
  LateFeeRule
} from '../api/delinquency';

export default function LateFeeRulesPage() {
  const [rules, setRules] = useState<LateFeeRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingRule, setEditingRule] = useState<LateFeeRule | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    grace_period_days: '10',
    fee_type: 'flat' as 'flat' | 'percentage' | 'both',
    flat_amount: '25.00',
    percentage_rate: '5.00',
    max_amount: '',
    is_recurring: false,
    is_active: true,
  });

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      setLoading(true);
      const data = await getLateFeeRules();
      setRules(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load late fee rules');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingRule(null);
    setFormData({
      name: '',
      grace_period_days: '10',
      fee_type: 'flat',
      flat_amount: '25.00',
      percentage_rate: '5.00',
      max_amount: '',
      is_recurring: false,
      is_active: true,
    });
    setShowModal(true);
  };

  const handleEdit = (rule: LateFeeRule) => {
    setEditingRule(rule);
    setFormData({
      name: rule.name,
      grace_period_days: rule.grace_period_days.toString(),
      fee_type: rule.fee_type,
      flat_amount: rule.flat_amount,
      percentage_rate: rule.percentage_rate,
      max_amount: rule.max_amount || '',
      is_recurring: rule.is_recurring,
      is_active: rule.is_active,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        grace_period_days: parseInt(formData.grace_period_days),
      };

      if (editingRule) {
        await updateLateFeeRule(editingRule.id, data);
      } else {
        await createLateFeeRule(data);
      }

      setShowModal(false);
      loadRules();
    } catch (err: any) {
      alert(err.message || 'Failed to save late fee rule');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this late fee rule?')) return;

    try {
      await deleteLateFeeRule(id);
      loadRules();
    } catch (err: any) {
      alert(err.message || 'Failed to delete late fee rule');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading late fee rules...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center gap-2 text-red-800">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Late Fee Rules</h1>
          <p className="text-gray-600 mt-1">Configure late fee policies</p>
        </div>
        <button
          onClick={handleCreate}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus className="h-5 w-5" />
          Add Rule
        </button>
      </div>

      {/* Rules Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grace Period</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fee Amount</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recurring</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {rules.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                  No late fee rules configured. Click "Add Rule" to create one.
                </td>
              </tr>
            ) : (
              rules.map((rule) => (
                <tr key={rule.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">{rule.name}</td>
                  <td className="px-6 py-4 text-gray-900">{rule.grace_period_days} days</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                      {rule.fee_type_display}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-900">
                    {rule.fee_type === 'flat' && `$${parseFloat(rule.flat_amount).toFixed(2)}`}
                    {rule.fee_type === 'percentage' && `${parseFloat(rule.percentage_rate).toFixed(2)}%`}
                    {rule.fee_type === 'both' && `$${parseFloat(rule.flat_amount).toFixed(2)} + ${parseFloat(rule.percentage_rate).toFixed(2)}%`}
                  </td>
                  <td className="px-6 py-4">
                    {rule.is_recurring ? (
                      <span className="text-green-600 font-semibold">Yes</span>
                    ) : (
                      <span className="text-gray-500">No</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {rule.is_active ? (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button
                      onClick={() => handleEdit(rule)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      <Edit className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleDelete(rule.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              {editingRule ? 'Edit Late Fee Rule' : 'Add Late Fee Rule'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rule Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Standard Late Fee"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Grace Period (days)</label>
                <input
                  type="number"
                  required
                  min="0"
                  value={formData.grace_period_days}
                  onChange={(e) => setFormData({ ...formData, grace_period_days: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fee Type</label>
                <select
                  value={formData.fee_type}
                  onChange={(e) => setFormData({ ...formData, fee_type: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="flat">Flat Amount</option>
                  <option value="percentage">Percentage</option>
                  <option value="both">Both (Flat + Percentage)</option>
                </select>
              </div>

              {(formData.fee_type === 'flat' || formData.fee_type === 'both') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Flat Amount ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.flat_amount}
                    onChange={(e) => setFormData({ ...formData, flat_amount: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}

              {(formData.fee_type === 'percentage' || formData.fee_type === 'both') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Percentage Rate (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.percentage_rate}
                    onChange={(e) => setFormData({ ...formData, percentage_rate: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Amount (optional)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.max_amount}
                  onChange={(e) => setFormData({ ...formData, max_amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Leave empty for no cap"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_recurring"
                  checked={formData.is_recurring}
                  onChange={(e) => setFormData({ ...formData, is_recurring: e.target.checked })}
                  className="rounded border-gray-300"
                />
                <label htmlFor="is_recurring" className="text-sm text-gray-700">Recurring (assess monthly)</label>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="rounded border-gray-300"
                />
                <label htmlFor="is_active" className="text-sm text-gray-700">Active</label>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
                >
                  {editingRule ? 'Update' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 bg-gray-200 text-gray-800 py-2 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
