import React, { useState } from 'react';
import { TelemetryMetrics } from '../types';

interface MissionControlViewProps {
  metrics: TelemetryMetrics;
  onUpdateDriveMode: (mode: string) => void;
}

export const MissionControlView: React.FC<MissionControlViewProps> = ({
  metrics,
  onUpdateDriveMode,
}) => {
  const [driveMode, setDriveMode] = useState('DIFFERENTIAL_CRAWL');
  const [antennaLock, setAntennaLock] = useState(true);
  const [rcsStatus, setRcsStatus] = useState('ARMED');

  const subsystems = [
    { name: 'RTG Nuclear Thermal', status: 'NOMINAL', val: '98.4%', temp: '142°C', icon: 'power' },
    { name: 'Differential Drive Motors', status: 'LOCKED', val: '4/4 ACTIVE', temp: '48°C', icon: 'settings_breathe' },
    { name: 'S-Band Orbiter Phased Array', status: antennaLock ? 'LINKED' : 'OCCLUDED', val: antennaLock ? '1.2 Mbps' : '0.1 Mbps', temp: '22°C', icon: 'radar' },
    { name: 'Laser Altimeter & LIDAR', status: 'SCANNING', val: '100 Hz', temp: '31°C', icon: 'sensors' },
    { name: 'Crater Thermal Shield', status: 'ACTIVE', val: '-180°C EXT', temp: '18°C INT', icon: 'shield' },
    { name: 'RCS Ascent Thruster Pods', status: rcsStatus, val: '220 bar', temp: '15°C', icon: 'rocket' },
  ];

  const handleDriveChange = (mode: string) => {
    setDriveMode(mode);
    onUpdateDriveMode(mode);
  };

  return (
    <div className="p-8 flex flex-col gap-6 select-none font-sans">
      {/* Top Banner */}
      <div className="bento-card-gradient p-6 flex flex-wrap justify-between items-center gap-6">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#3B82F6] block mb-1">
            ROVER APEX-7 STATUS
          </span>
          <h2 className="font-['Space_Grotesk'] text-2xl font-bold text-white tracking-tight">
            Primary Mission Overview
          </h2>
        </div>

        <div className="flex gap-3 font-mono text-xs">
          <div className="bg-[#161616] border border-[#262626] rounded-xl px-4 py-2.5">
            <span className="text-[#737373] block text-[10px] uppercase mb-0.5">Current Mode</span>
            <span className="text-white font-bold">{driveMode}</span>
          </div>
          <div className="bg-[#161616] border border-[#262626] rounded-xl px-4 py-2.5">
            <span className="text-[#737373] block text-[10px] uppercase mb-0.5">Battery SOC</span>
            <span className="text-[#10B981] font-bold">{metrics.battery}%</span>
          </div>
          <div className="bg-[#161616] border border-[#262626] rounded-xl px-4 py-2.5">
            <span className="text-[#737373] block text-[10px] uppercase mb-0.5">System Status</span>
            <span className="text-[#3B82F6] font-bold">ALL NOMINAL</span>
          </div>
        </div>
      </div>

      {/* Subsystem Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {subsystems.map((sub, i) => (
          <div key={i} className="bento-card p-5 flex flex-col gap-4">
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-2.5">
                <span className="material-symbols-outlined text-[#3B82F6] text-xl">{sub.icon}</span>
                <span className="font-['Space_Grotesk'] text-sm font-bold text-white">
                  {sub.name}
                </span>
              </div>
              <span className="text-[10px] bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/30 px-2 py-0.5 rounded-full font-mono font-medium">
                {sub.status}
              </span>
            </div>

            <div className="flex justify-between items-end border-t border-[#1F1F1F] pt-3 mt-1 font-mono text-xs">
              <div>
                <span className="text-[#737373] text-[10px] uppercase block mb-0.5">Output / Value</span>
                <span className="text-white font-bold">{sub.val}</span>
              </div>
              <div className="text-right">
                <span className="text-[#737373] text-[10px] uppercase block mb-0.5">Core Temp</span>
                <span className="text-[#3B82F6]">{sub.temp}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Drive Controls & Telemetry Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Drive Mode Selector */}
        <div className="bento-card p-6 flex flex-col gap-4">
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#737373] block mb-0.5">
              LOCOMOTION MATRIX
            </span>
            <h3 className="font-['Space_Grotesk'] text-base font-bold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-[#3B82F6]">directions_car</span>
              Rover Drive Configuration
            </h3>
          </div>

          <div className="grid grid-cols-3 gap-3 font-mono text-xs">
            {[
              { id: 'DIFFERENTIAL_CRAWL', label: 'CRAWL MODE', desc: '0.2 m/s Max Torque' },
              { id: 'STANDARD_TRAVERSE', label: 'TRAVERSE MODE', desc: '0.8 m/s Cruise' },
              { id: 'EMERGENCY_SPRINT', label: 'SPRINT MODE', desc: '1.5 m/s High Power' },
            ].map((mode) => (
              <button
                key={mode.id}
                onClick={() => handleDriveChange(mode.id)}
                className={`p-3.5 rounded-xl border text-left flex flex-col gap-1 cursor-pointer transition-all ${
                  driveMode === mode.id
                    ? 'border-[#3B82F6] bg-[#3B82F6]/10 text-white shadow-md font-bold'
                    : 'border-[#262626] bg-[#161616] text-[#A3A3A3] hover:text-white hover:bg-[#262626]'
                }`}
              >
                <span className="font-bold text-xs">{mode.label}</span>
                <span className="text-[10px] text-[#737373] font-normal">{mode.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Quick Override Controls */}
        <div className="bento-card p-6 flex flex-col gap-4">
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#737373] block mb-0.5">
              SYSTEM OVERRIDES
            </span>
            <h3 className="font-['Space_Grotesk'] text-base font-bold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-[#3B82F6]">tune</span>
              Manual Subsystem Toggles
            </h3>
          </div>

          <div className="grid grid-cols-2 gap-3 font-mono text-xs">
            <button
              onClick={() => setAntennaLock(!antennaLock)}
              className={`p-3.5 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                antennaLock
                  ? 'border-[#3B82F6]/40 text-[#3B82F6] bg-[#3B82F6]/10'
                  : 'border-[#EF4444]/40 text-[#EF4444] bg-[#EF4444]/10'
              }`}
            >
              <span className="font-medium text-[11px]">S-BAND TETHER</span>
              <span className="font-bold text-xs">{antennaLock ? 'ENABLED' : 'DISABLED'}</span>
            </button>

            <button
              onClick={() => setRcsStatus(rcsStatus === 'ARMED' ? 'SAFE' : 'ARMED')}
              className={`p-3.5 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                rcsStatus === 'ARMED'
                  ? 'border-[#F59E0B]/40 text-[#F59E0B] bg-[#F59E0B]/10'
                  : 'border-[#262626] text-[#A3A3A3] bg-[#161616]'
              }`}
            >
              <span className="font-medium text-[11px]">ASCENT RCS</span>
              <span className="font-bold text-xs">{rcsStatus}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
