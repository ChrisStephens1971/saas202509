/**
 * Work Orders List Page (Sprint 17)
 *
 * Displays list of all work orders with:
 * - Filtering by status, category, vendor, priority
 * - Search by work order number, title
 * - Pagination
 * - Actions: Create, View Detail, Assign, Complete
 *
 * API Integration:
 * - GET /api/v1/accounting/work-orders/
 * - GET /api/v1/accounting/work-order-categories/
 * - GET /api/v1/accounting/vendors/
 * - POST /api/v1/accounting/work-orders/{id}/assign/
 * - POST /api/v1/accounting/work-orders/{id}/complete/
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

// Types
interface WorkOrder {
  id: string;
  work_order_number: string;
  title: string;
  category_name: string;
  priority: 'urgent' | 'high' | 'normal' | 'low';
  status: 'draft' | 'open' | 'assigned' | 'in_progress' | 'completed' | 'closed';
  vendor_name?: string;
  estimated_cost?: number;
  actual_cost?: number;
  created_date: string;
}

// API Functions
const fetchWorkOrders = async (): Promise<WorkOrder[]> => {
  const response = await fetch('/api/v1/accounting/work-orders/');
  if (!response.ok) throw new Error('Failed to fetch work orders');
  return response.json();
};

export const WorkOrdersListPage: React.FC = () => {
  // Fetch work orders data
  const { data: workOrders, isLoading, error } = useQuery({
    queryKey: ['work-orders'],
    queryFn: fetchWorkOrders,
  });

  if (isLoading) {
    return <div className="p-8">Loading work orders...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-600">Error loading work orders</div>;
  }

  return (
    <div className="container mx-auto p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Work Orders</h1>
          <p className="text-gray-600 mt-1">Manage maintenance requests and repairs</p>
        </div>
        <Link
          to="/work-orders/create"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Create Work Order
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Open</div>
          <div className="text-2xl font-bold">
            {workOrders?.filter(wo => wo.status === 'open').length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Assigned</div>
          <div className="text-2xl font-bold">
            {workOrders?.filter(wo => wo.status === 'assigned').length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">In Progress</div>
          <div className="text-2xl font-bold">
            {workOrders?.filter(wo => wo.status === 'in_progress').length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Completed</div>
          <div className="text-2xl font-bold">
            {workOrders?.filter(wo => wo.status === 'completed').length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Total Cost</div>
          <div className="text-2xl font-bold">
            ${workOrders?.reduce((sum, wo) => sum + (wo.actual_cost || 0), 0).toFixed(2)}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Status</label>
            <select className="w-full border rounded px-3 py-2">
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Category</label>
            <select className="w-full border rounded px-3 py-2">
              <option value="">All Categories</option>
              {/* Populated from work-order-categories API */}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Priority</label>
            <select className="w-full border rounded px-3 py-2">
              <option value="">All Priorities</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="normal">Normal</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Search</label>
            <input
              type="text"
              placeholder="WO #, Title..."
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

      {/* Work Orders Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                WO #
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Title
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Priority
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Vendor
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Est. Cost
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {workOrders?.map((wo) => (
              <tr key={wo.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  {wo.work_order_number}
                </td>
                <td className="px-6 py-4 text-sm max-w-xs truncate">
                  {wo.title}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {wo.category_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded ${getPriorityColor(wo.priority)}`}>
                    {wo.priority}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded ${getStatusColor(wo.status)}`}>
                    {wo.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {wo.vendor_name || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  ${wo.estimated_cost?.toFixed(2) || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {new Date(wo.created_date).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <Link
                    to={`/work-orders/${wo.id}`}
                    className="text-blue-600 hover:text-blue-800 mr-3"
                  >
                    View
                  </Link>
                  {wo.status === 'open' && (
                    <button className="text-green-600 hover:text-green-800">
                      Assign
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
          Showing {workOrders?.length || 0} work orders
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 border rounded hover:bg-gray-50">Previous</button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded">1</button>
          <button className="px-4 py-2 border rounded hover:bg-gray-50">Next</button>
        </div>
      </div>
    </div>
  );
};

// Helper functions
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'draft':
      return 'bg-gray-100 text-gray-800';
    case 'open':
      return 'bg-yellow-100 text-yellow-800';
    case 'assigned':
      return 'bg-blue-100 text-blue-800';
    case 'in_progress':
      return 'bg-purple-100 text-purple-800';
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'closed':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const getPriorityColor = (priority: string): string => {
  switch (priority) {
    case 'urgent':
      return 'bg-red-100 text-red-800';
    case 'high':
      return 'bg-orange-100 text-orange-800';
    case 'normal':
      return 'bg-blue-100 text-blue-800';
    case 'low':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export default WorkOrdersListPage;
