/**
 * Match Rules Page - Manage auto-match rules
 */

import { useState, useEffect } from 'react';
import { Brain } from 'lucide-react';
import { getMatchRules, type AutoMatchRule } from '../api/matching';

export default function MatchRulesPage() {
  const [rules, setRules] = useState<AutoMatchRule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMatchRules().then(setRules).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-8">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Brain className="h-8 w-8 text-purple-600" />
        <h1 className="text-3xl font-bold">Match Rules</h1>
      </div>

      <div className="bg-white rounded-lg border">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confidence</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Times Used</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Accuracy</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {rules.map((rule) => (
              <tr key={rule.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium">{rule.rule_type_display}</td>
                <td className="px-6 py-4">{rule.confidence_score}%</td>
                <td className="px-6 py-4">{rule.times_used}</td>
                <td className="px-6 py-4">
                  <span className={`font-semibold ${parseFloat(rule.accuracy_rate) >= 90 ? 'text-green-600' : parseFloat(rule.accuracy_rate) >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {parseFloat(rule.accuracy_rate).toFixed(1)}%
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${rule.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                    {rule.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
