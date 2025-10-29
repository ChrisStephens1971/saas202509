/**
 * Match Statistics Page - Performance metrics dashboard
 */

import { useState, useEffect } from 'react';
import { TrendingUp, Target, AlertTriangle } from 'lucide-react';
import { getMatchStatistics, MatchStatistics } from '../api/matching';

export default function MatchStatisticsPage() {
  const [stats, setStats] = useState<MatchStatistics[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMatchStatistics().then(setStats).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-8">Loading...</div>;

  const latest = stats[0];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Match Statistics</h1>

      {latest && (
        <>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Auto-Match Rate</p>
                  <p className="text-3xl font-bold text-green-600">{parseFloat(latest.auto_match_rate).toFixed(1)}%</p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-600" />
              </div>
            </div>
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Avg Confidence</p>
                  <p className="text-3xl font-bold text-blue-600">{parseFloat(latest.average_confidence).toFixed(1)}%</p>
                </div>
                <Target className="h-8 w-8 text-blue-600" />
              </div>
            </div>
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">False Positive Rate</p>
                  <p className="text-3xl font-bold text-orange-600">{parseFloat(latest.false_positive_rate).toFixed(1)}%</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-orange-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Transaction Breakdown</h2>
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{latest.total_transactions}</div>
                <div className="text-sm text-gray-600">Total</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{latest.auto_matched}</div>
                <div className="text-sm text-gray-600">Auto-Matched</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{latest.manually_matched}</div>
                <div className="text-sm text-gray-600">Manual</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-600">{latest.unmatched}</div>
                <div className="text-sm text-gray-600">Unmatched</div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
