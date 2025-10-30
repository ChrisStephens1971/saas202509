/**
 * Create Work Order Page (Sprint 15)
 *
 * Form to create a new work order with:
 * - Title and description
 * - Category and priority
 * - Cost estimates
 * - Vendor assignment
 * - Location (unit or common area)
 * - Attachment uploads
 *
 * API Integration:
 * - POST /api/v1/accounting/work-orders/
 * - GET /api/v1/accounting/work-order-categories/
 * - GET /api/v1/accounting/vendors/
 * - GET /api/v1/accounting/units/
 * - POST /api/v1/accounting/work-order-attachments/ (file upload)
 */

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

// Types
interface WorkOrderFormData {
  title: string;
  description: string;
  category_id: string;
  priority: 'low' | 'medium' | 'high' | 'emergency';
  location_type: 'unit' | 'common_area';
  unit_id?: string;
  location_description: string;
  estimated_cost?: number;
  assigned_to_vendor_id?: string;
  scheduled_date?: string;
  notes?: string;
}

interface Category {
  id: string;
  name: string;
  description?: string;
}

interface Vendor {
  id: string;
  name: string;
  contact_name: string;
  phone: string;
  email: string;
  specialties: string[];
}

interface Unit {
  id: string;
  unit_number: string;
  owner: string;
}

// API Functions
const fetchCategories = async (): Promise<Category[]> => {
  const response = await fetch('/api/v1/accounting/work-order-categories/');
  if (!response.ok) throw new Error('Failed to fetch categories');
  return response.json();
};

const fetchVendors = async (): Promise<Vendor[]> => {
  const response = await fetch('/api/v1/accounting/vendors/');
  if (!response.ok) throw new Error('Failed to fetch vendors');
  return response.json();
};

const fetchUnits = async (): Promise<Unit[]> => {
  const response = await fetch('/api/v1/accounting/units/');
  if (!response.ok) throw new Error('Failed to fetch units');
  return response.json();
};

const createWorkOrder = async (data: WorkOrderFormData) => {
  const response = await fetch('/api/v1/accounting/work-orders/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create work order');
  return response.json();
};

