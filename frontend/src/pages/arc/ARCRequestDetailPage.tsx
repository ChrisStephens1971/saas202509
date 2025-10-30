/**
 * ARC Request Detail Page (Sprint 15)
 *
 * View and review an ARC request with:
 * - Full request details
 * - Document gallery
 * - Review history
 * - Committee comments
 * - Actions: Approve, Deny, Request Changes, Add Conditions
 *
 * API Integration:
 * - GET /api/v1/accounting/arc-requests/:id/
 * - POST /api/v1/accounting/arc-requests/:id/approve/
 * - POST /api/v1/accounting/arc-requests/:id/deny/
 * - POST /api/v1/accounting/arc-requests/:id/request-changes/
 * - POST /api/v1/accounting/arc-request-reviews/
 * - GET /api/v1/accounting/arc-request-reviews/?arc_request=:id
 * - GET /api/v1/accounting/arc-documents/?arc_request=:id
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';

// Types
interface ARCRequest {
  id: string;
  request_number: string;
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
  request_type: {
    id: string;
    code: string;
    name: string;
    category: string;
    requires_deposit: boolean;
    deposit_amount?: number;
  };
  project_description: string;
  estimated_cost?: number;
  estimated_start_date?: string;
  estimated_completion_date?: string;
  contractor_name?: string;
  contractor_license?: string;
  status: string;
  submission_date: string;
  review_date?: string;
  approval_date?: string;
  denial_date?: string;
  conditions?: string;
  denial_reason?: string;
  notes?: string;
}

interface Review {
  id: string;
  reviewer_name: string;
  review_date: string;
  decision: string;
  comments?: string;
  conditions?: string;
}

interface Document {
  id: string;
  document_type: string;
  file_url: string;
  file_name: string;
  file_size: number;
  upload_date: string;
}

// API Functions
const fetchARCRequest = async (id: string): Promise<ARCRequest> => {
  const response = await fetch(`/api/v1/accounting/arc-requests/${id}/`);
  if (!response.ok) throw new Error('Failed to fetch ARC request');
  return response.json();
};

const fetchReviews = async (arcRequestId: string): Promise<Review[]> => {
  const response = await fetch(`/api/v1/accounting/arc-request-reviews/?arc_request=${arcRequestId}`);
  if (!response.ok) throw new Error('Failed to fetch reviews');
  return response.json();
};

const fetchDocuments = async (arcRequestId: string): Promise<Document[]> => {
  const response = await fetch(`/api/v1/accounting/arc-documents/?arc_request=${arcRequestId}`);
  if (!response.ok) throw new Error('Failed to fetch documents');
  return response.json();
};

const approveRequest = async (id: string, data: { conditions?: string; comments?: string }) => {
  const response = await fetch(`/api/v1/accounting/arc-requests/${id}/approve/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to approve request');
  return response.json();
};

const denyRequest = async (id: string, data: { denial_reason: string; comments?: string }) => {
  const response = await fetch(`/api/v1/accounting/arc-requests/${id}/deny/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to deny request');
  return response.json();
};

const requestChanges = async (id: string, data: { requested_changes: string; comments?: string }) => {
  const response = await fetch(`/api/v1/accounting/arc-requests/${id}/request-changes/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to request changes');
  return response.json();
};

export const ARCRequestDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showApproveModal, setShowApproveModal] = useState(false);
  const [showDenyModal, setShowDenyModal] = useState(false);
  const [showChangesModal, setShowChangesModal] = useState(false);

  // Fetch data
  const { data: arcRequest, isLoading } = useQuery({
    queryKey: ['arc-request', id],
    queryFn: () => fetchARCRequest(id!),
    enabled: !!id,
  });

  const { data: reviews } = useQuery({
    queryKey: ['arc-request-reviews', id],
    queryFn: () => fetchReviews(id!),
    enabled: !!id,
  });

  const { data: documents } = useQuery({
    queryKey: ['arc-documents', id],
    queryFn: () => fetchDocuments(id!),
    enabled: !!id,
  });

  // Mutations
  const approveMutation = useMutation({
    mutationFn: (data: { conditions?: string; comments?: string }) => approveRequest(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['arc-request', id] });
      queryClient.invalidateQueries({ queryKey: ['arc-request-reviews', id] });
      setShowApproveModal(false);
    },
  });

  const denyMutation = useMutation({
    mutationFn: (data: { denial_reason: string; comments?: string }) => denyRequest(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['arc-request', id] });
      queryClient.invalidateQueries({ queryKey: ['arc-request-reviews', id] });
      setShowDenyModal(false);
    },
  });

  const changesMutation = useMutation({
    mutationFn: (data: { requested_changes: string; comments?: string }) => requestChanges(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['arc-request', id] });
      queryClient.invalidateQueries({ queryKey: ['arc-request-reviews', id] });
      setShowChangesModal(false);
    },
  });

  if (isLoading) {
    return <div className="container mx-auto p-8">Loading...</div>;
  }

  if (!arcRequest) {
    return <div className="container mx-auto p-8">ARC request not found</div>;
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'text-gray-600 bg-gray-50',
      submitted: 'text-blue-600 bg-blue-50',
      under_review: 'text-purple-600 bg-purple-50',
      approved: 'text-green-600 bg-green-50',
      conditional_approval: 'text-yellow-600 bg-yellow-50',
      denied: 'text-red-600 bg-red-50',
      changes_requested: 'text-orange-600 bg-orange-50',
      withdrawn: 'text-gray-600 bg-gray-50',
    };
    return colors[status] || 'text-gray-600 bg-gray-50';
  };

  const groupedDocuments = documents?.reduce((acc, doc) => {
    if (!acc[doc.document_type]) {
      acc[doc.document_type] = [];
    }
    acc[doc.document_type].push(doc);
    return acc;
  }, {} as Record<string, Document[]>);

  return (
    <div className="container mx-auto p-8 max-w-6xl">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold">{arcRequest.request_number}</h1>
          <p className="text-gray-600 mt-1">{arcRequest.request_type.name}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/arc-requests')}
            className="px-4 py-2 border rounded hover:bg-gray-50"
          >
            Back to List
          </button>
          {(arcRequest.status === 'submitted' || arcRequest.status === 'under_review') && (
            <>
              <button
                onClick={() => setShowApproveModal(true)}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Approve
              </button>
              <button
                onClick={() => setShowChangesModal(true)}
                className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
              >
                Request Changes
              </button>
              <button
                onClick={() => setShowDenyModal(true)}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Deny
              </button>
            </>
          )}
        </div>
      </div>

      {/* Status Badge */}
      <div className="mb-6">
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(arcRequest.status)}`}>
          {arcRequest.status.toUpperCase().replace('_', ' ')}
        </span>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Request Details */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Request Details</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Owner</p>
                <p className="font-medium">
                  {arcRequest.owner.first_name} {arcRequest.owner.last_name}
                </p>
                <p className="text-sm text-gray-600">{arcRequest.owner.email}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Unit</p>
                <p className="font-medium">{arcRequest.unit.unit_number}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Submission Date</p>
                <p className="font-medium">{new Date(arcRequest.submission_date).toLocaleDateString()}</p>
              </div>
              {arcRequest.review_date && (
                <div>
                  <p className="text-sm text-gray-600">Review Date</p>
                  <p className="font-medium">{new Date(arcRequest.review_date).toLocaleDateString()}</p>
                </div>
              )}
              {arcRequest.estimated_cost && (
                <div>
                  <p className="text-sm text-gray-600">Estimated Cost</p>
                  <p className="font-medium">${arcRequest.estimated_cost}</p>
                </div>
              )}
              {arcRequest.estimated_start_date && (
                <div>
                  <p className="text-sm text-gray-600">Est. Start Date</p>
                  <p className="font-medium">{new Date(arcRequest.estimated_start_date).toLocaleDateString()}</p>
                </div>
              )}
            </div>

            {/* Deposit Notice */}
            {arcRequest.request_type.requires_deposit && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                <p className="text-sm text-yellow-900">
                  <strong>Deposit Required:</strong> ${arcRequest.request_type.deposit_amount} refundable deposit
                </p>
              </div>
            )}

            {/* Project Description */}
            <div className="mt-4">
              <p className="text-sm text-gray-600 mb-2">Project Description</p>
              <p className="whitespace-pre-wrap">{arcRequest.project_description}</p>
            </div>

            {/* Contractor Info */}
            {arcRequest.contractor_name && (
              <div className="mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600 mb-2">Contractor Information</p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Name</p>
                    <p className="font-medium">{arcRequest.contractor_name}</p>
                  </div>
                  {arcRequest.contractor_license && (
                    <div>
                      <p className="text-sm text-gray-600">License</p>
                      <p className="font-medium">{arcRequest.contractor_license}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Conditions or Denial Reason */}
            {arcRequest.conditions && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                <p className="font-bold text-yellow-900 mb-2">Conditions for Approval:</p>
                <p className="text-sm text-yellow-900 whitespace-pre-wrap">{arcRequest.conditions}</p>
              </div>
            )}

            {arcRequest.denial_reason && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
                <p className="font-bold text-red-900 mb-2">Denial Reason:</p>
                <p className="text-sm text-red-900 whitespace-pre-wrap">{arcRequest.denial_reason}</p>
              </div>
            )}
          </div>

          {/* Review History */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Review History</h2>
            {reviews && reviews.length > 0 ? (
              <div className="space-y-4">
                {reviews.map((review) => (
                  <div key={review.id} className="border-l-4 border-blue-500 pl-4 py-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium">{review.reviewer_name}</p>
                        <p className="text-sm text-gray-600">
                          {new Date(review.review_date).toLocaleString()}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        review.decision === 'approved' ? 'bg-green-100 text-green-800' :
                        review.decision === 'denied' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {review.decision.toUpperCase()}
                      </span>
                    </div>
                    {review.comments && (
                      <p className="mt-2 text-sm">{review.comments}</p>
                    )}
                    {review.conditions && (
                      <div className="mt-2 p-2 bg-yellow-50 rounded">
                        <p className="text-sm font-medium text-yellow-900">Conditions:</p>
                        <p className="text-sm text-yellow-900">{review.conditions}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No reviews yet</p>
            )}
          </div>
        </div>

        {/* Right Column - Documents */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Documents</h2>
            {groupedDocuments && Object.keys(groupedDocuments).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(groupedDocuments).map(([type, docs]) => (
                  <div key={type}>
                    <h3 className="font-medium text-sm text-gray-700 mb-2">
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </h3>
                    <div className="space-y-2">
                      {docs.map((doc) => (
                        <a
                          key={doc.id}
                          href={doc.file_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block border rounded p-2 hover:bg-gray-50"
                        >
                          <div className="flex items-start gap-2">
                            {doc.file_url.match(/\.(jpg|jpeg|png|gif)$/i) ? (
                              <img
                                src={doc.file_url}
                                alt={doc.file_name}
                                className="w-12 h-12 object-cover rounded flex-shrink-0"
                              />
                            ) : (
                              <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center flex-shrink-0">
                                <span className="text-xs font-bold text-gray-600">
                                  {doc.file_name.split('.').pop()?.toUpperCase()}
                                </span>
                              </div>
                            )}
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">{doc.file_name}</p>
                              <p className="text-xs text-gray-600">
                                {(doc.file_size / 1024).toFixed(1)} KB
                              </p>
                            </div>
                          </div>
                        </a>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No documents attached</p>
            )}
          </div>
        </div>
      </div>

      {/* Approve Modal */}
      {showApproveModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Approve Request</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                approveMutation.mutate({
                  conditions: formData.get('conditions') as string || undefined,
                  comments: formData.get('comments') as string || undefined,
                });
              }}
            >
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Conditions (Optional)
                </label>
                <textarea
                  name="conditions"
                  rows={3}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Any conditions for approval..."
                />
                <p className="text-xs text-gray-600 mt-1">
                  Leave blank for unconditional approval
                </p>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Comments
                </label>
                <textarea
                  name="comments"
                  rows={3}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Committee comments..."
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowApproveModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={approveMutation.isPending}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
                >
                  {approveMutation.isPending ? 'Approving...' : 'Approve Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Deny Modal */}
      {showDenyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Deny Request</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                denyMutation.mutate({
                  denial_reason: formData.get('denial_reason') as string,
                  comments: formData.get('comments') as string || undefined,
                });
              }}
            >
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Reason for Denial <span className="text-red-500">*</span>
                </label>
                <textarea
                  name="denial_reason"
                  required
                  rows={4}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Explain why the request is being denied..."
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Additional Comments
                </label>
                <textarea
                  name="comments"
                  rows={2}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Committee comments..."
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowDenyModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={denyMutation.isPending}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:bg-gray-400"
                >
                  {denyMutation.isPending ? 'Denying...' : 'Deny Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Request Changes Modal */}
      {showChangesModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Request Changes</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                changesMutation.mutate({
                  requested_changes: formData.get('requested_changes') as string,
                  comments: formData.get('comments') as string || undefined,
                });
              }}
            >
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Requested Changes <span className="text-red-500">*</span>
                </label>
                <textarea
                  name="requested_changes"
                  required
                  rows={4}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Describe what changes are needed..."
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Additional Comments
                </label>
                <textarea
                  name="comments"
                  rows={2}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Committee comments..."
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowChangesModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={changesMutation.isPending}
                  className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:bg-gray-400"
                >
                  {changesMutation.isPending ? 'Sending...' : 'Request Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ARCRequestDetailPage;
