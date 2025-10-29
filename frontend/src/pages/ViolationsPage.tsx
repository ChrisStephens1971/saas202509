/**
 * Violations Page - List and manage HOA violations
 */

import { useState, useEffect } from 'react';
import { AlertOctagon, Camera, Plus, X, Upload as UploadIcon } from 'lucide-react';
import { getViolations, type Violation } from '../api/violations';
import ViolationPhotoUpload from '../components/violations/ViolationPhotoUpload';

export default function ViolationsPage() {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedViolation, setSelectedViolation] = useState<Violation | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);

  useEffect(() => {
    loadViolations();
  }, []);

  const loadViolations = () => {
    getViolations().then(setViolations).finally(() => setLoading(false));
  };

  const handleUploadComplete = () => {
    loadViolations();
  };

  const getSeverityColor = (severity: string) => {
    const colors = {
      minor: 'bg-yellow-100 text-yellow-800',
      moderate: 'bg-orange-100 text-orange-800',
      major: 'bg-red-100 text-red-800',
      critical: 'bg-red-200 text-red-900'
    };
    return colors[severity as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getStatusColor = (status: string) => {
    const colors = {
      reported: 'bg-blue-100 text-blue-800',
      notice_sent: 'bg-purple-100 text-purple-800',
      hearing_scheduled: 'bg-orange-100 text-orange-800',
      resolved: 'bg-green-100 text-green-800'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const filtered = violations.filter(v =>
    (severityFilter === 'all' || v.severity === severityFilter) &&
    (statusFilter === 'all' || v.status === statusFilter)
  );

  if (loading) return <div className="text-center py-8">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertOctagon className="h-8 w-8 text-red-600" />
          <h1 className="text-3xl font-bold">Violations</h1>
        </div>
        <button className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Report Violation
        </button>
      </div>

      <div className="flex gap-4">
        <select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)} className="px-4 py-2 border rounded-lg">
          <option value="all">All Severities</option>
          <option value="minor">Minor</option>
          <option value="moderate">Moderate</option>
          <option value="major">Major</option>
          <option value="critical">Critical</option>
        </select>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="px-4 py-2 border rounded-lg">
          <option value="all">All Statuses</option>
          <option value="reported">Reported</option>
          <option value="notice_sent">Notice Sent</option>
          <option value="hearing_scheduled">Hearing Scheduled</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>

      <div className="grid gap-4">
        {filtered.map((violation) => (
          <div key={violation.id} className="bg-white rounded-lg border p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold">{violation.owner_name}</h3>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(violation.severity)}`}>
                    {violation.severity_display}
                  </span>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(violation.status)}`}>
                    {violation.status_display}
                  </span>
                </div>
                <div className="text-sm text-gray-600 mb-2">{violation.property_address}</div>
                <div className="grid grid-cols-2 gap-4 mt-3">
                  <div>
                    <div className="text-sm text-gray-600">Type</div>
                    <div className="font-medium">{violation.violation_type}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Reported</div>
                    <div className="font-medium">{new Date(violation.reported_date).toLocaleDateString()}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Fine Amount</div>
                    <div className="font-semibold">${parseFloat(violation.fine_amount).toFixed(2)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Photos</div>
                    <div className="flex items-center gap-1">
                      <Camera className="h-4 w-4" />
                      <span>{violation.photos?.length || 0}</span>
                    </div>
                  </div>
                </div>
                <div className="mt-3 text-sm text-gray-700">{violation.description}</div>
                <div className="mt-4">
                  <button
                    onClick={() => {
                      setSelectedViolation(violation);
                      setShowUploadModal(true);
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 text-sm"
                  >
                    <UploadIcon className="h-4 w-4" />
                    Upload Photos
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Upload Modal */}
      {showUploadModal && selectedViolation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold">Upload Photos</h2>
                <p className="text-sm text-gray-600 mt-1">
                  {selectedViolation.violation_type} - {selectedViolation.property_address}
                </p>
              </div>
              <button
                onClick={() => {
                  setShowUploadModal(false);
                  setSelectedViolation(null);
                }}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-6">
              <ViolationPhotoUpload
                violationId={selectedViolation.id}
                onUploadComplete={handleUploadComplete}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
