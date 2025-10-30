/**
 * Violations List Page (Sprint 15)
 *
 * Displays list of all violations with:
 * - Filtering by status, type, unit
 * - Search by owner/unit
 * - Pagination
 * - Actions: Create, View Detail, Escalate
 *
 * API Integration:
 * - GET /api/v1/accounting/violations/
 * - GET /api/v1/accounting/violation-types/
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

// Types
interface Violation {
  id: string;
  unit_number: string;
  owner_name: string;
  violation_type_name: string;
  description: string;
  status: 'open' | 'escalated' | 'cured' | 'closed';
  reported_date: string;
  cure_deadline: string;
  fine_total?: number;
}

// API Functions
const fetchViolations = async (): Promise<Violation[]> => {
  const response = await fetch('/api/v1/accounting/violations/');
  if (!response.ok) throw new Error('Failed to fetch violations');
  return response.json();
};

export const ViolationsListPage: React.FC = () => {
  // Fetch violations data
  const { data: violations, isLoading, error } = useQuery({
    queryKey: ['violations'],
    queryFn: fetchViolations,
  });

  if (isLoading) {
    return <div className="p-8">Loading violations...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-600">Error loading violations</div>;
  }

  return (
    <div className="container mx-auto p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Violations</h1>
        <Link
          to="/violations/create"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Create Violation
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Status</label>
            <select className="w-full border rounded px-3 py-2">
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="escalated">Escalated</option>
              <option value="cured">Cured</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Type</label>
            <select className="w-full border rounded px-3 py-2">
              <option value="">All Types</option>
              {/* Populated from violation-types API */}
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

      {/* Violations Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
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
                Description
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Reported
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Deadline
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {violations?.map((violation) => (
              <tr key={violation.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  {violation.unit_number}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {violation.owner_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {violation.violation_type_name}
                </td>
                <td className="px-6 py-4 text-sm max-w-xs truncate">
                  {violation.description}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded ${getStatusColor(violation.status)}`}>
                    {violation.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {new Date(violation.reported_date).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {new Date(violation.cure_deadline).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <Link
                    to={`/violations/${violation.id}`}
                    className="text-blue-600 hover:text-blue-800 mr-3"
                  >
                    View
                  </Link>
                  {violation.status === 'open' && (
                    <button className="text-orange-600 hover:text-orange-800">
                      Escalate
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
          Showing {violations?.length || 0} violations
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 border rounded hover:bg-gray-50">Previous</button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded">1</button>
          <button className="px-4 py-2 border rounded hover:bg-gray-50">2</button>
          <button className="px-4 py-2 border rounded hover:bg-gray-50">Next</button>
        </div>
      </div>
    </div>
  );
};

// Helper function for status badge colors
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'open':
      return 'bg-yellow-100 text-yellow-800';
    case 'escalated':
      return 'bg-orange-100 text-orange-800';
    case 'cured':
      return 'bg-green-100 text-green-800';
    case 'closed':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export default ViolationsListPage;
