/**
 * Violation Detail Page (Sprint 15)
 *
 * View a single violation with:
 * - Full violation details
 * - Escalation history
 * - Fines posted
 * - Photo gallery
 * - Actions: Escalate, Mark as Cured, Add Fine
 *
 * API Integration:
 * - GET /api/v1/accounting/violations/:id/
 * - POST /api/v1/accounting/violations/:id/escalate/
 * - POST /api/v1/accounting/violations/:id/mark-cured/
 * - POST /api/v1/accounting/violation-fines/
 * - GET /api/v1/accounting/violation-escalations/?violation=:id
 * - GET /api/v1/accounting/violation-fines/?violation=:id
 * - GET /api/v1/accounting/violation-photos/?violation=:id
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';

// Types
interface Violation {
  id: string;
  violation_number: string;
  owner: {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
  };
  unit: {
    id: string;
    unit_number: string;
  };
  violation_type: {
    id: string;
    code: string;
    name: string;
    category: string;
  };
  description: string;
  location: string;
  severity: string;
  status: string;
  reported_date: string;
  cure_deadline: string;
  cured_date?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface Escalation {
  id: string;
  step_number: number;
  escalation_date: string;
  fine_amount?: number;
  notes?: string;
  created_by: string;
}

interface Fine {
  id: string;
  amount: number;
  fine_date: string;
  due_date: string;
  status: string;
  invoice?: {
    id: string;
    invoice_number: string;
  };
  notes?: string;
}

interface Photo {
  id: string;
  photo_url: string;
  caption?: string;
  uploaded_date: string;
  file_size: number;
}

// API Functions
const fetchViolation = async (id: string): Promise<Violation> => {
  const response = await fetch(`/api/v1/accounting/violations/${id}/`);
  if (!response.ok) throw new Error('Failed to fetch violation');
  return response.json();
};

const fetchEscalations = async (violationId: string): Promise<Escalation[]> => {
  const response = await fetch(`/api/v1/accounting/violation-escalations/?violation=${violationId}`);
  if (!response.ok) throw new Error('Failed to fetch escalations');
  return response.json();
};

const fetchFines = async (violationId: string): Promise<Fine[]> => {
  const response = await fetch(`/api/v1/accounting/violation-fines/?violation=${violationId}`);
  if (!response.ok) throw new Error('Failed to fetch fines');
  return response.json();
};

const fetchPhotos = async (violationId: string): Promise<Photo[]> => {
  const response = await fetch(`/api/v1/accounting/violation-photos/?violation=${violationId}`);
  if (!response.ok) throw new Error('Failed to fetch photos');
  return response.json();
};

const escalateViolation = async (id: string, data: { fine_amount?: number; notes?: string }) => {
  const response = await fetch(`/api/v1/accounting/violations/${id}/escalate/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to escalate violation');
  return response.json();
};

const markCured = async (id: string, data: { cured_date: string; notes?: string }) => {
  const response = await fetch(`/api/v1/accounting/violations/${id}/mark-cured/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to mark as cured');
  return response.json();
};

const addFine = async (data: {
  violation: string;
  amount: number;
  fine_date: string;
  due_date: string;
  notes?: string;
}) => {
  const response = await fetch('/api/v1/accounting/violation-fines/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to add fine');
  return response.json();
};

export const ViolationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showEscalateModal, setShowEscalateModal] = useState(false);
  const [showCureModal, setShowCureModal] = useState(false);
  const [showFineModal, setShowFineModal] = useState(false);

  // Fetch data
  const { data: violation, isLoading } = useQuery({
    queryKey: ['violation', id],
    queryFn: () => fetchViolation(id!),
    enabled: !!id,
  });

  const { data: escalations } = useQuery({
    queryKey: ['violation-escalations', id],
    queryFn: () => fetchEscalations(id!),
    enabled: !!id,
  });

  const { data: fines } = useQuery({
    queryKey: ['violation-fines', id],
    queryFn: () => fetchFines(id!),
    enabled: !!id,
  });

  const { data: photos } = useQuery({
    queryKey: ['violation-photos', id],
    queryFn: () => fetchPhotos(id!),
    enabled: !!id,
  });

  // Mutations
  const escalateMutation = useMutation({
    mutationFn: (data: { fine_amount?: number; notes?: string }) => escalateViolation(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['violation', id] });
      queryClient.invalidateQueries({ queryKey: ['violation-escalations', id] });
      setShowEscalateModal(false);
    },
  });

  const cureMutation = useMutation({
    mutationFn: (data: { cured_date: string; notes?: string }) => markCured(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['violation', id] });
      setShowCureModal(false);
    },
  });

  const fineMutation = useMutation({
    mutationFn: addFine,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['violation-fines', id] });
      setShowFineModal(false);
    },
  });

  if (isLoading) {
    return <div className="container mx-auto p-8">Loading...</div>;
  }

  if (!violation) {
    return <div className="container mx-auto p-8">Violation not found</div>;
  }

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      minor: 'text-blue-600 bg-blue-50',
      moderate: 'text-yellow-600 bg-yellow-50',
      major: 'text-orange-600 bg-orange-50',
      critical: 'text-red-600 bg-red-50',
    };
    return colors[severity] || 'text-gray-600 bg-gray-50';
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      open: 'text-red-600 bg-red-50',
      escalated: 'text-orange-600 bg-orange-50',
      cured: 'text-green-600 bg-green-50',
      closed: 'text-gray-600 bg-gray-50',
    };
    return colors[status] || 'text-gray-600 bg-gray-50';
  };

  return (
    <div className="container mx-auto p-8 max-w-6xl">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold">{violation.violation_number}</h1>
          <p className="text-gray-600 mt-1">{violation.violation_type.name}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/violations')}
            className="px-4 py-2 border rounded hover:bg-gray-50"
          >
            Back to List
          </button>
          {violation.status === 'open' && (
            <button
              onClick={() => setShowEscalateModal(true)}
              className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
            >
              Escalate
            </button>
          )}
          {violation.status !== 'cured' && violation.status !== 'closed' && (
            <button
              onClick={() => setShowCureModal(true)}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Mark as Cured
            </button>
          )}
          <button
            onClick={() => setShowFineModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Add Fine
          </button>
        </div>
      </div>

      {/* Status and Severity Badges */}
      <div className="flex gap-2 mb-6">
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(violation.status)}`}>
          {violation.status.toUpperCase()}
        </span>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(violation.severity)}`}>
          {violation.severity.toUpperCase()}
        </span>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Violation Details */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Violation Details</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Owner</p>
                <p className="font-medium">
                  {violation.owner.first_name} {violation.owner.last_name}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Unit</p>
                <p className="font-medium">{violation.unit.unit_number}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Reported Date</p>
                <p className="font-medium">{new Date(violation.reported_date).toLocaleDateString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Cure Deadline</p>
                <p className="font-medium">{new Date(violation.cure_deadline).toLocaleDateString()}</p>
              </div>
              {violation.cured_date && (
                <div>
                  <p className="text-sm text-gray-600">Cured Date</p>
                  <p className="font-medium">{new Date(violation.cured_date).toLocaleDateString()}</p>
                </div>
              )}
            </div>
            <div className="mt-4">
              <p className="text-sm text-gray-600">Location</p>
              <p className="font-medium">{violation.location}</p>
            </div>
            <div className="mt-4">
              <p className="text-sm text-gray-600">Description</p>
              <p className="mt-1">{violation.description}</p>
            </div>
            {violation.notes && (
              <div className="mt-4">
                <p className="text-sm text-gray-600">Internal Notes</p>
                <p className="mt-1 text-sm">{violation.notes}</p>
              </div>
            )}
          </div>

          {/* Escalation History */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Escalation History</h2>
            {escalations && escalations.length > 0 ? (
              <div className="space-y-3">
                {escalations.map((escalation) => (
                  <div key={escalation.id} className="border-l-4 border-orange-500 pl-4 py-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium">Step {escalation.step_number}</p>
                        <p className="text-sm text-gray-600">
                          {new Date(escalation.escalation_date).toLocaleDateString()}
                        </p>
                      </div>
                      {escalation.fine_amount && (
                        <span className="text-red-600 font-bold">${escalation.fine_amount}</span>
                      )}
                    </div>
                    {escalation.notes && (
                      <p className="text-sm mt-1">{escalation.notes}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No escalations yet</p>
            )}
          </div>

          {/* Fines Posted */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Fines Posted</h2>
            {fines && fines.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Amount</th>
                      <th className="text-left py-2">Fine Date</th>
                      <th className="text-left py-2">Due Date</th>
                      <th className="text-left py-2">Status</th>
                      <th className="text-left py-2">Invoice</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fines.map((fine) => (
                      <tr key={fine.id} className="border-b">
                        <td className="py-2 font-bold text-red-600">${fine.amount}</td>
                        <td className="py-2">{new Date(fine.fine_date).toLocaleDateString()}</td>
                        <td className="py-2">{new Date(fine.due_date).toLocaleDateString()}</td>
                        <td className="py-2">
                          <span className={`px-2 py-1 rounded text-xs ${
                            fine.status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {fine.status}
                          </span>
                        </td>
                        <td className="py-2">
                          {fine.invoice ? (
                            <a href={`/invoices/${fine.invoice.id}`} className="text-blue-600 hover:underline">
                              {fine.invoice.invoice_number}
                            </a>
                          ) : (
                            <span className="text-gray-400">Pending</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500">No fines posted</p>
            )}
          </div>
        </div>

        {/* Right Column - Photos */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Photo Evidence</h2>
            {photos && photos.length > 0 ? (
              <div className="grid grid-cols-1 gap-4">
                {photos.map((photo) => (
                  <div key={photo.id} className="border rounded overflow-hidden">
                    <img
                      src={photo.photo_url}
                      alt={photo.caption || 'Violation photo'}
                      className="w-full h-48 object-cover"
                    />
                    {photo.caption && (
                      <div className="p-2 bg-gray-50">
                        <p className="text-sm">{photo.caption}</p>
                      </div>
                    )}
                    <div className="p-2 bg-gray-50 border-t text-xs text-gray-600">
                      {new Date(photo.uploaded_date).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No photos uploaded</p>
            )}
          </div>
        </div>
      </div>

      {/* Escalate Modal */}
      {showEscalateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Escalate Violation</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                escalateMutation.mutate({
                  fine_amount: formData.get('fine_amount') ? Number(formData.get('fine_amount')) : undefined,
                  notes: formData.get('notes') as string || undefined,
                });
              }}
            >
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">Fine Amount (Optional)</label>
                <input
                  type="number"
                  name="fine_amount"
                  step="0.01"
                  className="w-full border rounded px-3 py-2"
                  placeholder="0.00"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">Notes</label>
                <textarea
                  name="notes"
                  rows={3}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Escalation notes..."
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowEscalateModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={escalateMutation.isPending}
                  className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:bg-gray-400"
                >
                  {escalateMutation.isPending ? 'Escalating...' : 'Escalate'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Mark as Cured Modal */}
      {showCureModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Mark as Cured</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                cureMutation.mutate({
                  cured_date: formData.get('cured_date') as string,
                  notes: formData.get('notes') as string || undefined,
                });
              }}
            >
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Cured Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  name="cured_date"
                  required
                  defaultValue={new Date().toISOString().split('T')[0]}
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">Notes</label>
                <textarea
                  name="notes"
                  rows={3}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Resolution notes..."
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCureModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={cureMutation.isPending}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
                >
                  {cureMutation.isPending ? 'Saving...' : 'Mark as Cured'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Fine Modal */}
      {showFineModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Add Fine</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                fineMutation.mutate({
                  violation: id!,
                  amount: Number(formData.get('amount')),
                  fine_date: formData.get('fine_date') as string,
                  due_date: formData.get('due_date') as string,
                  notes: formData.get('notes') as string || undefined,
                });
              }}
            >
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Amount <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="amount"
                  step="0.01"
                  required
                  className="w-full border rounded px-3 py-2"
                  placeholder="0.00"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Fine Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  name="fine_date"
                  required
                  defaultValue={new Date().toISOString().split('T')[0]}
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Due Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  name="due_date"
                  required
                  defaultValue={new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">Notes</label>
                <textarea
                  name="notes"
                  rows={3}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Fine notes..."
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowFineModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={fineMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {fineMutation.isPending ? 'Adding...' : 'Add Fine'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ViolationDetailPage;
