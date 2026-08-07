import React, { useState } from 'react';

interface EmergencyAbortModalProps {
  onClose: () => void;
  onConfirmAbort: () => void;
}

export const EmergencyAbortModal: React.FC<EmergencyAbortModalProps> = ({
  onClose,
  onConfirmAbort,
}) => {
  const [overrideKey, setOverrideKey] = useState('');
  const [isAborted, setIsAborted] = useState(false);

  const handleAbortExecute = (e: React.FormEvent) => {
    e.preventDefault();
    setIsAborted(true);
    onConfirmAbort();
  };

  return (
    <div className="fixed inset-0 bg-[#93000a]/40 backdrop-blur-md z-50 flex items-center justify-center p-4 select-none">
      <div className="bg-[#111625] border-2 border-[#ffb4ab] p-8 w-full max-w-lg flex flex-col gap-6 shadow-2xl relative error-pulse">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#bac9cc] hover:text-[#ffb4ab] cursor-pointer"
        >
          <span className="material-symbols-outlined text-xl">close</span>
        </button>

        <div className="flex items-center gap-3 border-b border-[#2a3441] pb-4">
          <span className="material-symbols-outlined text-[#ffb4ab] text-4xl animate-ping">
            warning
          </span>
          <div>
            <h2 className="font-['Space_Grotesk'] text-xl font-bold text-[#ffb4ab] uppercase">
              EMERGENCY ABORT OVERRIDE
            </h2>
            <p className="font-['JetBrains_Mono'] text-xs text-[#bac9cc]">
              SECTOR-7 CRITICAL MISSION TERMINATION SEQUENCE
            </p>
          </div>
        </div>

        {!isAborted ? (
          <form onSubmit={handleAbortExecute} className="flex flex-col gap-4 font-['JetBrains_Mono'] text-xs">
            <div className="p-3 border border-[#ffb4ab] bg-[#93000a]/20 text-[#ffb4ab] leading-relaxed">
              WARNING: Executing emergency abort will fire pyrotechnic decouplers, jettison heavy science payloads, and initiate instant launch thrusters.
            </div>

            <div>
              <label className="block text-[#bac9cc] mb-1">Enter Override Key to Confirm Abort:</label>
              <input
                type="text"
                placeholder="Type 'ABORT-7'"
                value={overrideKey}
                onChange={(e) => setOverrideKey(e.target.value)}
                className="w-full bg-[#05080f] border border-[#ffb4ab] text-[#ffb4ab] p-3 font-bold uppercase focus:outline-none"
              />
            </div>

            <div className="flex gap-3 mt-2">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 py-3 border border-[#2a3441] text-[#bac9cc] hover:bg-[#1a233a] cursor-pointer font-bold"
              >
                CANCEL & RESUME MISSION
              </button>
              <button
                type="submit"
                disabled={overrideKey.toUpperCase() !== 'ABORT-7'}
                className="flex-1 py-3 bg-[#ffb4ab] text-[#05080f] font-bold uppercase hover:bg-[#ffdad6] disabled:opacity-40 cursor-pointer"
              >
                EXECUTE ABORT
              </button>
            </div>
          </form>
        ) : (
          <div className="flex flex-col gap-4 text-center font-['JetBrains_Mono'] text-xs">
            <div className="p-4 bg-[#93000a] text-[#ffdad6] font-bold text-sm uppercase border border-[#ffb4ab]">
              EMERGENCY ABORT INITIATED. JETTISON COMPLETED.
            </div>
            <p className="text-[#bac9cc]">
              Telemetry buses locked. Automatic rescue signal transmitted via S-Band relay.
            </p>
            <button
              onClick={onClose}
              className="py-3 bg-[#06e0f9] text-[#05080f] font-bold uppercase hover:bg-[#b2f3ff] cursor-pointer"
            >
              RETURN TO CONTROL CONSOLE
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
