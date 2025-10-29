/**
 * Delinquency Dashboard Page
 *
 * Overview of delinquent owners with summary statistics and aging breakdown
 */

import { useState, useEffect } from 'react';
import { AlertCircle, TrendingUp, DollarSign, Users, Clock } from 'lucide-react';
import {
  getDelinquencyStatuses,
  getDelinquencySummary,
  DelinquencyStatus,
  DelinquencySummary
} from '../api/delinquency';

export default function DelinquencyDashboardPage() {
  const [statuses, setStatuses] = useState<DelinquencyStatus[]>([]);
  const [summary, setSummary] = useState<DelinquencySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stageFilter, setStageFilter] = useState<string>('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statusesData, summaryData] = await Promise.all([
        getDelinquencyStatuses(),
        getDelinquencySummary()
      ]);
      setStatuses(statusesData);
      setSummary(summaryData);
    } catch (err: any) {
      setError(err.message || 'Failed to load delinquency data');
    } finally {
      setLoading(false);
    }
  };

  const filteredStatuses = stageFilter === 'all'
    ? statuses
    : statuses.filter(s => s.collection_stage === stageFilter);

  const getStageColor = (stage: string): string => {
    const colors: Record<string, string> = {
      'current': 'bg-green-100 text-green-800',
      'first_notice': 'bg-yellow-100 text-yellow-800',
      'second_notice': 'bg-orange-100 text-orange-800',
      'final_notice': 'bg-red-100 text-red-800',
      'pre_legal': 'bg-purple-100 text-purple-800',
      'legal_action': 'bg-red-200 text-red-900',
      'lien_filed': 'bg-red-300 text-red-950',
      'foreclosure': 'bg-gray-900 text-white',
    };
    return colors[stage] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading delinquency data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center gap-2 text-red-800">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Delinquency Dashboard</h1>
        <p className="text-gray-600 mt-1">Monitor and manage delinquent accounts</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Delinquent</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {summary?.total_delinquent || 0}
              </p>
            </div>
            <div className="bg-red-100 rounded-lg p-3">
              <Users className="h-6 w-6 text-red-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Balance</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                ${parseFloat(summary?.total_balance || '0').toLocaleString()}
              </p>
            </div>
            <div className="bg-orange-100 rounded-lg p-3">
              <DollarSign className="h-6 w-6 text-orange-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Days Delinquent</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {statuses.length > 0
                  ? Math.round(statuses.reduce((sum, s) => sum + s.days_delinquent, 0) / statuses.length)
                  : 0}
              </p>
            </div>
            <div className="bg-blue-100 rounded-lg p-3">
              <Clock className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Accounts 90+ Days</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {statuses.filter(s => parseFloat(s.balance_90_plus) > 0).length}
              </p>
            </div>
            <div className="bg-purple-100 rounded-lg p-3">
              <TrendingUp className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Stage Breakdown */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">By Collection Stage</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {summary && Object.entries(summary.by_stage).map(([stage, data]) => (
            <div key={stage} className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{data.count}</div>
              <div className="text-sm text-gray-600 mt-1 capitalize">
                {stage.replace(/_/g, ' ')}
              </div>
              <div className="text-sm font-semibold text-gray-900 mt-1">
                ${parseFloat(data.balance).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={stageFilter}
          onChange={(e) => setStageFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="all">All Stages</option>
          <option value="current">Current</option>
          <option value="first_notice">First Notice</option>
          <option value="second_notice">Second Notice</option>
          <option value="final_notice">Final Notice</option>
          <option value="pre_legal">Pre-Legal</option>
          <option value="legal_action">Legal Action</option>
          <option value="lien_filed">Lien Filed</option>
          <option value="foreclosure">Foreclosure</option>
        </select>
      </div>

      {/* Delinquent Accounts Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Delinquent Accounts</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Owner
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Balance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  0-30 Days
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  31-60 Days
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  61-90 Days
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  90+ Days
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Stage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Days
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredStatuses.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                    No delinquent accounts found
                  </td>
                </tr>
              ) : (
                filteredStatuses.map((status) => (
                  <tr key={status.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{status.owner_name}</div>
                      {status.is_payment_plan && (
                        <div className="text-xs text-blue-600">Payment Plan</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-semibold text-gray-900">
                      ${parseFloat(status.current_balance).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                      ${parseFloat(status.balance_0_30).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                      ${parseFloat(status.balance_31_60).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                      ${parseFloat(status.balance_61_90).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-red-600 font-semibold">
                      ${parseFloat(status.balance_90_plus).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStageColor(status.collection_stage)}`}>
                        {status.stage_display}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                      {status.days_delinquent}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
