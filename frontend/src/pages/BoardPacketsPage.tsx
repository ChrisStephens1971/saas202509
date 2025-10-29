/**
 * Board Packets Page - Generate comprehensive board packets
 */

import { useState, useEffect } from 'react';
import { FileText, Plus, Download, Send } from 'lucide-react';
import { getBoardPackets, generatePDF, sendEmail, type BoardPacket } from '../api/boardPackets';

export default function BoardPacketsPage() {
  const [packets, setPackets] = useState<BoardPacket[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getBoardPackets().then(setPackets).finally(() => setLoading(false));
  }, []);

  const handleGenerate = async (id: string) => {
    try {
      await generatePDF(id);
      alert('PDF generation started');
    } catch (err) {
      alert('Failed to generate PDF');
    }
  };

  const handleSend = async (id: string) => {
    const emails = prompt('Enter email addresses (comma-separated):');
    if (!emails) return;
    try {
      await sendEmail(id, emails.split(',').map(e => e.trim()));
      alert('Packet sent successfully');
    } catch (err) {
      alert('Failed to send packet');
    }
  };

  if (loading) return <div className="text-center py-8">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold">Board Packets</h1>
            <p className="text-gray-600">Generate comprehensive meeting packets</p>
          </div>
        </div>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2">
          <Plus className="h-5 w-5" />
          New Packet
        </button>
      </div>

      <div className="grid gap-4">
        {packets.map((packet) => (
          <div key={packet.id} className="bg-white rounded-lg border p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold">
                    Board Meeting - {new Date(packet.meeting_date).toLocaleDateString()}
                  </h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    packet.status === 'ready' ? 'bg-green-100 text-green-800' :
                    packet.status === 'generating' ? 'bg-blue-100 text-blue-800' :
                    packet.status === 'sent' ? 'bg-purple-100 text-purple-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {packet.status_display}
                  </span>
                </div>
                <div className="text-sm text-gray-600 mb-3">Template: {packet.template_name}</div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm text-gray-600">Sections</div>
                    <div className="font-semibold">{packet.sections?.length || 0}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Pages</div>
                    <div className="font-semibold">{packet.page_count || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Recipients</div>
                    <div className="font-semibold">{packet.sent_to?.length || 0}</div>
                  </div>
                </div>
              </div>
              <div className="ml-4 flex gap-2">
                {packet.status === 'draft' && (
                  <button
                    onClick={() => handleGenerate(packet.id)}
                    className="bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2 text-sm"
                  >
                    <FileText className="h-4 w-4" />
                    Generate
                  </button>
                )}
                {packet.status === 'ready' && (
                  <>
                    <button className="bg-green-600 text-white px-3 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2 text-sm">
                      <Download className="h-4 w-4" />
                      Download
                    </button>
                    <button
                      onClick={() => handleSend(packet.id)}
                      className="bg-purple-600 text-white px-3 py-2 rounded-lg hover:bg-purple-700 flex items-center gap-2 text-sm"
                    >
                      <Send className="h-4 w-4" />
                      Send
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        {packets.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No board packets yet. Click "New Packet" to create one.
          </div>
        )}
      </div>
    </div>
  );
}
