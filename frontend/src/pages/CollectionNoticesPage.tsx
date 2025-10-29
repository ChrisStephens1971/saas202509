/**
 * Collection Notices Page - View and manage collection notices
 */

import { useState, useEffect } from 'react';
import { Mail, AlertCircle } from 'lucide-react';
import { getCollectionNotices, type CollectionNotice } from '../api/delinquency';

export default function CollectionNoticesPage() {
  const [notices, setNotices] = useState<CollectionNotice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNotices();
  }, []);

  const loadNotices = async () => {
    try {
      const data = await getCollectionNotices();
      setNotices(data);
    } catch (err) {
      console.error('Failed to load notices:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center py-8">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Collection Notices</h1>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2">
          <Mail className="h-5 w-5" />
          Send Notice
        </button>
      </div>

      <div className="bg-white rounded-lg border">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Owner</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notice Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sent Date</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Balance</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tracking</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {notices.map((notice) => (
              <tr key={notice.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium">{notice.owner_name}</td>
                <td className="px-6 py-4">
                  <span className="px-2 py-1 text-xs rounded-full bg-orange-100 text-orange-800">
                    {notice.notice_type_display}
                  </span>
                </td>
                <td className="px-6 py-4">{new Date(notice.sent_date).toLocaleDateString()}</td>
                <td className="px-6 py-4 font-semibold">${parseFloat(notice.balance_at_notice).toLocaleString()}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{notice.tracking_number || 'N/A'}</td>
                <td className="px-6 py-4">
                  {notice.delivered_date ? (
                    <span className="text-green-600">Delivered {new Date(notice.delivered_date).toLocaleDateString()}</span>
                  ) : notice.returned_undeliverable ? (
                    <span className="flex items-center gap-1 text-red-600">
                      <AlertCircle className="h-4 w-4" />
                      Undeliverable
                    </span>
                  ) : (
                    <span className="text-gray-500">In Transit</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
