/**
 * Auditor Exports Page
 * Sprint 21 - Auditor Export
 *
 * Features:
 * - List all auditor exports
 * - Create new export (date range picker)
 * - Generate CSV/Excel/PDF
 * - Download exports
 * - Track download history
 * - Verify file integrity
 */

import React, { useState, useEffect } from 'react';
import {
  AuditorExport,
  getAuditorExports,
  createAuditorExport,
  generateExport,
  downloadExport,
  deleteAuditorExport,
  verifyIntegrity,
} from '../api/auditorExports';

const AuditorExportsPage: React.FC = () => {
  const [exports, setExports] = useState<AuditorExport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [generating, setGenerating] = useState<string | null>(null);

  // Load exports on mount
  useEffect(() => {
    loadExports();
  }, []);

  const loadExports = async () => {
    try {
      setLoading(true);
      const data = await getAuditorExports();
      setExports(data);
      setError(null);
    } catch (err) {
      setError('Failed to load auditor exports');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExport = async (data: {
    title: string;
    start_date: string;
    end_date: string;
    format: 'csv' | 'excel' | 'pdf';
    include_evidence: boolean;
  }) => {
    try {
      const newExport = await createAuditorExport(data);
      setExports([newExport, ...exports]);
      setShowCreateModal(false);

      // Auto-generate after creation
      handleGenerateExport(newExport.id);
    } catch (err) {
      setError('Failed to create export');
      console.error(err);
    }
  };

  const handleGenerateExport = async (id: string) => {
    try {
      setGenerating(id);
      const result = await generateExport(id);

      if (result.status === 'success') {
        // Update export in list
        setExports(exports.map((exp) => (exp.id === id ? result.export : exp)));
        alert(`Export generated successfully: ${result.message}`);
      } else {
        alert(`Export generation failed: ${result.message}`);
      }
    } catch (err) {
      alert('Failed to generate export');
      console.error(err);
    } finally {
      setGenerating(null);
    }
  };

  const handleDownloadExport = async (exp: AuditorExport) => {
    try {
      const filename = `${exp.title.replace(/ /g, '_')}_${exp.start_date}_${exp.end_date}.${exp.format}`;
      await downloadExport(exp.id, filename);

      // Refresh to get updated download count
      loadExports();
    } catch (err) {
      alert('Failed to download export');
      console.error(err);
    }
  };

  const handleVerifyIntegrity = async (id: string) => {
    try {
      const result = await verifyIntegrity(id);

      if (result.status === 'valid') {
        alert(
          `✓ Export integrity verified\n\n` +
            `Entries: ${result.details?.total_entries}\n` +
            `Balanced: ${result.details?.balanced ? 'Yes' : 'No'}\n` +
            `Evidence: ${result.details?.evidence_percentage}%\n` +
            `Hash: ${result.details?.file_hash.substring(0, 12)}...`
        );
      } else {
        alert(`✗ Integrity check failed: ${result.error}`);
      }
    } catch (err) {
      alert('Failed to verify integrity');
      console.error(err);
    }
  };

  const handleDeleteExport = async (id: string, title: string) => {
    if (!confirm(`Delete export "${title}"?`)) return;

    try {
      await deleteAuditorExport(id);
      setExports(exports.filter((exp) => exp.id !== id));
    } catch (err) {
      alert('Failed to delete export');
      console.error(err);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-green-100 text-green-800';
      case 'generating':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading auditor exports...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Auditor Exports</h1>
          <p className="text-gray-600 mt-1">
            Generate audit-grade financial exports with evidence links
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          + New Export
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Exports Grid */}
      {exports.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No exports yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating your first auditor export.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              + New Export
            </button>
          </div>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {exports.map((exp) => (
            <div
              key={exp.id}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition"
            >
              {/* Header */}
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex-1">{exp.title}</h3>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded ${getStatusBadgeColor(
                    exp.status
                  )}`}
                >
                  {exp.status_display}
                </span>
              </div>

              {/* Date Range */}
              <div className="text-sm text-gray-600 mb-4">
                <div className="flex items-center">
                  <svg
                    className="h-4 w-4 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                  {formatDate(exp.start_date)} - {formatDate(exp.end_date)}
                </div>
              </div>

              {/* Metadata */}
              <div className="space-y-2 mb-4 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>Format:</span>
                  <span className="font-medium">{exp.format_display}</span>
                </div>
                <div className="flex justify-between">
                  <span>Entries:</span>
                  <span className="font-medium">{exp.total_entries.toLocaleString()}</span>
                </div>
                {exp.status === 'ready' && (
                  <>
                    <div className="flex justify-between">
                      <span>File Size:</span>
                      <span className="font-medium">{formatFileSize(exp.file_size_bytes)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Evidence:</span>
                      <span className="font-medium">{exp.evidence_percentage.toFixed(0)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Downloaded:</span>
                      <span className="font-medium">{exp.downloaded_count}x</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Balanced:</span>
                      <span className={exp.is_balanced ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                        {exp.is_balanced ? '✓ Yes' : '✗ No'}
                      </span>
                    </div>
                  </>
                )}
              </div>

              {/* Error Message */}
              {exp.status === 'failed' && exp.error_message && (
                <div className="text-xs text-red-600 mb-4 p-2 bg-red-50 rounded">
                  {exp.error_message}
                </div>
              )}

              {/* Actions */}
              <div className="flex flex-wrap gap-2">
                {exp.status === 'generating' && (
                  <button disabled className="px-3 py-1 text-sm bg-gray-100 text-gray-400 rounded cursor-not-allowed flex-1">
                    Generating...
                  </button>
                )}

                {exp.status === 'failed' && (
                  <button
                    onClick={() => handleGenerateExport(exp.id)}
                    disabled={generating === exp.id}
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition flex-1"
                  >
                    {generating === exp.id ? 'Generating...' : 'Retry'}
                  </button>
                )}

                {exp.status === 'ready' && (
                  <>
                    <button
                      onClick={() => handleDownloadExport(exp)}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition flex-1"
                    >
                      Download
                    </button>
                    <button
                      onClick={() => handleVerifyIntegrity(exp.id)}
                      className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition"
                      title="Verify file integrity"
                    >
                      Verify
                    </button>
                  </>
                )}

                <button
                  onClick={() => handleDeleteExport(exp.id, exp.title)}
                  className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition"
                >
                  Delete
                </button>
              </div>

              {/* Footer */}
              <div className="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-500">
                Generated {formatDate(exp.generated_at)} by {exp.generated_by_name}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Export Modal */}
      {showCreateModal && (
        <CreateExportModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateExport}
        />
      )}
    </div>
  );
};

// Create Export Modal Component
interface CreateExportModalProps {
  onClose: () => void;
  onCreate: (data: {
    title: string;
    start_date: string;
    end_date: string;
    format: 'csv' | 'excel' | 'pdf';
    include_evidence: boolean;
  }) => void;
}

const CreateExportModal: React.FC<CreateExportModalProps> = ({ onClose, onCreate }) => {
  const [title, setTitle] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [format, setFormat] = useState<'csv' | 'excel' | 'pdf'>('csv');
  const [includeEvidence, setIncludeEvidence] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!title || !startDate || !endDate) {
      alert('Please fill in all required fields');
      return;
    }

    if (new Date(endDate) < new Date(startDate)) {
      alert('End date must be after start date');
      return;
    }

    onCreate({
      title,
      start_date: startDate,
      end_date: endDate,
      format,
      include_evidence: includeEvidence,
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Create Auditor Export</h2>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4">
          <div className="space-y-4">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Export Title *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., 2025 Annual Audit Export"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            {/* Date Range */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date *
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date *
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            {/* Format */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Format</label>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value as 'csv' | 'excel' | 'pdf')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="csv">CSV (Excel compatible)</option>
                <option value="excel">Excel (.xlsx)</option>
                <option value="pdf">PDF Report</option>
              </select>
            </div>

            {/* Options */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeEvidence}
                  onChange={(e) => setIncludeEvidence(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Include evidence links</span>
              </label>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Create & Generate
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AuditorExportsPage;
