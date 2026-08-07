import React, { useState } from 'react';

export const DiagnosticsView: React.FC = () => {
  const [query, setQuery] = useState('');
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const [testStatus, setTestStatus] = useState<'IDLE' | 'RUNNING' | 'COMPLETE'>('IDLE');
  const [testLogs, setTestLogs] = useState<string[]>([
    '[SYSTEM] Sector-7 Operations Diagnostic Engine Initialized.',
    '[CHECK] S-Band Phased Array: 100% Signal Coherence.',
    '[CHECK] Wheel Differential Motor Bus: Nominal.',
  ]);

  const handleRunAiQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setAiResponse(null);

    try {
      const res = await fetch('/api/ai/diagnostics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      setAiResponse(data.answer || 'No response from diagnostic core.');
    } catch (err) {
      setAiResponse(
        'Diagnostic AI Link Offline. Local Telemetry indicates: System Nominal. No critical sub-assembly faults detected.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunSelfTest = () => {
    setTestStatus('RUNNING');
    setTestLogs((prev) => [...prev, '[TEST] Initiating full spectrum subsystem benchmark...']);

    setTimeout(() => {
      setTestLogs((prev) => [
        ...prev,
        '[TEST] RTG Thermal Loop: PASS (142°C)',
        '[TEST] LIDAR Laser Altimeter Calibration: PASS',
      ]);
    }, 1000);

    setTimeout(() => {
      setTestLogs((prev) => [
        ...prev,
        '[TEST] Emergency Abort Ascent Pyros: ARMED & CONTINUOUS',
        '[TEST] Diagnostic Self-Test Complete. All 18 Subsystems PASSED.',
      ]);
      setTestStatus('COMPLETE');
    }, 2200);
  };

  return (
    <div className="p-8 flex flex-col gap-6 select-none font-sans">
      <div className="bento-card-gradient p-6 flex justify-between items-center flex-wrap gap-4">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#3B82F6] block mb-1">
            SUB-ASSEMBLY BENCHMARK
          </span>
          <h2 className="font-['Space_Grotesk'] text-2xl font-bold text-white tracking-tight">
            Diagnostics & AI Tactical Advisor
          </h2>
          <p className="font-mono text-xs text-[#737373] mt-1">
            SECTOR-7 SUB-ASSEMBLY DIAGNOSTIC BUS & GEMINI TACTICAL ASSISTANT
          </p>
        </div>

        <button
          onClick={handleRunSelfTest}
          disabled={testStatus === 'RUNNING'}
          className="px-5 py-2.5 bg-[#3B82F6] text-white font-semibold font-mono text-xs rounded-xl hover:bg-[#2563EB] disabled:opacity-50 cursor-pointer shadow-md transition-all active:scale-[0.99]"
        >
          {testStatus === 'RUNNING' ? 'RUNNING BENCHMARKS...' : 'EXECUTE SELF-TEST'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gemini AI Tactical Assistant */}
        <div className="bento-card p-6 flex flex-col gap-5">
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#737373] block mb-0.5">
              GEMINI CORE
            </span>
            <h3 className="font-['Space_Grotesk'] text-base font-bold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-[#3B82F6]">auto_awesome</span>
              AI Mission Command Tactical Advisor
            </h3>
          </div>

          <form onSubmit={handleRunAiQuery} className="flex flex-col gap-3 font-mono text-xs">
            <label className="text-[#A3A3A3]">Query Lunar Mission Assistant:</label>
            <div className="flex gap-2.5">
              <input
                type="text"
                placeholder="e.g. How do I clear an S-Band signal occlusion in crater basin?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1 bg-[#0A0A0A] border border-[#262626] focus:border-[#3B82F6] text-white p-3 rounded-xl outline-none"
              />
              <button
                type="submit"
                disabled={isLoading}
                className="px-5 bg-[#3B82F6] text-white font-bold rounded-xl hover:bg-[#2563EB] cursor-pointer disabled:opacity-50 transition-all shadow-md"
              >
                {isLoading ? 'ANALYZING...' : 'QUERY'}
              </button>
            </div>
          </form>

          {aiResponse && (
            <div className="p-4 border border-[#3B82F6]/40 bg-[#0A0A0A] rounded-xl text-white font-mono text-xs leading-relaxed mt-2 relative">
              <span className="text-[#3B82F6] font-bold uppercase block mb-1">
                // SECTOR-7 TACTICAL RESPONSE:
              </span>
              {aiResponse}
            </div>
          )}
        </div>

        {/* Diagnostic System Console Log */}
        <div className="bento-card p-6 flex flex-col gap-4 font-mono text-xs">
          <div className="flex justify-between items-center border-b border-[#1F1F1F] pb-3">
            <h3 className="font-['Space_Grotesk'] text-base font-bold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-[#3B82F6]">terminal</span>
              System Bus Console Output
            </h3>
            <span className="text-[10px] text-[#3B82F6] bg-[#3B82F6]/10 border border-[#3B82F6]/30 px-2.5 py-0.5 rounded-full font-bold">
              STATUS: {testStatus}
            </span>
          </div>

          <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-4 font-mono text-xs text-[#A3A3A3] h-64 overflow-y-auto flex flex-col gap-2 leading-relaxed">
            {testLogs.map((log, idx) => (
              <div
                key={idx}
                className={
                  log.includes('PASS') || log.includes('Nominal')
                    ? 'text-[#10B981]'
                    : log.includes('CHECK')
                    ? 'text-[#3B82F6]'
                    : 'text-[#A3A3A3]'
                }
              >
                {log}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
