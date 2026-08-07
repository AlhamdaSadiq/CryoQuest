import React, { useState } from 'react';

interface Waypoint {
  id: number;
  x: number;
  y: number;
  label: string;
  slope: number;
}

export const TrajectoryPlannerView: React.FC = () => {
  const [waypoints, setWaypoints] = useState<Waypoint[]>([
    { id: 1, x: 15, y: 30, label: 'ALPHA_START', slope: 4.2 },
    { id: 2, x: 40, y: 55, label: 'BASIN_ENTRY', slope: 14.8 },
    { id: 3, x: 75, y: 70, label: 'CRATER_RIM', slope: 22.1 },
  ]);

  const [isSimulating, setIsSimulating] = useState(false);
  const [roverPos, setRoverPos] = useState({ x: 15, y: 30 });

  const handleMapClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isSimulating) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.round(((e.clientX - rect.left) / rect.width) * 100);
    const y = Math.round(((e.clientY - rect.top) / rect.height) * 100);

    const newWp: Waypoint = {
      id: waypoints.length + 1,
      x,
      y,
      label: `WAYPOINT_${waypoints.length + 1}`,
      slope: parseFloat((Math.random() * 20 + 3).toFixed(1)),
    };
    setWaypoints([...waypoints, newWp]);
  };

  const handleClearWaypoints = () => {
    setWaypoints([]);
    setIsSimulating(false);
    setRoverPos({ x: 15, y: 30 });
  };

  const handleRunSimulation = () => {
    if (waypoints.length < 2) return;
    setIsSimulating(true);

    let idx = 0;
    const timer = setInterval(() => {
      if (idx >= waypoints.length) {
        clearInterval(timer);
        setIsSimulating(false);
        return;
      }
      setRoverPos({ x: waypoints[idx].x, y: waypoints[idx].y });
      idx++;
    }, 1200);
  };

  const calculateTotalDistance = () => {
    let dist = 0;
    for (let i = 1; i < waypoints.length; i++) {
      const dx = waypoints[i].x - waypoints[i - 1].x;
      const dy = waypoints[i].y - waypoints[i - 1].y;
      dist += Math.sqrt(dx * dx + dy * dy) * 0.2;
    }
    return dist.toFixed(2);
  };

  return (
    <div className="p-8 flex flex-col gap-6 select-none font-sans">
      <div className="bento-card-gradient p-6 flex justify-between items-center flex-wrap gap-4">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#3B82F6] block mb-1">
            ROVER PATHFINDING ENGINE
          </span>
          <h2 className="font-['Space_Grotesk'] text-2xl font-bold text-white tracking-tight">
            Trajectory Pathfinder & Route Simulator
          </h2>
          <p className="font-mono text-xs text-[#737373] mt-1">
            CLICK ON MAP TO PLOT WAYPOINTS. RUN TRAVERSE SIMULATION.
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleClearWaypoints}
            className="px-4 py-2 bg-[#161616] border border-[#262626] text-[#A3A3A3] hover:text-white font-mono text-xs rounded-xl cursor-pointer transition-all"
          >
            RESET PATH
          </button>
          <button
            onClick={handleRunSimulation}
            disabled={isSimulating || waypoints.length < 2}
            className="px-5 py-2 bg-[#3B82F6] text-white font-semibold font-mono text-xs rounded-xl hover:bg-[#2563EB] disabled:opacity-50 cursor-pointer shadow-md transition-all active:scale-[0.99]"
          >
            {isSimulating ? 'SIMULATING TRAVERSE...' : 'RUN TRAVERSE SIMULATION'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Map Interactive Canvas */}
        <div className="lg:col-span-8 bento-card relative aspect-[4/3] overflow-hidden group p-0">
          <img
            alt="Crater Pathfinder Topography"
            className="absolute inset-0 w-full h-full object-cover mix-blend-screen opacity-65 contrast-125 grayscale"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuAorngXNlUnx8Fnja6TdOH66seEnIrFSitfi26kCTnFaNEBGnJsq0Di1EtkzHYTIQAoRwwziCCjNfdeN7ftVW3uA5Sd1h-nSgO7bX9GkrmkflvyufmZItSB2yVX3Pe1yY6JEru-in2XO1v9Hp0gw_SGDjpmNr493U6efl-HBWbl204z8MvI92gCgFdbdPbRP2A-zC4Dx7fDez5CnSzsgQJ1FSDnq5wxsja2AXz_0K9_hBhhQxp7sBJNcc4ukz-JD0ANc1Q"
          />

          <div
            onClick={handleMapClick}
            className="absolute inset-0 cursor-crosshair data-grid opacity-30"
          />

          {/* SVG Connecting Path Line */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none overflow-visible">
            {waypoints.length > 1 && (
              <polyline
                fill="none"
                stroke="#3B82F6"
                strokeWidth="2.5"
                strokeDasharray="4 4"
                points={waypoints.map((wp) => `${wp.x}%,${wp.y}%`).join(' ')}
              />
            )}
          </svg>

          {/* Waypoint Markers */}
          {waypoints.map((wp, i) => (
            <div
              key={wp.id}
              className="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none flex flex-col items-center"
              style={{ left: `${wp.x}%`, top: `${wp.y}%` }}
            >
              <div className="w-6 h-6 rounded-full border-2 border-[#3B82F6] bg-[#0A0A0A] flex items-center justify-center font-mono text-[11px] font-bold text-white shadow-lg">
                {i + 1}
              </div>
              <span className="font-mono text-[10px] text-[#3B82F6] bg-[#0A0A0A]/90 border border-[#262626] rounded-md px-1.5 py-0.5 mt-1 whitespace-nowrap shadow">
                {wp.label} ({wp.slope}°)
              </span>
            </div>
          ))}

          {/* Rover Position Marker */}
          {isSimulating && (
            <div
              className="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none transition-all duration-1000 ease-in-out z-20"
              style={{ left: `${roverPos.x}%`, top: `${roverPos.y}%` }}
            >
              <div className="w-9 h-9 border border-[#F59E0B] bg-[#F59E0B]/30 rounded-full flex items-center justify-center text-[#F59E0B] glow-active live-pulse">
                <span className="material-symbols-outlined text-base">precision_manufacturing</span>
              </div>
            </div>
          )}
        </div>

        {/* Waypoint Table & Route Summary */}
        <div className="lg:col-span-4 flex flex-col gap-4 font-mono text-xs">
          <div className="bento-card p-6 flex flex-col gap-4">
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#737373] block mb-0.5">
                ROUTE TELEMETRY
              </span>
              <h3 className="font-['Space_Grotesk'] text-base font-bold text-white uppercase">
                Plotted Route Specs
              </h3>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs border-y border-[#1F1F1F] py-3">
              <div>
                <span className="text-[#737373] block text-[10px] uppercase mb-0.5">Total Waypoints</span>
                <span className="text-white font-bold">{waypoints.length}</span>
              </div>
              <div>
                <span className="text-[#737373] block text-[10px] uppercase mb-0.5">Est. Path Distance</span>
                <span className="text-[#3B82F6] font-bold">{calculateTotalDistance()} km</span>
              </div>
            </div>

            <div className="flex flex-col gap-2 max-h-64 overflow-y-auto pr-1">
              {waypoints.map((wp, i) => (
                <div
                  key={wp.id}
                  className="p-3 border border-[#1F1F1F] bg-[#0A0A0A] rounded-xl flex justify-between items-center"
                >
                  <div>
                    <span className="text-[#3B82F6] font-bold mr-2">WP#{i + 1}</span>
                    <span className="text-white">{wp.label}</span>
                  </div>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full border font-mono ${
                      wp.slope > 18
                        ? 'text-[#EF4444] border-[#EF4444]/30 bg-[#EF4444]/10'
                        : 'text-[#3B82F6] border-[#3B82F6]/30 bg-[#3B82F6]/10'
                    }`}
                  >
                    SLOPE: {wp.slope}°
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
