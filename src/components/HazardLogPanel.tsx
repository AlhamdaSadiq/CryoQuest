import React, { useState } from 'react';
import { HazardItem, HazardSeverity } from '../types';

interface HazardLogPanelProps {
  hazards: HazardItem[];
  onAddHazard: (hazard: HazardItem) => void;
  onExportMatrix: () => void;
}

export const HazardLogPanel: React.FC<HazardLogPanelProps> = ({
  hazards,
  onAddHazard,
  onExportMatrix,
}) => {
  const [filter, setFilter] = useState<'ALL' | HazardSeverity>('ALL');
  const [showAddModal, setShowAddModal] = useState(false);

  // New Hazard Form State
  const [newTitle, setNewTitle] = useState('');
  const [newCode, setNewCode] = useState('WARN-02');
  const [newDistance, setNewDistance] = useState('5.5km');
  const [newSeverity, setNewSeverity] = useState<HazardSeverity>('WARNING');
  const [newDesc, setNewDesc] = useState('');

  const criticalCount = hazards.filter((h) => h.severity === 'CRITICAL').length;

  const filteredHazards = hazards.filter((h) => (filter === 'ALL' ? true : h.severity === filter));

  const handleCreateHazard = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    const item: HazardItem = {
      id: Date.now().toString(),
      code: newCode.toUpperCase(),
      title: newTitle,
      distance: newDistance,
      severity: newSeverity,
      description: newDesc || 'User logged telemetry anomaly.',
      attributes: [
        { label: 'SOURCE', value: 'MANUAL_SCAN' },
        { label: 'STATUS', value: 'ACTIVE', isDanger: newSeverity === 'CRITICAL' },
      ],
    };

    onAddHazard(item);
    setShowAddModal(false);
    setNewTitle('');
    setNewDesc('');
  };

  const getSeverityBorder = (sev: HazardSeverity) => {
    switch (sev) {
      case 'CRITICAL':
        return 'border-l-[#EF4444] text-[#EF4444]';
      case 'WARNING':
        return 'border-l-[#F59E0B] text-[#F59E0B]';
      case 'INFO':
        return 'border-l-[#3B82F6] text-[#3B82F6]';
    }
  };

  return (
    <div className="bento-card p-6 flex flex-col gap-5 select-none h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#1F1F1F] pb-3">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#737373] block mb-0.5">
            SURFACE THREAT MATRIX
          </span>
          <h3 className="font-['Space_Grotesk'] text-base font-bold text-white flex items-center gap-2">
            <span className="material-symbols-outlined text-[#3B82F6] text-lg">warning</span>
            Hazard Log
          </h3>
        </div>
        <span className="text-[11px] bg-[#EF4444]/10 text-[#EF4444] border border-[#EF4444]/30 px-2.5 py-1 rounded-full font-mono font-semibold">
          {criticalCount} CRITICAL
        </span>
      </div>

      {/* Filter Tabs */}
      <div className="flex bg-[#161616] border border-[#262626] rounded-xl p-1 text-[11px] font-mono">
        {(['ALL', 'CRITICAL', 'WARNING', 'INFO'] as const).map((sev) => (
          <button
            key={sev}
            onClick={() => setFilter(sev)}
            className={`flex-1 py-1.5 rounded-lg transition-all cursor-pointer font-medium ${
              filter === sev
                ? 'bg-[#3B82F6] text-white font-bold shadow-md'
                : 'text-[#A3A3A3] hover:text-white'
            }`}
          >
            {sev}
          </button>
        ))}
      </div>

      {/* Hazard Items Scroll Area */}
      <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-3 min-h-[280px]">
        {filteredHazards.map((item) => (
          <div
            key={item.id}
            className={`border border-[#1F1F1F] bg-[#0A0A0A] rounded-xl border-l-4 p-4 cursor-crosshair hover:border-[#333333] transition-all ${getSeverityBorder(
              item.severity
            )}`}
          >
            <div className="flex justify-between items-start mb-1.5">
              <span className="font-mono font-bold text-[11px] uppercase tracking-wider">
                {item.code}
              </span>
              <span className="font-mono text-[11px] text-[#737373]">
                D: {item.distance}
              </span>
            </div>

            <div className="font-['Space_Grotesk'] font-bold text-sm text-white mb-1">
              {item.title}
            </div>

            <div className="font-sans text-xs text-[#A3A3A3] mb-3 leading-relaxed">
              {item.description}
            </div>

            <div className="flex flex-wrap gap-2">
              {item.attributes.map((attr, idx) => (
                <span
                  key={idx}
                  className={`font-mono text-[10px] rounded-md px-2 py-0.5 border ${
                    attr.isDanger
                      ? 'border-[#EF4444]/30 text-[#EF4444] bg-[#EF4444]/10'
                      : 'border-[#262626] text-[#737373] bg-[#161616]'
                  }`}
                >
                  {attr.label}: {attr.value}
                </span>
              ))}
            </div>
          </div>
        ))}

        {filteredHazards.length === 0 && (
          <div className="p-8 text-center text-[#737373] font-mono text-xs border border-dashed border-[#262626] rounded-xl">
            No hazard anomalies matching current filter.
          </div>
        )}
      </div>

      {/* Action Buttons Footer */}
      <div className="flex flex-col gap-2.5 mt-auto">
        <button
          onClick={() => setShowAddModal(true)}
          className="w-full py-2.5 bg-[#161616] hover:bg-[#262626] border border-[#262626] text-[#A3A3A3] hover:text-white font-mono text-xs rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <span className="material-symbols-outlined text-base">add_alert</span>
          LOG HAZARD ANOMALY
        </button>

        <button
          onClick={onExportMatrix}
          className="w-full py-3 bg-[#1A1A1A] hover:bg-[#262626] border border-[#333333] hover:border-[#3B82F6] text-[#3B82F6] hover:text-white font-semibold text-xs rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer shadow-sm active:scale-[0.99]"
        >
          <span className="material-symbols-outlined text-base">download</span>
          EXPORT HAZARD MATRIX
        </button>
      </div>

      {/* Add Hazard Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-[#0A0A0A]/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-[#161616] border border-[#262626] rounded-2xl p-6 w-full max-w-md flex flex-col gap-5 shadow-2xl">
            <div className="flex justify-between items-center border-b border-[#262626] pb-3">
              <h4 className="font-['Space_Grotesk'] text-base font-bold text-white flex items-center gap-2">
                <span className="material-symbols-outlined text-[#3B82F6]">add_alert</span> Log Terrain Anomaly
              </h4>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-[#737373] hover:text-white cursor-pointer"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <form onSubmit={handleCreateHazard} className="flex flex-col gap-4 font-mono text-xs">
              <div>
                <label className="block text-[#A3A3A3] mb-1.5 font-medium">Hazard Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sub-surface Thermal Cavity"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-[#0A0A0A] border border-[#262626] focus:border-[#3B82F6] text-white p-2.5 rounded-xl outline-none"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-[#A3A3A3] mb-1.5 font-medium">Code</label>
                  <input
                    type="text"
                    value={newCode}
                    onChange={(e) => setNewCode(e.target.value)}
                    className="w-full bg-[#0A0A0A] border border-[#262626] focus:border-[#3B82F6] text-white p-2.5 rounded-xl outline-none uppercase"
                  />
                </div>
                <div>
                  <label className="block text-[#A3A3A3] mb-1.5 font-medium">Distance</label>
                  <input
                    type="text"
                    value={newDistance}
                    onChange={(e) => setNewDistance(e.target.value)}
                    className="w-full bg-[#0A0A0A] border border-[#262626] focus:border-[#3B82F6] text-white p-2.5 rounded-xl outline-none"
                  />
                </div>
                <div>
                  <label className="block text-[#A3A3A3] mb-1.5 font-medium">Severity</label>
                  <select
                    value={newSeverity}
                    onChange={(e) => setNewSeverity(e.target.value as HazardSeverity)}
                    className="w-full bg-[#0A0A0A] border border-[#262626] focus:border-[#3B82F6] text-white p-2.5 rounded-xl outline-none"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="WARNING">WARNING</option>
                    <option value="INFO">INFO</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[#A3A3A3] mb-1.5 font-medium">Description</label>
                <textarea
                  rows={3}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Detailed radar anomaly or surface obstruction specs..."
                  className="w-full bg-[#0A0A0A] border border-[#262626] focus:border-[#3B82F6] text-white p-2.5 rounded-xl outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 mt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 border border-[#262626] text-[#A3A3A3] hover:text-white rounded-xl cursor-pointer"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-[#3B82F6] text-white font-bold rounded-xl hover:bg-[#2563EB] cursor-pointer shadow-md"
                >
                  SAVE HAZARD
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
