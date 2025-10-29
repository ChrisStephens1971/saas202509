import React, { useState, useEffect } from 'react';
import { customReportsApi, type CustomReport } from '../api/reports';

const CustomReportsPage: React.FC = () => {
  const [reports, setReports] = useState<CustomReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const data = await customReportsApi.list();
      setReports(data);
    } catch (err) {
      setError('Failed to load custom reports');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const executeReport = async (reportId: string) => {
    try {
      const result = await customReportsApi.execute(reportId, {});
      alert(`Report executed successfully! ${result.row_count} rows returned in ${result.execution_time_ms}ms`);
    } catch (err) {
      console.error('Failed to execute report:', err);
      alert('Failed to execute report');
    }
  };

  const exportCSV = async (reportId: string, reportName: string) => {
    try {
      const csvData = await customReportsApi.exportCSV(reportId);
      // Download CSV
      const blob = new Blob([csvData], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportName}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export CSV:', err);
      alert('Failed to export CSV');
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Custom Reports</h1>
          <p className="mt-2 text-gray-600">
            Create and manage custom financial reports
          </p>
        </div>
        <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          + New Report
        </button>
      </div>

      {reports.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500 mb-4">No custom reports found</p>
          <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Create First Report
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {reports.map((report) => (
            <div
              key={report.id}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-semibold text-gray-900">{report.name}</h3>
                    {report.is_favorite && (
                      <span className="text-yellow-500">⭐</span>
                    )}
                  </div>
                  <p className="text-gray-600 mt-1">{report.description || 'No description'}</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Type: {report.report_type_display}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => executeReport(report.id)}
                    className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                  >
                    Run
                  </button>
                  <button
                    onClick={() => exportCSV(report.id, report.name)}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                  >
                    Export CSV
                  </button>
                </div>
              </div>

              <div className="mt-4 flex gap-2">
                <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                  {report.columns.length} Columns
                </span>
                <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                  {report.execution_count} Executions
                </span>
                {report.is_public && (
                  <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">
                    Public
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CustomReportsPage;
