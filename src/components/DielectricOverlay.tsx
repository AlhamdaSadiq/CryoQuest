import React, { useState } from 'react';
import { BandType, Coordinates } from '../types';

interface DielectricOverlayProps {
  currentCoords: Coordinates;
  onSelectCoords: (coords: Coordinates) => void;
  selectedBand: BandType;
  setSelectedBand: (band: BandType) => void;
  reflectance: string;
  roughness: string;
  dielectric: string;
  altitude: string;
  onRunAiAnalysis?: () => void;
  isAiLoading?: boolean;
  mapImageUrl?: string;
}

const DEFAULT_MAP_IMAGE =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuAorngXNlUnx8Fnja6TdOH66seEnIrFSitfi26kCTnFaNEBGnJsq0Di1EtkzHYTIQAoRwwziCCjNfdeN7ftVW3uA5Sd1h-nSgO7bX9GkrmkflvyufmZItSB2yVX3Pe1yY6JEru-in2XO1v9Hp0gw_SGDjpmNr493U6efl-HBWbl204z8MvI92gCgFdbdPbRP2A-zC4Dx7fDez5CnSzsgQJ1FSDnq5wxsja2AXz_0K9_hBhhQxp7sBJNcc4ukz-JD0ANc1Q';

export const DielectricOverlay: React.FC<DielectricOverlayProps> = ({
  currentCoords,
  onSelectCoords,
  selectedBand,
  setSelectedBand,
  reflectance,
  roughness,
  dielectric,
  altitude,
  onRunAiAnalysis,
  isAiLoading,
  mapImageUrl,
}) => {
  const [clickPoint, setClickPoint] = useState<{ xPct: number; yPct: number }>({
    xPct: 50,
    yPct: 50,
  });

  const handleMapClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const xPct = Math.max(5, Math.min(95, (x / rect.width) * 100));
    const yPct = Math.max(5, Math.min(95, (y / rect.height) * 100));

    setClickPoint({ xPct, yPct });

    // Calculate new virtual coordinates based on click
    const newLat = 42.12 + (50 - yPct) * 0.005;
    const newLon = 18.45 + (xPct - 50) * 0.005;
    onSelectCoords({ lat: parseFloat(newLat.toFixed(4)), lon: parseFloat(newLon.toFixed(4)) });
  };

  // Spectral overlay color filters based on band
  const getFilterStyle = () => {
    switch (selectedBand) {
      case 'L-BAND':
        return 'contrast-125 grayscale mix-blend-screen opacity-70';
      case 'S-BAND':
        return 'contrast-150 hue-rotate-180 sepia opacity-80';
      case 'INFRARED':
        return 'contrast-150 invert opacity-75 blur-[0.3px]';
      case 'RADAR':
        return 'contrast-200 saturate-200 opacity-90';
      default:
        return 'contrast-125 grayscale opacity-70';
    }
  };

  return (
    <div className="bento-card p-6 flex flex-col gap-5 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#1F1F1F] pb-3">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#737373] block mb-0.5">
            SPECTRAL RADAR SENSOR
          </span>
          <h3 className="font-['Space_Grotesk'] text-base font-bold text-white flex items-center gap-2">
            <span className="material-symbols-outlined text-[#3B82F6] text-lg">layers</span>
            Dielectric Overlay Map
          </h3>
        </div>
        <div className="flex items-center gap-2 bg-[#161616] border border-[#262626] rounded-full px-3 py-1">
          <span className="w-2 h-2 rounded-full bg-[#3B82F6] live-pulse" />
          <span className="font-mono text-[11px] font-medium text-[#3B82F6]">
            {selectedBand}
          </span>
        </div>
      </div>

      {/* Map Display Box */}
      <div
        onClick={handleMapClick}
        className="relative w-full aspect-square border border-[#1F1F1F] rounded-2xl bg-[#0A0A0A] overflow-hidden group cursor-crosshair shadow-inner"
      >
        {/* Map Image Placeholder */}
        <img
          alt="Lunar Ice-Probability Fusion Map"
          className={`absolute inset-0 w-full h-full object-cover transition-all duration-300 ${getFilterStyle()}`}
          src={mapImageUrl || DEFAULT_MAP_IMAGE}
        />

        {/* Tactical Grid Background Overlay */}
        <div className="absolute inset-0 border border-[#3B82F6]/20 pointer-events-none data-grid opacity-30" />

        {/* Scanning Laser Line Animation */}
        <div className="laser-line pointer-events-none" />

        {/* Dynamic Target Reticle */}
        <div
          className="absolute w-16 h-16 border border-[#3B82F6]/70 rounded-full pointer-events-none -translate-x-1/2 -translate-y-1/2 transition-all duration-150 ease-out"
          style={{ left: `${clickPoint.xPct}%`, top: `${clickPoint.yPct}%` }}
        >
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2.5 h-2.5 bg-[#3B82F6] rounded-full glow-active" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-full w-px h-full bg-[#3B82F6]/50" />
          <div className="absolute top-1/2 left-0 -translate-x-full -translate-y-1/2 w-full h-px bg-[#3B82F6]/50" />
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-full w-px h-full bg-[#3B82F6]/50" />
          <div className="absolute top-1/2 right-0 translate-x-full -translate-y-1/2 w-full h-px bg-[#3B82F6]/50" />
        </div>

        {/* Coordinates Readout Overlay Top Left */}
        <div className="absolute top-4 left-4 bg-[#0A0A0A]/85 border border-[#262626] rounded-xl p-2.5 backdrop-blur-md pointer-events-none shadow-md">
          <div className="font-mono text-[10px] text-[#737373] uppercase mb-0.5">TARGET LAT / LON</div>
          <div className="font-mono font-bold text-xs text-[#3B82F6]">
            {currentCoords.lat.toFixed(4)}° N<br />
            {currentCoords.lon.toFixed(4)}° E
          </div>
        </div>

        {/* Altitude Readout Overlay Bottom Right */}
        <div className="absolute bottom-4 right-4 bg-[#0A0A0A]/85 border border-[#262626] rounded-xl p-2.5 backdrop-blur-md text-right pointer-events-none shadow-md">
          <div className="font-mono text-[10px] text-[#737373] uppercase mb-0.5">ALTITUDE</div>
          <div className="font-mono font-bold text-xs text-[#3B82F6]">
            {altitude} km
          </div>
        </div>

        {/* Band Mode Toggle Controls Overlay Bottom Left */}
        <div className="absolute bottom-4 left-4 flex bg-[#0A0A0A]/90 border border-[#262626] rounded-xl p-1 z-20 backdrop-blur-md">
          {(['L-BAND', 'S-BAND', 'INFRARED', 'RADAR'] as BandType[]).map((band) => (
            <button
              key={band}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedBand(band);
              }}
              className={`px-3 py-1 font-mono font-bold text-[11px] rounded-lg transition-all cursor-pointer ${
                selectedBand === band
                  ? 'bg-[#3B82F6] text-white shadow-md glow-active'
                  : 'text-[#A3A3A3] hover:text-white hover:bg-[#1A1A1A]'
              }`}
            >
              {band}
            </button>
          ))}
        </div>
      </div>

      {/* Telemetry Stats Below Map */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-[#161616] border border-[#262626] rounded-xl p-3.5">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[#737373] block mb-1">
            Reflectance
          </span>
          <div className="font-mono font-bold text-base text-white">
            {reflectance} <span className="text-xs text-[#3B82F6]">μ</span>
          </div>
        </div>
        <div className="bg-[#161616] border border-[#262626] rounded-xl p-3.5">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[#737373] block mb-1">
            Roughness
          </span>
          <div className="font-mono font-bold text-base text-white">
            RMS {roughness}
          </div>
        </div>
        <div className="bg-[#161616] border border-[#262626] rounded-xl p-3.5">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[#737373] block mb-1">
            Dielectric
          </span>
          <div className="font-mono font-bold text-base text-white">
            ε = {dielectric}
          </div>
        </div>
      </div>

      {/* AI Terrain Analysis Trigger */}
      {onRunAiAnalysis && (
        <button
          onClick={onRunAiAnalysis}
          disabled={isAiLoading}
          className="w-full py-3 bg-[#1A1A1A] hover:bg-[#262626] border border-[#333333] hover:border-[#3B82F6] text-[#3B82F6] hover:text-white font-semibold text-xs rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 active:scale-[0.99] shadow-sm"
        >
          <span className="material-symbols-outlined text-base">
            {isAiLoading ? 'sync' : 'auto_awesome'}
          </span>
          {isAiLoading ? 'SCANNING SURFACE SPECTRA...' : 'AI SPECTRAL TERRAIN EVALUATION'}
        </button>
      )}
    </div>
  );
};