export const WorkOrderCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const [attachments, setAttachments] = useState<File[]>([]);

  // Form handling
  const { register, handleSubmit, watch, formState: { errors } } = useForm<WorkOrderFormData>({
    defaultValues: {
      priority: 'medium',
      location_type: 'common_area',
    }
  });

  const locationType = watch('location_type');

  // Fetch reference data
  const { data: categories } = useQuery({
    queryKey: ['work-order-categories'],
    queryFn: fetchCategories,
  });

  const { data: vendors } = useQuery({
    queryKey: ['vendors'],
    queryFn: fetchVendors,
  });

  const { data: units } = useQuery({
    queryKey: ['units'],
    queryFn: fetchUnits,
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: createWorkOrder,
    onSuccess: (data) => {
      // TODO: Upload attachments if any
      navigate(`/work-orders/${data.id}`);
    },
  });

  const onSubmit = (data: WorkOrderFormData) => {
    createMutation.mutate(data);
  };

  const handleAttachmentChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setAttachments(Array.from(e.target.files));
    }
  };

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Create Work Order</h1>
        <p className="text-gray-600 mt-1">Schedule maintenance or repairs</p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="bg-white rounded-lg shadow p-6">
        {/* Title */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            {...register('title', { required: 'Title is required' })}
            className="w-full border rounded px-3 py-2"
            placeholder="Brief summary of the work needed..."
          />
          {errors.title && (
            <p className="text-red-500 text-sm mt-1">{errors.title.message}</p>
          )}
        </div>

        {/* Category and Priority */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium mb-1">
              Category <span className="text-red-500">*</span>
            </label>
            <select
              {...register('category_id', { required: 'Category is required' })}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">Select Category...</option>
              {categories?.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            {errors.category_id && (
              <p className="text-red-500 text-sm mt-1">{errors.category_id.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Priority <span className="text-red-500">*</span>
            </label>
            <select
              {...register('priority', { required: 'Priority is required' })}
              className="w-full border rounded px-3 py-2"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="emergency">Emergency</option>
            </select>
            {errors.priority && (
              <p className="text-red-500 text-sm mt-1">{errors.priority.message}</p>
            )}
          </div>
        </div>

        {/* Description */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Description <span className="text-red-500">*</span>
          </label>
          <textarea
            {...register('description', { required: 'Description is required' })}
            rows={4}
            className="w-full border rounded px-3 py-2"
            placeholder="Detailed description of the work needed..."
          />
          {errors.description && (
            <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
          )}
        </div>

        {/* Location Type */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Location Type <span className="text-red-500">*</span>
          </label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="common_area"
                {...register('location_type')}
                className="mr-2"
              />
              Common Area
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="unit"
                {...register('location_type')}
                className="mr-2"
              />
              Specific Unit
            </label>
          </div>
        </div>

        {/* Unit Selection (conditional) */}
        {locationType === 'unit' && (
          <div className="mb-6">
            <label className="block text-sm font-medium mb-1">
              Unit <span className="text-red-500">*</span>
            </label>
            <select
              {...register('unit_id', {
                required: locationType === 'unit' ? 'Unit is required' : false
              })}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">Select Unit...</option>
              {units?.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.unit_number}
                </option>
              ))}
            </select>
            {errors.unit_id && (
              <p className="text-red-500 text-sm mt-1">{errors.unit_id.message}</p>
            )}
          </div>
        )}

        {/* Location Description */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Location Description <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            {...register('location_description', { required: 'Location description is required' })}
            className="w-full border rounded px-3 py-2"
            placeholder="Pool area, Unit 101 kitchen, etc."
          />
          {errors.location_description && (
            <p className="text-red-500 text-sm mt-1">{errors.location_description.message}</p>
          )}
        </div>

        {/* Estimated Cost and Scheduled Date */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium mb-1">
              Estimated Cost (Optional)
            </label>
            <input
              type="number"
              step="0.01"
              {...register('estimated_cost')}
              className="w-full border rounded px-3 py-2"
              placeholder="0.00"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Scheduled Date (Optional)
            </label>
            <input
              type="date"
              {...register('scheduled_date')}
              className="w-full border rounded px-3 py-2"
            />
          </div>
        </div>

        {/* Vendor Assignment */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Assign to Vendor (Optional)
          </label>
          <select
            {...register('assigned_to_vendor_id')}
            className="w-full border rounded px-3 py-2"
          >
            <option value="">Not Assigned</option>
            {vendors?.map((vendor) => (
              <option key={vendor.id} value={vendor.id}>
                {vendor.name} - {vendor.specialties.join(', ')}
              </option>
            ))}
          </select>
          <p className="text-sm text-gray-600 mt-1">
            You can assign a vendor now or later
          </p>
        </div>

        {/* Attachments */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Attachments (Photos, Documents)
          </label>
          <input
            type="file"
            multiple
            onChange={handleAttachmentChange}
            className="w-full border rounded px-3 py-2"
          />
          <p className="text-sm text-gray-600 mt-1">
            Upload photos or documents related to this work order
          </p>
          {attachments.length > 0 && (
            <div className="mt-2">
              <p className="text-sm text-green-600">{attachments.length} file(s) selected</p>
            </div>
          )}
        </div>

        {/* Internal Notes */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Internal Notes (Optional)
          </label>
          <textarea
            {...register('notes')}
            rows={3}
            className="w-full border rounded px-3 py-2"
            placeholder="Internal notes not visible to vendor..."
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/work-orders')}
            className="px-4 py-2 border rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {createMutation.isPending ? 'Creating...' : 'Create Work Order'}
          </button>
        </div>

        {/* Error Message */}
        {createMutation.isError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
            <p className="text-red-700">Failed to create work order. Please try again.</p>
          </div>
        )}
      </form>
    </div>
  );
};

export default WorkOrderCreatePage;
