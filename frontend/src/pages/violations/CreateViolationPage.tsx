/**
 * Create Violation Page (Sprint 15)
 *
 * Form to create a new violation with:
 * - Owner/Unit selection
 * - Violation type selection
 * - Description and location
 * - Photo upload
 * - Cure deadline
 *
 * API Integration:
 * - POST /api/v1/accounting/violations/
 * - GET /api/v1/accounting/violation-types/
 * - GET /api/v1/accounting/owners/
 * - GET /api/v1/accounting/units/
 * - POST /api/v1/accounting/violation-photos/ (file upload)
 */

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

// Types
interface ViolationFormData {
  owner_id: string;
  unit_id: string;
  violation_type_id: string;
  description: string;
  location: string;
  severity: 'minor' | 'moderate' | 'major' | 'critical';
  cure_deadline: string;
  notes?: string;
}

interface ViolationType {
  id: string;
  code: string;
  name: string;
  category: string;
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

// API Functions
const fetchViolationTypes = async (): Promise<ViolationType[]> => {
  const response = await fetch('/api/v1/accounting/violation-types/');
  if (!response.ok) throw new Error('Failed to fetch violation types');
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

const createViolation = async (data: ViolationFormData) => {
  const response = await fetch('/api/v1/accounting/violations/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create violation');
  return response.json();
};

export const CreateViolationPage: React.FC = () => {
  const navigate = useNavigate();
  const [photos, setPhotos] = useState<File[]>([]);

  // Form handling
  const { register, handleSubmit, watch, formState: { errors } } = useForm<ViolationFormData>({
    defaultValues: {
      cure_deadline: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 14 days from now
    }
  });

  // Fetch reference data
  const { data: violationTypes } = useQuery({
    queryKey: ['violation-types'],
    queryFn: fetchViolationTypes,
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
    mutationFn: createViolation,
    onSuccess: (data) => {
      // TODO: Upload photos if any
      navigate(`/violations/${data.id}`);
    },
  });

  const onSubmit = (data: ViolationFormData) => {
    createMutation.mutate(data);
  };

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setPhotos(Array.from(e.target.files));
    }
  };

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Create Violation</h1>
        <p className="text-gray-600 mt-1">Document a new violation with photo evidence</p>
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

        {/* Violation Type and Severity */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium mb-1">
              Violation Type <span className="text-red-500">*</span>
            </label>
            <select
              {...register('violation_type_id', { required: 'Violation type is required' })}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">Select Type...</option>
              {violationTypes?.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.code} - {type.name}
                </option>
              ))}
            </select>
            {errors.violation_type_id && (
              <p className="text-red-500 text-sm mt-1">{errors.violation_type_id.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Severity <span className="text-red-500">*</span>
            </label>
            <select
              {...register('severity', { required: 'Severity is required' })}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">Select Severity...</option>
              <option value="minor">Minor</option>
              <option value="moderate">Moderate</option>
              <option value="major">Major</option>
              <option value="critical">Critical</option>
            </select>
            {errors.severity && (
              <p className="text-red-500 text-sm mt-1">{errors.severity.message}</p>
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
            placeholder="Detailed description of the violation..."
          />
          {errors.description && (
            <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
          )}
        </div>

        {/* Location */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Location <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            {...register('location', { required: 'Location is required' })}
            className="w-full border rounded px-3 py-2"
            placeholder="Front yard, Balcony, etc."
          />
          {errors.location && (
            <p className="text-red-500 text-sm mt-1">{errors.location.message}</p>
          )}
        </div>

        {/* Cure Deadline */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Cure Deadline <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            {...register('cure_deadline', { required: 'Cure deadline is required' })}
            className="w-full border rounded px-3 py-2"
          />
          {errors.cure_deadline && (
            <p className="text-red-500 text-sm mt-1">{errors.cure_deadline.message}</p>
          )}
          <p className="text-sm text-gray-600 mt-1">
            Date by which the violation must be corrected
          </p>
        </div>

        {/* Photo Upload */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Photos (Evidence)
          </label>
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={handlePhotoChange}
            className="w-full border rounded px-3 py-2"
          />
          <p className="text-sm text-gray-600 mt-1">
            Upload photos documenting the violation (max 10MB per photo)
          </p>
          {photos.length > 0 && (
            <div className="mt-2">
              <p className="text-sm text-green-600">{photos.length} photo(s) selected</p>
            </div>
          )}
        </div>

        {/* Notes */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">
            Internal Notes (Optional)
          </label>
          <textarea
            {...register('notes')}
            rows={3}
            className="w-full border rounded px-3 py-2"
            placeholder="Internal notes (not visible to owner)..."
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/violations')}
            className="px-4 py-2 border rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {createMutation.isPending ? 'Creating...' : 'Create Violation'}
          </button>
        </div>

        {/* Error Message */}
        {createMutation.isError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
            <p className="text-red-700">Failed to create violation. Please try again.</p>
          </div>
        )}
      </form>
    </div>
  );
};

export default CreateViolationPage;
