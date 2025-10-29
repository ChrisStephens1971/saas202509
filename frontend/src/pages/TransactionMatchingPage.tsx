/**
 * Transaction Matching Page - Review and accept AI match suggestions
 */

import { useState, useEffect } from 'react';
import { Check, X, Zap } from 'lucide-react';
import { getMatchResults, acceptMatch, MatchResult } from '../api/matching';

export default function TransactionMatchingPage() {
  const [matches, setMatches] = useState<MatchResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMatches();
  }, []);

  const loadMatches = async () => {
    try {
      const data = await getMatchResults();
      setMatches(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (id: string) => {
    try {
      await acceptMatch(id);
      loadMatches();
    } catch (err) {
      alert('Failed to accept match');
    }
  };

  if (loading) return <div className="text-center py-8">Loading matches...</div>;

  const pendingMatches = matches.filter(m => !m.was_accepted);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Zap className="h-8 w-8 text-yellow-500" />
        <div>
          <h1 className="text-3xl font-bold">Transaction Matching</h1>
          <p className="text-gray-600">Review AI-powered match suggestions</p>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-blue-900">{pendingMatches.length}</div>
            <div className="text-sm text-blue-700">Pending Matches</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-900">{matches.filter(m => m.was_accepted).length}</div>
            <div className="text-sm text-green-700">Accepted</div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {pendingMatches.map((match) => (
          <div key={match.id} className="bg-white rounded-lg border p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`px-3 py-1 rounded-full text-sm font-bold ${
                    match.confidence_score >= 90 ? 'bg-green-100 text-green-800' :
                    match.confidence_score >= 70 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-orange-100 text-orange-800'
                  }`}>
                    {match.confidence_score}% Confidence
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm font-medium text-gray-600">Bank Transaction</div>
                    <div className="font-semibold">{match.bank_transaction_description}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600">Matched Entry</div>
                    <div className="font-semibold">{match.matched_entry_reference}</div>
                  </div>
                </div>
                <div className="mt-3 p-3 bg-gray-50 rounded">
                  <div className="text-sm text-gray-700">{match.match_explanation}</div>
                </div>
              </div>
              <div className="ml-4 flex gap-2">
                <button
                  onClick={() => handleAccept(match.id)}
                  className="bg-green-600 text-white p-2 rounded-lg hover:bg-green-700"
                  title="Accept Match"
                >
                  <Check className="h-5 w-5" />
                </button>
                <button
                  className="bg-red-600 text-white p-2 rounded-lg hover:bg-red-700"
                  title="Reject Match"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        ))}
        {pendingMatches.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No pending matches. All transactions have been reviewed!
          </div>
        )}
      </div>
    </div>
  );
}
