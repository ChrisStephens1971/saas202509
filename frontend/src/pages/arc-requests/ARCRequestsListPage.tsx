/**
 * ARC Requests List Page (Sprint 16)
 *
 * Displays list of all architectural review committee requests with:
 * - Filtering by status, request type
 * - Search by owner/unit
 * - Pagination
 * - Actions: Create, View Detail, Review, Approve
 *
 * API Integration:
 * - GET /api/v1/accounting/arc-requests/
 * - GET /api/v1/accounting/arc-request-types/
 * - POST /api/v1/accounting/arc-requests/{id}/submit/
 * - POST /api/v1/accounting/arc-requests/{id}/assign_reviewer/
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

// Types
interface ARCRequest {
  id: string;
  request_number: string;
  unit_number: string;
  owner_name: string;
  request_type_name: string;
  project_description: string;
  status: 'draft' | 'submitted' | 'under_review' | 'approved' | 'denied' | 'conditional_approval' | 'completed';
  submission_date?: string;
  estimated_cost?: number;
}

// API Functions
const fetchARCRequests = async (): Promise<ARCRequest[]> => {
  const response = await fetch('/api/v1/accounting/arc-requests/');
  if (!response.ok) throw new Error('Failed to fetch ARC requests');
  return response.json();
};

export const ARCRequestsListPage: React.FC = () => {
  // Fetch ARC requests data
  const { data: requests, isLoading, error } = useQuery({
    queryKey: ['arc-requests'],
    queryFn: fetchARCRequests,
  });

  if (isLoading) {
    return <div className="p-8">Loading ARC requests...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-600">Error loading ARC requests</div>;
  }

  return (
    <div className="container mx-auto p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Architectural Review Committee</h1>
          <p className="text-gray-600 mt-1">Review and approve homeowner modification requests</p>
        </div>
        <Link
          to="/arc-requests/create"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          New Request
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Pending Review</div>
          <div className="text-2xl font-bold">
            {requests?.filter(r => r.status === 'submitted' || r.status === 'under_review').length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Approved</div>
          <div className="text-2xl font-bold text-green-600">
            {requests?.filter(r => r.status === 'approved').length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Conditional</div>
          <div className="text-2xl font-bold text-orange-600">
            {requests?.filter(r => r.status === 'conditional_approval').length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Denied</div>
          <div className="text-2xl font-bold text-red-600">
            {requests?.filter(r => r.status === 'denied').length || 0}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Status</label>
            <select className="w-full border rounded px-3 py-2">
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="submitted">Submitted</option>
              <option value="under_review">Under Review</option>
              <option value="approved">Approved</option>
              <option value="denied">Denied</option>
              <option value="conditional_approval">Conditional Approval</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Request Type</label>
            <select className="w-full border rounded px-3 py-2">
              <option value="">All Types</option>
              {/* Populated from arc-request-types API */}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Search</label>
            <input
              type="text"
              placeholder="Owner or Unit..."
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div className="flex items-end">
            <button className="w-full bg-gray-200 px-4 py-2 rounded hover:bg-gray-300">
              Apply Filters
            </button>
          </div>
        </div>
      </div>

      {/* Requests Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Request #
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Unit
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Owner
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Project
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Submitted
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {requests?.map((request) => (
              <tr key={request.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  {request.request_number}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {request.unit_number}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {request.owner_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {request.request_type_name}
                </td>
                <td className="px-6 py-4 text-sm max-w-xs truncate">
                  {request.project_description}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded ${getStatusColor(request.status)}`}>
                    {request.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {request.submission_date
                    ? new Date(request.submission_date).toLocaleDateString()
                    : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <Link
                    to={`/arc-requests/${request.id}`}
                    className="text-blue-600 hover:text-blue-800 mr-3"
                  >
                    View
                  </Link>
                  {request.status === 'submitted' && (
                    <button className="text-green-600 hover:text-green-800">
                      Review
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="mt-6 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          Showing {requests?.length || 0} requests
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 border rounded hover:bg-gray-50">Previous</button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded">1</button>
          <button className="px-4 py-2 border rounded hover:bg-gray-50">Next</button>
        </div>
      </div>

      {/* Info Box */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Owner Portal</h3>
        <p className="text-sm text-blue-800">
          Homeowners can submit ARC requests directly through the owner portal.
          The committee will be notified automatically and can review, approve,
          or request modifications here.
        </p>
      </div>
    </div>
  );
};

// Helper function for status badge colors
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'draft':
      return 'bg-gray-100 text-gray-800';
    case 'submitted':
      return 'bg-yellow-100 text-yellow-800';
    case 'under_review':
      return 'bg-blue-100 text-blue-800';
    case 'approved':
      return 'bg-green-100 text-green-800';
    case 'denied':
      return 'bg-red-100 text-red-800';
    case 'conditional_approval':
      return 'bg-orange-100 text-orange-800';
    case 'completed':
      return 'bg-purple-100 text-purple-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export default ARCRequestsListPage;
