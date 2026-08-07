import React, { useState, useEffect } from 'react';
import { AscentData } from '../types';

interface AscentModalProps {
  onClose: () => void;
}

export const AscentModal: React.FC<AscentModalProps> = ({ onClose }) => {
  const [ascent, setAscent] = useState<AscentData>({
    isAscending: true,
    stage: 'IGNITION',
    altitudeKm: 0,
    velocityKmS: 0,
    thrustPct: 100,
    fuelPct: 100,
    secondsRemaining: 180,
  });

  useEffect(() => {
    const timer = setInterval(() => {
      setAscent((prev) => {
        if (prev.secondsRemaining <= 0) {
          clearInterval(timer);
          return {
            ...prev,
            stage: 'ORBITAL_INSERTION',
            altitudeKm: 110.0,
            velocityKmS: 1.68,
            thrustPct: 0,
            fuelPct: 24,
            secondsRemaining: 0,
          };
        }

        const elapsed = 180 - prev.secondsRemaining + 1;
        let nextStage = prev.stage;
        if (elapsed > 10 && elapsed <= 40) nextStage = 'LIFT_OFF';
        if (elapsed > 40 && elapsed <= 90) nextStage = 'MAX_Q';
        if (elapsed > 90 && elapsed <= 150) nextStage = 'STAGE_SEPARATION';
        if (elapsed > 150) nextStage = 'ORBITAL_INSERTION';

        const nextAlt = parseFloat((elapsed * 0.61).toFixed(1));
        const nextVel = parseFloat((elapsed * 0.0093).toFixed(2));
        const nextFuel = Math.max(0, Math.round(100 - (elapsed / 180) * 76));

        return {
          ...prev,
          stage: nextStage,
          altitudeKm: nextAlt,
          velocityKmS: nextVel,
          fuelPct: nextFuel,
          secondsRemaining: prev.secondsRemaining - 1,
        };
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="fixed inset-0 bg-[#05080f]/90 backdrop-blur-md z-50 flex items-center justify-center p-4 select-none">
      <div className="bg-[#111625] border-2 border-[#06e0f9] p-8 w-full max-w-xl flex flex-col gap-6 shadow-2xl relative glow-active">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#bac9cc] hover:text-[#ffb4ab] cursor-pointer"
        >
          <span className="material-symbols-outlined text-xl">close</span>
        </button>

        <div className="flex items-center gap-3 border-b border-[#2a3441] pb-4">
          <span className="material-symbols-outlined text-[#06e0f9] text-3xl live-pulse">
            rocket_launch
          </span>
          <div>
            <h2 className="font-['Space_Grotesk'] text-xl font-bold text-[#b2f3ff] uppercase">
              LUNAR ASCENT ENGINE IGNITION
            </h2>
            <p className="font-['JetBrains_Mono'] text-xs text-[#bac9cc]">
              STAGE 1 MONOPROPELLANT ASCENT SEQUENCE ACTIVE
            </p>
          </div>
        </div>

        {/* Live Gauges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-['JetBrains_Mono'] text-xs">
          <div className="p-3 border border-[#2a3441] bg-[#05080f]">
            <span className="text-[#bac9cc] text-[10px] block">STAGE</span>
            <span className="text-[#06e0f9] font-bold">{ascent.stage}</span>
          </div>
          <div className="p-3 border border-[#2a3441] bg-[#05080f]">
            <span className="text-[#bac9cc] text-[10px] block">ALTITUDE</span>
            <span className="text-[#b2f3ff] font-bold">{ascent.altitudeKm} km</span>
          </div>
          <div className="p-3 border border-[#2a3441] bg-[#05080f]">
            <span className="text-[#bac9cc] text-[10px] block">VELOCITY</span>
            <span className="text-[#06e0f9] font-bold">{ascent.velocityKmS} km/s</span>
          </div>
          <div className="p-3 border border-[#2a3441] bg-[#05080f]">
            <span className="text-[#bac9cc] text-[10px] block">FUEL SOC</span>
            <span className="text-[#ffb950] font-bold">{ascent.fuelPct}%</span>
          </div>
        </div>

        {/* Thrust Bar */}
        <div className="flex flex-col gap-1 font-['JetBrains_Mono'] text-xs">
          <div className="flex justify-between text-[#bac9cc]">
            <span>THRUST OUTPUT</span>
            <span className="text-[#06e0f9] font-bold">{ascent.thrustPct}%</span>
          </div>
          <div className="w-full h-3 bg-[#05080f] border border-[#2a3441] p-0.5">
            <div
              className="h-full bg-[#06e0f9] transition-all duration-300 glow-active"
              style={{ width: `${ascent.thrustPct}%` }}
            />
          </div>
        </div>

        {/* Ascent Status Animation Card */}
        <div className="p-4 border border-[#2a3441] bg-[#05080f] text-center font-['JetBrains_Mono'] text-xs text-[#06e0f9] flex flex-col items-center justify-center gap-2">
          {ascent.secondsRemaining > 0 ? (
            <>
              <span className="material-symbols-outlined text-2xl animate-bounce text-[#06e0f9]">
                vertical_align_top
              </span>
              <span>ORBITAL TETHER COUNTDOWN: {ascent.secondsRemaining}s</span>
              <span className="text-[#bac9cc] text-[10px]">
                MAINTAINING TARGET VECTOR 18.2° TO LUNAR ORBITER RELAY
              </span>
            </>
          ) : (
            <>
              <span className="material-symbols-outlined text-3xl text-[#06e0f9]">
                check_circle
              </span>
              <span className="font-bold text-sm text-[#b2f3ff]">
                LUNAR ORBIT INSERTION SUCCESSFUL
              </span>
              <span className="text-[#bac9cc] text-[10px]">
                ASCENT VEHICLE LINKED WITH MOTHERSHIP COMMAND
              </span>
            </>
          )}
        </div>

        <button
          onClick={onClose}
          className="w-full py-3 bg-[#06e0f9] text-[#05080f] font-['Space_Grotesk'] font-bold text-sm uppercase hover:bg-[#b2f3ff] cursor-pointer glow-active"
        >
          {ascent.secondsRemaining > 0 ? 'MONITOR IN BACKGROUND' : 'CLOSE ASCENT WINDOW'}
        </button>
      </div>
    </div>
  );
};
