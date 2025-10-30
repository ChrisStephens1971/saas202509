/**
 * ARC Request Create Page (Sprint 15)
 *
 * Form for owners to submit architectural review requests with:
 * - Owner/Unit selection
 * - Request type selection
 * - Project description
 * - Document uploads (plans, specs, photos, contracts)
 * - Estimated cost and timeline
 *
 * API Integration:
 * - POST /api/v1/accounting/arc-requests/
 * - GET /api/v1/accounting/arc-request-types/
 * - GET /api/v1/accounting/owners/
 * - GET /api/v1/accounting/units/
 * - POST /api/v1/accounting/arc-documents/ (file upload)
 */

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

// Types
interface ARCRequestFormData {
  owner_id: string;
  unit_id: string;
  request_type_id: string;
  project_description: string;
  estimated_cost?: number;
  estimated_start_date?: string;
  estimated_completion_date?: string;
  contractor_name?: string;
  contractor_license?: string;
  notes?: string;
}

interface RequestType {
  id: string;
  code: string;
  name: string;
  category: string;
  requires_deposit: boolean;
  deposit_amount?: number;
}

interface Owner {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

interface Unit {
  id: string;
  unit_number: string;
  owner: string;
}

interface FilesByType {
  plans: File[];
  specs: File[];
  photos: File[];
  contracts: File[];
  other: File[];
}

// API Functions
const fetchRequestTypes = async (): Promise<RequestType[]> => {
  const response = await fetch('/api/v1/accounting/arc-request-types/');
  if (!response.ok) throw new Error('Failed to fetch request types');
  return response.json();
};

const fetchOwners = async (): Promise<Owner[]> => {
  const response = await fetch('/api/v1/accounting/owners/');
  if (!response.ok) throw new Error('Failed to fetch owners');
  return response.json();
};

const fetchUnits = async (): Promise<Unit[]> => {
  const response = await fetch('/api/v1/accounting/units/');
  if (!response.ok) throw new Error('Failed to fetch units');
  return response.json();
};

const createARCRequest = async (data: ARCRequestFormData) => {
  const response = await fetch('/api/v1/accounting/arc-requests/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create ARC request');
  return response.json();
};

export const ARCRequestCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState<FilesByType>({
    plans: [],
    specs: [],
    photos: [],
    contracts: [],
    other: [],
  });

  // Form handling
  const { register, handleSubmit, watch, formState: { errors } } = useForm<ARCRequestFormData>({
    defaultValues: {
      estimated_start_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days from now
    }
  });

  const selectedTypeId = watch('request_type_id');

  // Fetch reference data
  const { data: requestTypes } = useQuery({
    queryKey: ['arc-request-types'],
    queryFn: fetchRequestTypes,
  });

  const { data: owners } = useQuery({
    queryKey: ['owners'],
    queryFn: fetchOwners,
  });

  const { data: units } = useQuery({
    queryKey: ['units'],
    queryFn: fetchUnits,
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: createARCRequest,
    onSuccess: (data) => {
      // TODO: Upload documents if any
      navigate(`/arc-requests/${data.id}`);
    },
  });

  const onSubmit = (data: ARCRequestFormData) => {
    createMutation.mutate(data);
  };

