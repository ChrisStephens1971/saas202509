/**
 * Collection Actions Page - Major collection actions requiring board approval
 */

import { useState, useEffect } from 'react';
import { Scale, Check } from 'lucide-react';
import { getCollectionActions, approveCollectionAction, type CollectionAction } from '../api/delinquency';

export default function CollectionActionsPage() {
  const [actions, setActions] = useState<CollectionAction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadActions();
  }, []);

  const loadActions = async () => {
    try {
      const data = await getCollectionActions();
      setActions(data);
    } catch (err) {
      console.error('Failed to load actions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      await approveCollectionAction(id, 'Board');
      loadActions();
    } catch (err) {
      alert('Failed to approve action');
    }
  };

  if (loading) return <div className="text-center py-8">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Scale className="h-8 w-8 text-red-600" />
        <div>
          <h1 className="text-3xl font-bold">Collection Actions</h1>
          <p className="text-gray-600">Legal and board-level collection actions</p>
        </div>
      </div>

      <div className="grid gap-4">
        {actions.map((action) => (
          <div key={action.id} className="bg-white rounded-lg border p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold">{action.owner_name}</h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    action.status === 'approved' ? 'bg-green-100 text-green-800' :
                    action.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {action.status_display}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div>
                    <div className="text-sm text-gray-600">Action Type</div>
                    <div className="font-semibold text-red-600">{action.action_type_display}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Balance at Action</div>
                    <div className="font-semibold">${parseFloat(action.balance_at_action).toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Requested Date</div>
                    <div>{new Date(action.requested_date).toLocaleDateString()}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Attorney</div>
                    <div>{action.attorney_name || 'Not assigned'}</div>
                  </div>
                </div>
                {action.notes && (
                  <div className="mt-4 p-3 bg-gray-50 rounded">
                    <div className="text-sm text-gray-600 mb-1">Notes:</div>
                    <div className="text-sm">{action.notes}</div>
                  </div>
                )}
              </div>
              {action.status === 'pending' && (
                <button
                  onClick={() => handleApprove(action.id)}
                  className="ml-4 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
                >
                  <Check className="h-5 w-5" />
                  Approve
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
