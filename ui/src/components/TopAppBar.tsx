import React, { useState, useEffect } from 'react';
import { Coordinates } from '../types';

interface TopAppBarProps {
  currentCoords: Coordinates;
  onEmergencyAbort: () => void;
  batteryPct: number;
  subTitle?: string;
}

export const TopAppBar: React.FC<TopAppBarProps> = ({
  currentCoords,
  onEmergencyAbort,
  batteryPct,
  subTitle = 'CRATER ANALYSIS',
}) => {
  const [secondsElapsed, setSecondsElapsed] = useState(511702);

  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatMissionTime = (totalSec: number) => {
    const hrs = Math.floor(totalSec / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const secs = totalSec % 60;
    return `T+${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <header className="h-20 border-b border-[#1F1F1F] bg-[#0A0A0A] flex justify-between items-center px-8 w-full sticky top-0 z-40 transition-all duration-200 select-none">
      <div className="flex items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="font-['Space_Grotesk'] text-lg font-bold text-white tracking-tight">
              MISSION ALPHA-1
            </h2>
            <span className="text-[11px] bg-[#161616] text-[#3B82F6] border border-[#262626] px-2.5 py-0.5 rounded-full font-mono font-medium">
              {subTitle}
            </span>
          </div>
          <div className="flex items-center gap-3 font-['JetBrains_Mono'] text-xs text-[#737373] mt-1">
            <span>LAT: {currentCoords.lat.toFixed(2)}°N</span>
            <span>LON: {currentCoords.lon.toFixed(2)}°E</span>
            <span className="text-[#3B82F6] font-bold">{formatMissionTime(secondsElapsed)}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Battery SOC Pill */}
        <div className="bg-[#161616] border border-[#262626] rounded-xl px-3 py-1.5 flex items-center gap-2 text-xs">
          <span className="material-symbols-outlined text-[#10B981] text-base">battery_charging_full</span>
          <span className="font-mono font-bold text-white">{batteryPct}%</span>
        </div>

        {/* System Link Status Pill */}
        <div className="bg-[#161616] border border-[#262626] rounded-xl px-3 py-1.5 flex items-center gap-2 text-xs hidden sm:flex">
          <span className="w-2 h-2 rounded-full bg-[#10B981] live-pulse" />
          <span className="font-mono text-[#A3A3A3] text-[11px]">S-BAND 1.2 Mbps</span>
        </div>

        {/* Link to the Python analysis dashboard (Streamlit) */}
        <a
          href="http://localhost:8501"
          target="_blank"
          rel="noopener noreferrer"
          className="bg-[#161616] hover:bg-[#1A1A1A] border border-[#262626] hover:border-[#3B82F6] text-[#A3A3A3] hover:text-[#3B82F6] font-semibold text-xs rounded-xl px-3 py-2 transition-all cursor-pointer flex items-center gap-1.5 shadow-sm"
          title="Open the pipeline analysis dashboard (Streamlit, app.py)"
        >
          <span className="material-symbols-outlined text-base">query_stats</span>
          <span className="hidden md:inline">ANALYSIS DASHBOARD</span>
        </a>

        {/* Emergency Abort Button */}
        <button
          onClick={onEmergencyAbort}
          className="bg-[#EF4444]/10 hover:bg-[#EF4444] text-[#EF4444] hover:text-white border border-[#EF4444]/30 font-semibold text-xs rounded-xl px-4 py-2 transition-all cursor-pointer flex items-center gap-1.5 active:scale-95 shadow-sm"
        >
          <span className="material-symbols-outlined text-base">warning</span>
          ABORT
        </button>

        {/* User Profile Avatar */}
        <div className="w-9 h-9 rounded-xl bg-[#161616] border border-[#262626] flex items-center justify-center text-xs font-bold text-[#E5E5E5] overflow-hidden">
          <img
            className="w-full h-full object-cover opacity-80"
            alt="Space operator avatar"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuB6oR9-MqTFH7X8l_J0NPkFwyimCQsEVPbGasVtJBITPyDWPVtxVVYozrIojVY3EJXEUUda6EHNnquXIfew6AUZ4I-qh1fIm1YYqpPmtJgKSRCxJoXNGy6KjqXIp72sBMsWlU-BNC_Nf5q9F0FlETNgQkdeZiBjDD91XBWavm-55B5vFtfa2jTj4jAxILdgwdrjEUiDehlnYK-ukwLepuSm5LyGY2PiFWRehmE5aimZg3PEQzMOb0Kkpw"
          />
        </div>
      </div>
    </header>
  );
};