  const handleFileChange = (type: keyof FilesByType) => (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(prev => ({
        ...prev,
        [type]: Array.from(e.target.files!),
      }));
    }
  };

  const selectedType = requestTypes?.find(t => t.id === selectedTypeId);
  const totalFiles = Object.values(files).reduce((sum, arr) => sum + arr.length, 0);

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Submit ARC Request</h1>
        <p className="text-gray-600 mt-1">Architectural Review Committee Request Form</p>
      </div>

      {/* Information Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-bold text-blue-900 mb-2">Before You Submit</h3>
        <ul className="text-sm text-blue-900 space-y-1">
          <li>• Complete all required fields</li>
          <li>• Upload detailed plans and specifications</li>
          <li>• Include photos of the current condition</li>
          <li>• Provide contractor information if applicable</li>
          <li>• Review committee typically responds within 30 days</li>
        </ul>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="bg-white rounded-lg shadow p-6">
        {/* Owner and Unit Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium mb-1">
              Owner <span className="text-red-500">*</span>
            </label>
            <select
              {...register('owner_id', { required: 'Owner is required' })}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">Select Owner...</option>
              {owners?.map((owner) => (
                <option key={owner.id} value={owner.id}>
                  {owner.first_name} {owner.last_name}
                </option>
              ))}
            </select>
            {errors.owner_id && (
              <p className="text-red-500 text-sm mt-1">{errors.owner_id.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Unit <span className="text-red-500">*</span>
            </label>
            <select
              {...register('unit_id', { required: 'Unit is required' })}
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
        </div>

        {/* Request Type */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Request Type <span className="text-red-500">*</span>
          </label>
          <select
            {...register('request_type_id', { required: 'Request type is required' })}
            className="w-full border rounded px-3 py-2"
          >
            <option value="">Select Type...</option>
            {requestTypes?.map((type) => (
              <option key={type.id} value={type.id}>
                {type.code} - {type.name}
              </option>
            ))}
          </select>
          {errors.request_type_id && (
            <p className="text-red-500 text-sm mt-1">{errors.request_type_id.message}</p>
          )}
          {selectedType?.requires_deposit && (
            <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded">
              <p className="text-sm text-yellow-900">
                <strong>Deposit Required:</strong> ${selectedType.deposit_amount} refundable deposit required for this request type.
              </p>
            </div>
          )}
        </div>

        {/* Project Description */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Project Description <span className="text-red-500">*</span>
          </label>
          <textarea
            {...register('project_description', { required: 'Project description is required' })}
            rows={6}
            className="w-full border rounded px-3 py-2"
            placeholder="Provide a detailed description of your project including scope of work, materials, colors, dimensions, and any other relevant details..."
          />
          {errors.project_description && (
            <p className="text-red-500 text-sm mt-1">{errors.project_description.message}</p>
          )}
        </div>

        {/* Estimated Cost and Timeline */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium mb-1">
              Estimated Cost
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
              Estimated Start Date
            </label>
            <input
              type="date"
              {...register('estimated_start_date')}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Estimated Completion Date
            </label>
            <input
              type="date"
              {...register('estimated_completion_date')}
              className="w-full border rounded px-3 py-2"
            />
          </div>
        </div>

        {/* Contractor Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium mb-1">
              Contractor Name
            </label>
            <input
              type="text"
              {...register('contractor_name')}
              className="w-full border rounded px-3 py-2"
              placeholder="If using a contractor..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Contractor License Number
            </label>
            <input
              type="text"
              {...register('contractor_license')}
              className="w-full border rounded px-3 py-2"
              placeholder="License #..."
            />
          </div>
        </div>

        {/* Document Uploads */}
        <div className="mb-6">
          <h3 className="text-lg font-bold mb-4">Supporting Documents</h3>
          <div className="space-y-4">
            {/* Plans */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Plans / Drawings
              </label>
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                multiple
                onChange={handleFileChange('plans')}
                className="w-full border rounded px-3 py-2"
              />
              <p className="text-sm text-gray-600 mt-1">
                Upload detailed plans, drawings, or sketches (PDF, JPG, PNG)
              </p>
              {files.plans.length > 0 && (
                <p className="text-sm text-green-600 mt-1">{files.plans.length} file(s) selected</p>
              )}
            </div>

            {/* Specifications */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Specifications / Details
              </label>
              <input
                type="file"
                accept=".pdf,.doc,.docx"
                multiple
                onChange={handleFileChange('specs')}
                className="w-full border rounded px-3 py-2"
              />
              <p className="text-sm text-gray-600 mt-1">
                Material specs, product details, color samples (PDF, DOC)
              </p>
              {files.specs.length > 0 && (
                <p className="text-sm text-green-600 mt-1">{files.specs.length} file(s) selected</p>
              )}
            </div>

            {/* Photos */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Photos (Current Condition)
              </label>
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={handleFileChange('photos')}
                className="w-full border rounded px-3 py-2"
              />
              <p className="text-sm text-gray-600 mt-1">
                Photos of the current condition and area to be modified
              </p>
              {files.photos.length > 0 && (
                <p className="text-sm text-green-600 mt-1">{files.photos.length} photo(s) selected</p>
              )}
            </div>

            {/* Contracts */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Contractor Agreement / Contract
              </label>
              <input
                type="file"
                accept=".pdf,.doc,.docx"
                multiple
                onChange={handleFileChange('contracts')}
                className="w-full border rounded px-3 py-2"
              />
              <p className="text-sm text-gray-600 mt-1">
                Signed contractor agreements, insurance certificates
              </p>
              {files.contracts.length > 0 && (
                <p className="text-sm text-green-600 mt-1">{files.contracts.length} file(s) selected</p>
              )}
            </div>

            {/* Other Documents */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Other Supporting Documents
              </label>
              <input
                type="file"
                multiple
                onChange={handleFileChange('other')}
                className="w-full border rounded px-3 py-2"
              />
              <p className="text-sm text-gray-600 mt-1">
                Any other relevant documentation
              </p>
              {files.other.length > 0 && (
                <p className="text-sm text-green-600 mt-1">{files.other.length} file(s) selected</p>
              )}
            </div>
          </div>
          {totalFiles > 0 && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded">
              <p className="text-sm text-green-900">
                <strong>Total:</strong> {totalFiles} document(s) ready to upload
              </p>
            </div>
          )}
        </div>

        {/* Additional Notes */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Additional Notes
          </label>
          <textarea
            {...register('notes')}
            rows={3}
            className="w-full border rounded px-3 py-2"
            placeholder="Any additional information for the committee..."
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/arc-requests')}
            className="px-4 py-2 border rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {createMutation.isPending ? 'Submitting...' : 'Submit Request'}
          </button>
        </div>

        {/* Error Message */}
        {createMutation.isError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
            <p className="text-red-700">Failed to submit request. Please try again.</p>
          </div>
        )}
      </form>
    </div>
  );
};

export default ARCRequestCreatePage;
