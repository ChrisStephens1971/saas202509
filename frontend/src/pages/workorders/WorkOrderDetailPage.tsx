/**
 * Work Order Detail Page (Sprint 15)
 *
 * View a single work order with:
 * - Full work order details
 * - Status timeline
 * - Comments/updates
 * - Attachments
 * - Actions: Update status, Add comment, Complete work order
 *
 * API Integration:
 * - GET /api/v1/accounting/work-orders/:id/
 * - POST /api/v1/accounting/work-orders/:id/update-status/
 * - POST /api/v1/accounting/work-orders/:id/add-comment/
 * - POST /api/v1/accounting/work-orders/:id/complete/
 * - GET /api/v1/accounting/work-order-comments/?work_order=:id
 * - GET /api/v1/accounting/work-order-attachments/?work_order=:id
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';

// Types
interface WorkOrder {
  id: string;
  work_order_number: string;
  title: string;
  description: string;
  category: {
    id: string;
    name: string;
  };
  priority: string;
  status: string;
  location_type: string;
  unit?: {
    id: string;
    unit_number: string;
  };
  location_description: string;
  estimated_cost?: number;
  actual_cost?: number;
  assigned_to_vendor?: {
    id: string;
    name: string;
    contact_name: string;
    phone: string;
    email: string;
  };
  created_date: string;
  scheduled_date?: string;
  started_date?: string;
  completed_date?: string;
  closed_date?: string;
  notes?: string;
}

interface Comment {
  id: string;
  comment: string;
  comment_type: string;
  created_by: string;
  created_at: string;
  is_internal: boolean;
}

interface Attachment {
  id: string;
  file_url: string;
  file_name: string;
  file_size: number;
  file_type: string;
  uploaded_date: string;
  uploaded_by: string;
}

// API Functions
const fetchWorkOrder = async (id: string): Promise<WorkOrder> => {
  const response = await fetch(`/api/v1/accounting/work-orders/${id}/`);
  if (!response.ok) throw new Error('Failed to fetch work order');
  return response.json();
};

const fetchComments = async (workOrderId: string): Promise<Comment[]> => {
  const response = await fetch(`/api/v1/accounting/work-order-comments/?work_order=${workOrderId}`);
  if (!response.ok) throw new Error('Failed to fetch comments');
  return response.json();
};

const fetchAttachments = async (workOrderId: string): Promise<Attachment[]> => {
  const response = await fetch(`/api/v1/accounting/work-order-attachments/?work_order=${workOrderId}`);
  if (!response.ok) throw new Error('Failed to fetch attachments');
  return response.json();
};

const updateStatus = async (id: string, data: { status: string; notes?: string }) => {
  const response = await fetch(`/api/v1/accounting/work-orders/${id}/update-status/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to update status');
  return response.json();
};

const addComment = async (id: string, data: { comment: string; comment_type: string; is_internal: boolean }) => {
  const response = await fetch(`/api/v1/accounting/work-orders/${id}/add-comment/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to add comment');
  return response.json();
};

const completeWorkOrder = async (id: string, data: { actual_cost?: number; completion_notes?: string }) => {
  const response = await fetch(`/api/v1/accounting/work-orders/${id}/complete/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to complete work order');
  return response.json();
};

export const WorkOrderDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showCommentModal, setShowCommentModal] = useState(false);
  const [showCompleteModal, setShowCompleteModal] = useState(false);

  // Fetch data
  const { data: workOrder, isLoading } = useQuery({
    queryKey: ['work-order', id],
    queryFn: () => fetchWorkOrder(id!),
    enabled: !!id,
  });

  const { data: comments } = useQuery({
    queryKey: ['work-order-comments', id],
    queryFn: () => fetchComments(id!),
    enabled: !!id,
  });

  const { data: attachments } = useQuery({
    queryKey: ['work-order-attachments', id],
    queryFn: () => fetchAttachments(id!),
    enabled: !!id,
  });

  // Mutations
  const statusMutation = useMutation({
    mutationFn: (data: { status: string; notes?: string }) => updateStatus(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-order', id] });
      queryClient.invalidateQueries({ queryKey: ['work-order-comments', id] });
      setShowStatusModal(false);
    },
  });

  const commentMutation = useMutation({
    mutationFn: (data: { comment: string; comment_type: string; is_internal: boolean }) => addComment(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-order-comments', id] });
      setShowCommentModal(false);
    },
  });

  const completeMutation = useMutation({
    mutationFn: (data: { actual_cost?: number; completion_notes?: string }) => completeWorkOrder(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-order', id] });
      setShowCompleteModal(false);
    },
  });

  if (isLoading) {
    return <div className="container mx-auto p-8">Loading...</div>;
  }

  if (!workOrder) {
    return <div className="container mx-auto p-8">Work order not found</div>;
  }

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: 'text-gray-600 bg-gray-50',
      medium: 'text-blue-600 bg-blue-50',
      high: 'text-orange-600 bg-orange-50',
      emergency: 'text-red-600 bg-red-50',
    };
    return colors[priority] || 'text-gray-600 bg-gray-50';
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'text-gray-600 bg-gray-50',
      pending: 'text-yellow-600 bg-yellow-50',
      assigned: 'text-blue-600 bg-blue-50',
      in_progress: 'text-purple-600 bg-purple-50',
      completed: 'text-green-600 bg-green-50',
      closed: 'text-gray-600 bg-gray-50',
      cancelled: 'text-red-600 bg-red-50',
    };
    return colors[status] || 'text-gray-600 bg-gray-50';
  };

  return (
    <div className="container mx-auto p-8 max-w-6xl">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold">{workOrder.work_order_number}</h1>
          <p className="text-gray-600 mt-1">{workOrder.title}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/work-orders')}
            className="px-4 py-2 border rounded hover:bg-gray-50"
          >
            Back to List
          </button>
          {workOrder.status !== 'completed' && workOrder.status !== 'closed' && workOrder.status !== 'cancelled' && (
            <>
              <button
                onClick={() => setShowStatusModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Update Status
              </button>
              <button
                onClick={() => setShowCompleteModal(true)}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Complete
              </button>
            </>
          )}
          <button
            onClick={() => setShowCommentModal(true)}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Add Comment
          </button>
        </div>
      </div>

      {/* Status and Priority Badges */}
      <div className="flex gap-2 mb-6">
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(workOrder.status)}`}>
          {workOrder.status.toUpperCase().replace('_', ' ')}
        </span>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(workOrder.priority)}`}>
          {workOrder.priority.toUpperCase()}
        </span>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Work Order Details */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Work Order Details</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Category</p>
                <p className="font-medium">{workOrder.category.name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Location Type</p>
                <p className="font-medium">{workOrder.location_type.replace('_', ' ').toUpperCase()}</p>
              </div>
              {workOrder.unit && (
                <div>
                  <p className="text-sm text-gray-600">Unit</p>
                  <p className="font-medium">{workOrder.unit.unit_number}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-gray-600">Location</p>
                <p className="font-medium">{workOrder.location_description}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Created Date</p>
                <p className="font-medium">{new Date(workOrder.created_date).toLocaleDateString()}</p>
              </div>
              {workOrder.scheduled_date && (
                <div>
                  <p className="text-sm text-gray-600">Scheduled Date</p>
                  <p className="font-medium">{new Date(workOrder.scheduled_date).toLocaleDateString()}</p>
                </div>
              )}
              {workOrder.started_date && (
                <div>
                  <p className="text-sm text-gray-600">Started Date</p>
                  <p className="font-medium">{new Date(workOrder.started_date).toLocaleDateString()}</p>
                </div>
              )}
              {workOrder.completed_date && (
                <div>
                  <p className="text-sm text-gray-600">Completed Date</p>
                  <p className="font-medium">{new Date(workOrder.completed_date).toLocaleDateString()}</p>
                </div>
              )}
            </div>
            <div className="mt-4">
              <p className="text-sm text-gray-600">Description</p>
              <p className="mt-1">{workOrder.description}</p>
            </div>
            {workOrder.notes && (
              <div className="mt-4">
                <p className="text-sm text-gray-600">Internal Notes</p>
                <p className="mt-1 text-sm">{workOrder.notes}</p>
              </div>
            )}
          </div>

          {/* Vendor and Cost */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Vendor & Cost</h2>
            {workOrder.assigned_to_vendor ? (
              <div className="space-y-2">
                <div>
                  <p className="text-sm text-gray-600">Vendor</p>
                  <p className="font-medium text-lg">{workOrder.assigned_to_vendor.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Contact</p>
                  <p>{workOrder.assigned_to_vendor.contact_name}</p>
                  <p className="text-sm">{workOrder.assigned_to_vendor.phone}</p>
                  <p className="text-sm text-blue-600">{workOrder.assigned_to_vendor.email}</p>
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No vendor assigned</p>
            )}
            <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t">
              <div>
                <p className="text-sm text-gray-600">Estimated Cost</p>
                <p className="font-bold text-lg">${workOrder.estimated_cost || '0.00'}</p>
              </div>
              {workOrder.actual_cost && (
                <div>
                  <p className="text-sm text-gray-600">Actual Cost</p>
                  <p className="font-bold text-lg text-green-600">${workOrder.actual_cost}</p>
                </div>
              )}
            </div>
          </div>

          {/* Comments/Updates */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Comments & Updates</h2>
            {comments && comments.length > 0 ? (
              <div className="space-y-4">
                {comments.map((comment) => (
                  <div key={comment.id} className="border-l-4 border-blue-500 pl-4 py-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium">{comment.created_by}</p>
                        <p className="text-sm text-gray-600">
                          {new Date(comment.created_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <span className="text-xs px-2 py-1 rounded bg-gray-100">
                          {comment.comment_type}
                        </span>
                        {comment.is_internal && (
                          <span className="text-xs px-2 py-1 rounded bg-yellow-100 text-yellow-800">
                            INTERNAL
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="mt-2">{comment.comment}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No comments yet</p>
            )}
          </div>
        </div>

        {/* Right Column - Attachments */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Attachments</h2>
            {attachments && attachments.length > 0 ? (
              <div className="space-y-3">
                {attachments.map((attachment) => (
                  <a
                    key={attachment.id}
                    href={attachment.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block border rounded p-3 hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-2">
                      <div className="flex-shrink-0">
                        {attachment.file_type.startsWith('image/') ? (
                          <img
                            src={attachment.file_url}
                            alt={attachment.file_name}
                            className="w-12 h-12 object-cover rounded"
                          />
                        ) : (
                          <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
                            <span className="text-xs font-bold text-gray-600">
                              {attachment.file_type.split('/')[1].toUpperCase()}
                            </span>
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{attachment.file_name}</p>
                        <p className="text-xs text-gray-600">
                          {(attachment.file_size / 1024).toFixed(1)} KB
                        </p>
                        <p className="text-xs text-gray-600">
                          {new Date(attachment.uploaded_date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No attachments</p>
            )}
          </div>
        </div>
      </div>

      {/* Update Status Modal */}
      {showStatusModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Update Status</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                statusMutation.mutate({
                  status: formData.get('status') as string,
                  notes: formData.get('notes') as string || undefined,
                });
              }}
            >
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  New Status <span className="text-red-500">*</span>
                </label>
                <select name="status" required className="w-full border rounded px-3 py-2">
                  <option value="">Select Status...</option>
                  <option value="pending">Pending</option>
                  <option value="assigned">Assigned</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">Notes</label>
                <textarea
                  name="notes"
                  rows={3}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Status update notes..."
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowStatusModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={statusMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {statusMutation.isPending ? 'Updating...' : 'Update Status'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Comment Modal */}
      {showCommentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Add Comment</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                commentMutation.mutate({
                  comment: formData.get('comment') as string,
                  comment_type: formData.get('comment_type') as string,
                  is_internal: formData.get('is_internal') === 'on',
                });
              }}
            >
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Comment <span className="text-red-500">*</span>
                </label>
                <textarea
                  name="comment"
                  required
                  rows={4}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Add a comment or update..."
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Type <span className="text-red-500">*</span>
                </label>
                <select name="comment_type" required className="w-full border rounded px-3 py-2">
                  <option value="general">General</option>
                  <option value="status_update">Status Update</option>
                  <option value="issue">Issue</option>
                  <option value="resolution">Resolution</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="flex items-center">
                  <input type="checkbox" name="is_internal" className="mr-2" />
                  <span className="text-sm">Internal only (not visible to vendor)</span>
                </label>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCommentModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={commentMutation.isPending}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:bg-gray-400"
                >
                  {commentMutation.isPending ? 'Adding...' : 'Add Comment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Complete Work Order Modal */}
      {showCompleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Complete Work Order</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                completeMutation.mutate({
                  actual_cost: formData.get('actual_cost') ? Number(formData.get('actual_cost')) : undefined,
                  completion_notes: formData.get('completion_notes') as string || undefined,
                });
              }}
            >
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Actual Cost <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="actual_cost"
                  step="0.01"
                  required
                  defaultValue={workOrder.estimated_cost}
                  className="w-full border rounded px-3 py-2"
                  placeholder="0.00"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">Completion Notes</label>
                <textarea
                  name="completion_notes"
                  rows={3}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Work completed notes..."
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCompleteModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={completeMutation.isPending}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
                >
                  {completeMutation.isPending ? 'Completing...' : 'Complete Work Order'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkOrderDetailPage;
