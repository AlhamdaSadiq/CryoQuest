import React, { useState, useEffect } from 'react';

export const TelemetryStreamView: React.FC = () => {
  const [dataPoints, setDataPoints] = useState<
    { time: string; torque: number; temp: number; voltage: number; latency: number }[]
  >([]);

  useEffect(() => {
    const initial = Array.from({ length: 15 }).map((_, i) => ({
      time: `${i * 2}s`,
      torque: 140 + Math.random() * 30,
      temp: 45 + Math.random() * 5,
      voltage: 28.2 + Math.random() * 0.4,
      latency: 120 + Math.random() * 15,
    }));
    setDataPoints(initial);

    const interval = setInterval(() => {
      setDataPoints((prev) => {
        const nextTime = `${(prev.length * 2) % 60}s`;
        const newPoint = {
          time: nextTime,
          torque: 140 + Math.random() * 35,
          temp: 46 + Math.random() * 4,
          voltage: 28.1 + Math.random() * 0.5,
          latency: 118 + Math.random() * 20,
        };
        return [...prev.slice(1), newPoint];
      });
    }, 1500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 flex flex-col gap-6 select-none font-sans">
      <div className="bento-card-gradient p-6 flex justify-between items-center flex-wrap gap-4">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#3B82F6] block mb-1">
            SENSOR TELEMETRY BUS
          </span>
          <h2 className="font-['Space_Grotesk'] text-2xl font-bold text-white tracking-tight">
            Live Telemetry Streams
          </h2>
          <p className="font-mono text-xs text-[#737373] mt-1">
            REALTIME HIGH-FREQUENCY SENSOR BUS (100 Hz SAMPLING)
          </p>
        </div>
        <div className="flex items-center gap-2 bg-[#161616] border border-[#262626] rounded-full px-4 py-2 text-xs font-mono">
          <span className="w-2.5 h-2.5 rounded-full bg-[#10B981] live-pulse" />
          <span className="text-[#10B981] font-bold">BUS ACTIVE</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Motor Torque Stream */}
        <div className="bento-card p-6 flex flex-col gap-4">
          <div className="flex justify-between items-center font-mono text-xs">
            <span className="text-[#3B82F6] font-bold">MOTOR TORQUE OUTPUT (Nm)</span>
            <span className="text-white font-semibold">
              AVG: {(dataPoints.reduce((a, b) => a + b.torque, 0) / (dataPoints.length || 1)).toFixed(1)} Nm
            </span>
          </div>
          <div className="h-44 bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-4 relative flex items-end">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 100 100" preserveAspectRatio="none">
              <polyline
                fill="none"
                stroke="#3B82F6"
                strokeWidth="2.5"
                points={dataPoints
                  .map((pt, idx) => `${(idx / (dataPoints.length - 1)) * 100},${100 - (pt.torque / 200) * 100}`)
                  .join(' ')}
              />
            </svg>
          </div>
        </div>

        {/* Chassis Temperature Stream */}
        <div className="bento-card p-6 flex flex-col gap-4">
          <div className="flex justify-between items-center font-mono text-xs">
            <span className="text-[#F59E0B] font-bold">CHASSIS THERMAL LOAD (°C)</span>
            <span className="text-white font-semibold">
              PEAK: {Math.max(...dataPoints.map((d) => d.temp), 0).toFixed(1)}°C
            </span>
          </div>
          <div className="h-44 bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-4 relative flex items-end">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 100 100" preserveAspectRatio="none">
              <polyline
                fill="none"
                stroke="#F59E0B"
                strokeWidth="2.5"
                points={dataPoints
                  .map((pt, idx) => `${(idx / (dataPoints.length - 1)) * 100},${100 - (pt.temp / 80) * 100}`)
                  .join(' ')}
              />
            </svg>
          </div>
        </div>

        {/* RTG Bus Voltage */}
        <div className="bento-card p-6 flex flex-col gap-4">
          <div className="flex justify-between items-center font-mono text-xs">
            <span className="text-[#10B981] font-bold">RTG VOLTAGE BUS (V)</span>
            <span className="text-white font-semibold">28.3 V STABLE</span>
          </div>
          <div className="h-44 bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-4 relative flex items-end">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 100 100" preserveAspectRatio="none">
              <polyline
                fill="none"
                stroke="#10B981"
                strokeWidth="2.5"
                points={dataPoints
                  .map((pt, idx) => `${(idx / (dataPoints.length - 1)) * 100},${100 - (pt.voltage / 35) * 100}`)
                  .join(' ')}
              />
            </svg>
          </div>
        </div>

        {/* Signal Latency */}
        <div className="bento-card p-6 flex flex-col gap-4">
          <div className="flex justify-between items-center font-mono text-xs">
            <span className="text-[#EF4444] font-bold">SIGNAL LATENCY (ms)</span>
            <span className="text-white font-semibold">UHF RELAY: 124 ms</span>
          </div>
          <div className="h-44 bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-4 relative flex items-end">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 100 100" preserveAspectRatio="none">
              <polyline
                fill="none"
                stroke="#EF4444"
                strokeWidth="2.5"
                points={dataPoints
                  .map((pt, idx) => `${(idx / (dataPoints.length - 1)) * 100},${100 - (pt.latency / 200) * 100}`)
                  .join(' ')}
              />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};
