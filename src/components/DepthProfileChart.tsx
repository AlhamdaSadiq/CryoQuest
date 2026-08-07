import React, { useState } from 'react';

interface DepthProfileChartProps {
  maxSlope: string;
  status: 'GO' | 'NO-GO ZONE' | 'CAUTION';
  onSelectWaypoint?: (km: number, depthKm: number) => void;
}

export const DepthProfileChart: React.FC<DepthProfileChartProps> = ({
  maxSlope,
  status,
  onSelectWaypoint,
}) => {
  const [scannerX, setScannerX] = useState<number>(40);

  const handleChartClick = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const xRatio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const distanceKm = parseFloat((xRatio * 20).toFixed(1));

    const centerNorm = Math.abs(xRatio - 0.5) * 2;
    const depthKm = parseFloat((-3.0 + centerNorm * 2.0).toFixed(2));

    setScannerX(xRatio * 100);

    if (onSelectWaypoint) {
      onSelectWaypoint(distanceKm, depthKm);
    }
  };

  return (
    <div className="bento-card p-6 flex flex-col gap-5 select-none h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#1F1F1F] pb-3">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#737373] block mb-0.5">
            CRATER TOPOGRAPHY
          </span>
          <h3 className="font-['Space_Grotesk'] text-base font-bold text-white flex items-center gap-2">
            <span className="material-symbols-outlined text-[#3B82F6] text-lg">show_chart</span>
            Depth Profile (Axis Z)
          </h3>
        </div>
        <span className="text-[11px] bg-[#161616] text-[#737373] border border-[#262626] px-2.5 py-1 rounded-full font-mono font-medium">
          20 KM SCAN
        </span>
      </div>

      {/* Main Graph Box */}
      <div className="flex-1 bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-5 flex flex-col relative min-h-[360px]">
        {/* Top Metric Header */}
        <div className="font-mono text-[11px] text-[#737373] mb-4 flex justify-between uppercase">
          <span>SURFACE LEVEL (0 km)</span>
          <span>DISTANCE (km)</span>
        </div>

        {/* Chart Area Container */}
        <div className="flex-1 relative border-l border-b border-[#262626] mt-2 mb-6 ml-8">
          {/* Y-Axis Depth Labels */}
          <div className="absolute -left-8 top-0 font-mono text-[10px] text-[#737373]">
            -1.0
          </div>
          <div className="absolute -left-8 top-1/4 font-mono text-[10px] text-[#737373]">
            -1.5
          </div>
          <div className="absolute -left-8 top-2/4 font-mono text-[10px] text-[#737373]">
            -2.0
          </div>
          <div className="absolute -left-8 top-3/4 font-mono text-[10px] text-[#737373]">
            -2.5
          </div>
          <div className="absolute -left-8 bottom-0 font-mono text-[10px] text-[#737373]">
            -3.0
          </div>

          {/* Grid Guidelines */}
          <div className="absolute w-full h-px top-1/4 bg-[#1F1F1F]" />
          <div className="absolute w-full h-px top-2/4 bg-[#1F1F1F]" />
          <div className="absolute w-full h-px top-3/4 bg-[#1F1F1F]" />

          {/* X-Axis Distance Labels */}
          <div className="absolute -bottom-5 left-0 font-mono text-[10px] text-[#737373]">
            0
          </div>
          <div className="absolute -bottom-5 left-1/4 font-mono text-[10px] text-[#737373]">
            5
          </div>
          <div className="absolute -bottom-5 left-1/2 font-mono text-[10px] text-[#737373]">
            10
          </div>
          <div className="absolute -bottom-5 left-3/4 font-mono text-[10px] text-[#737373]">
            15
          </div>
          <div className="absolute -bottom-5 right-0 font-mono text-[10px] text-[#737373]">
            20
          </div>

          {/* SVG Line Chart */}
          <svg
            onClick={handleChartClick}
            className="absolute inset-0 w-full h-full overflow-visible cursor-pointer"
            preserveAspectRatio="none"
            viewBox="0 0 100 100"
          >
            <defs>
              <linearGradient id="chartGlow" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity="0" />
              </linearGradient>
            </defs>

            {/* Gradient Area Fill */}
            <path
              d="M 0 20 L 10 22 L 20 28 L 30 45 L 40 85 L 50 90 L 60 82 L 70 40 L 80 25 L 90 21 L 100 20 L 100 100 L 0 100 Z"
              fill="url(#chartGlow)"
            />

            {/* Polyline Surface Contour */}
            <polyline
              className="glow-active draw-path"
              fill="none"
              points="0,20 10,22 20,28 30,45 40,85 50,90 60,82 70,40 80,25 90,21 100,20"
              stroke="#3B82F6"
              strokeWidth="2.5"
              vectorEffect="non-scaling-stroke"
            />

            {/* Critical Hazard Alert Points */}
            <circle className="animate-pulse" cx="40" cy="85" fill="#EF4444" r="3.5" />
            <circle className="animate-pulse" cx="50" cy="90" fill="#EF4444" r="3.5" />
            <circle cx="70" cy="40" fill="#F59E0B" r="3.5" />
          </svg>

          {/* Vertical Interactive Scanner Line */}
          <div
            className="absolute top-0 bottom-0 w-px bg-[#3B82F6] pointer-events-none transition-all duration-150"
            style={{ left: `${scannerX}%` }}
          >
            <div className="absolute -top-1 -left-1 w-2.5 h-2.5 bg-[#3B82F6] rounded-full glow-active" />
            <div className="absolute bottom-0 -left-6 bg-[#0A0A0A] border border-[#3B82F6] text-[#3B82F6] font-mono text-[9px] px-1.5 py-0.5 rounded">
              {(scannerX * 0.2).toFixed(1)}km
            </div>
          </div>
        </div>

        {/* Slope Data Box Bottom */}
        <div className="mt-auto bg-[#161616] border border-[#262626] rounded-xl p-3.5">
          <div className="flex justify-between items-end">
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#737373] block mb-1">
                Max Slope Gradient
              </span>
              <div
                className={`font-mono font-bold text-xl ${
                  status === 'NO-GO ZONE'
                    ? 'text-[#EF4444]'
                    : status === 'CAUTION'
                    ? 'text-[#F59E0B]'
                    : 'text-[#3B82F6]'
                }`}
              >
                {maxSlope}°
              </div>
            </div>

            <div className="text-right">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#737373] block mb-1">
                Traverse Status
              </span>
              <div
                className={`text-xs font-bold px-3 py-1 rounded-full uppercase inline-block border ${
                  status === 'NO-GO ZONE'
                    ? 'text-[#EF4444] border-[#EF4444]/40 bg-[#EF4444]/10 error-pulse'
                    : status === 'CAUTION'
                    ? 'text-[#F59E0B] border-[#F59E0B]/40 bg-[#F59E0B]/10'
                    : 'text-[#10B981] border-[#10B981]/40 bg-[#10B981]/10 glow-active'
                }`}
              >
                {status}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
