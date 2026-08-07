import React, { useEffect, useState } from 'react';
import {
  BandType,
  Coordinates,
  HazardItem,
  SystemTab,
  TelemetryMetrics,
} from './types';
import { SideNavBar } from './components/SideNavBar';
import { TopAppBar } from './components/TopAppBar';
import { DielectricOverlay } from './components/DielectricOverlay';
import { DepthProfileChart } from './components/DepthProfileChart';
import { HazardLogPanel } from './components/HazardLogPanel';
import { MissionControlView } from './components/MissionControlView';
import { TelemetryStreamView } from './components/TelemetryStreamView';
import { TrajectoryPlannerView } from './components/TrajectoryPlannerView';
import { DiagnosticsView } from './components/DiagnosticsView';
import { AscentModal } from './components/AscentModal';
import { EmergencyAbortModal } from './components/EmergencyAbortModal';

const INITIAL_HAZARDS: HazardItem[] = [
  {
    id: 'h1',
    code: 'CRIT-01',
    distance: '8.4km',
    title: 'Slope > 15°',
    description: 'Exceeds rover traverse limits. Inner crater wall descent impossible.',
    severity: 'CRITICAL',
    attributes: [
      { label: 'ELEV', value: '-2.8km' },
      { label: 'GRADE', value: '24.5°', isDanger: true },
    ],
  },
  {
    id: 'h2',
    code: 'CRIT-02',
    distance: '9.1km',
    title: 'Loose Regolith',
    description: 'Low bearing capacity detected. High risk of traction loss.',
    severity: 'CRITICAL',
    attributes: [
      { label: 'ZONE', value: 'BASIN' },
      { label: 'FRIC', value: '< 0.2', isDanger: true },
    ],
  },
  {
    id: 'h3',
    code: 'WARN-01',
    distance: '12.0km',
    title: 'Signal Occlusion',
    description: 'Crater rim blocks direct S-Band LOS to orbiter relay.',
    severity: 'WARNING',
    attributes: [
      { label: 'DUR', value: '45min' },
      { label: 'COMMS', value: 'UHF' },
    ],
  },
  {
    id: 'h4',
    code: 'INFO-01',
    distance: '2.1km',
    title: 'Boulder Field',
    description: 'Scattered ejecta >0.5m. Navigable with reduced speed.',
    severity: 'INFO',
    attributes: [{ label: 'SPEED', value: '0.5m/s' }],
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<SystemTab>('navigation');
  const [selectedBand, setSelectedBand] = useState<BandType>('L-BAND');
  const [currentCoords, setCurrentCoords] = useState<Coordinates>({
    lat: 42.1245,
    lon: 18.4521,
  });

  const [metrics, setMetrics] = useState<TelemetryMetrics>({
    reflectance: '0.14',
    roughness: '4.2',
    dielectric: '2.8',
    altitude: '-2.4',
    maxSlope: '24.5',
    status: 'NO-GO ZONE',
    speed: '0.5m/s',
    cabinTemp: '22°C',
    battery: 94,
    commsStatus: 'S-BAND LINKED',
    latency: '124 ms',
  });

  const [hazards, setHazards] = useState<HazardItem[]>(INITIAL_HAZARDS);
  const [mapImageUrl, setMapImageUrl] = useState<string | undefined>(undefined);
  const [pipelineStatus, setPipelineStatus] = useState<
    'unknown' | 'connected' | 'unavailable'
  >('unknown');
  const [isPipelineRunning, setIsPipelineRunning] = useState(false);
  const [pipelineLog, setPipelineLog] = useState<string>('');

  // Pull real outputs from the Lunar Ice Detection pipeline (fusion probability
  // map + ranked landing-site shortlist + Maxwell-Garnett volume estimate) and
  // fold them into the UI instead of the placeholder/simulated values above.
  const loadMissionData = React.useCallback(async () => {
    try {
      const [sitesRes, volumeRes] = await Promise.all([
        fetch('/api/pipeline/landing-sites'),
        fetch('/api/pipeline/volume-estimate'),
      ]);
      if (!sitesRes.ok || !volumeRes.ok) {
        setPipelineStatus('unavailable');
        return;
      }

      const sites = await sitesRes.json();
      const volume = await volumeRes.json();

      setPipelineStatus('connected');
      setMapImageUrl(`/api/pipeline/ice-probability-map.png?t=${Date.now()}`);

      const siteHazards: HazardItem[] = (sites.features ?? [])
        .slice(0, 4)
        .map((f: any) => {
          const p = f.properties ?? {};
          const slope: number = p.slope_degrees ?? 0;
          const severity: HazardItem['severity'] =
            slope > 15 ? 'CRITICAL' : slope > 8 ? 'WARNING' : 'INFO';
          return {
            id: `site-${p.rank}`,
            code: `SITE-0${p.rank}`,
            distance: `${(p.distance_to_ice_m ?? 0).toFixed(0)}m`,
            title: `Candidate Landing Site #${p.rank}`,
            description: `Fusion-ranked site, score ${(p.score ?? 0).toFixed(
              2
            )}. Illumination ${((p.illumination_fraction ?? 0) * 100).toFixed(0)}% direct.`,
            severity,
            attributes: [
              { label: 'SCORE', value: (p.score ?? 0).toFixed(2) },
              { label: 'SLOPE', value: `${slope.toFixed(1)}°`, isDanger: slope > 15 },
            ],
          } satisfies HazardItem;
        });

      if (siteHazards.length > 0) {
        setHazards(siteHazards);
      }

      setMetrics((m) => ({
        ...m,
        dielectric: volume?.dielectric_assumptions?.ice?.nominal?.toFixed(2) ?? m.dielectric,
        roughness: volume?.mean_ice_fraction
          ? (volume.mean_ice_fraction * 10).toFixed(1)
          : m.roughness,
      }));
    } catch {
      setPipelineStatus('unavailable');
    }
  }, []);

  useEffect(() => {
    loadMissionData();
  }, [loadMissionData]);

  // Trigger a full pipeline re-run on the Python side (server.ts spawns
  // main.py + the PNG preview renderer), streaming progress back live, then
  // reload the mission data above once it finishes.
  const handleRunPipeline = async () => {
    setIsPipelineRunning(true);
    setPipelineLog('');
    try {
      const res = await fetch('/api/pipeline/run', { method: 'POST' });
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      if (reader) {
        // eslint-disable-next-line no-constant-condition
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          setPipelineLog((prev) => prev + decoder.decode(value, { stream: true }));
        }
      }
      await loadMissionData();
    } catch (e) {
      setPipelineLog((prev) => prev + `\nFailed to reach pipeline server: ${e}`);
    } finally {
      setIsPipelineRunning(false);
    }
  };

  const [showAscentModal, setShowAscentModal] = useState(false);
  const [showAbortModal, setShowAbortModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  const [aiReport, setAiReport] = useState<{
    riskLevel?: string;
    recommendedSpeed?: string;
    summary?: string;
    recommendedAction?: string;
  } | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);

  // Band Change handler
  const handleBandChange = (band: BandType) => {
    setSelectedBand(band);
    switch (band) {
      case 'L-BAND':
        setMetrics((m) => ({ ...m, reflectance: '0.14', roughness: '4.2', dielectric: '2.8' }));
        break;
      case 'S-BAND':
        setMetrics((m) => ({ ...m, reflectance: '0.22', roughness: '5.1', dielectric: '3.4' }));
        break;
      case 'INFRARED':
        setMetrics((m) => ({ ...m, reflectance: '0.38', roughness: '3.9', dielectric: '2.1' }));
        break;
      case 'RADAR':
        setMetrics((m) => ({ ...m, reflectance: '0.45', roughness: '6.0', dielectric: '4.2' }));
        break;
    }
  };

  // Coordinates select handler
  const handleSelectCoords = (newCoords: Coordinates) => {
    setCurrentCoords(newCoords);
    const distFromCenter = Math.hypot(newCoords.lat - 42.12, newCoords.lon - 18.45);

    let slopeVal = 24.5;
    let statusVal: 'GO' | 'NO-GO ZONE' | 'CAUTION' = 'NO-GO ZONE';
    let altVal = '-2.4';

    if (distFromCenter < 0.05) {
      slopeVal = 24.5;
      statusVal = 'NO-GO ZONE';
      altVal = '-2.8';
    } else if (distFromCenter < 0.12) {
      slopeVal = 14.2;
      statusVal = 'CAUTION';
      altVal = '-1.9';
    } else {
      slopeVal = 6.4;
      statusVal = 'GO';
      altVal = '-1.1';
    }

    setMetrics((m) => ({
      ...m,
      maxSlope: slopeVal.toFixed(1),
      status: statusVal,
      altitude: altVal,
    }));
  };

  // Run AI Terrain Analysis
  const handleRunAiAnalysis = async () => {
    setIsAiLoading(true);
    setAiReport(null);

    try {
      const res = await fetch('/api/ai/analyze-crater', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: currentCoords.lat,
          lon: currentCoords.lon,
          band: selectedBand,
          slope: parseFloat(metrics.maxSlope),
          altitude: parseFloat(metrics.altitude),
        }),
      });
      const data = await res.json();
      setAiReport(data);
    } catch (e) {
      setAiReport({
        riskLevel: 'HIGH',
        recommendedSpeed: '0.3 m/s',
        summary: 'Crater basin wall detected. High slope gradient requires crawler differential lock.',
        recommendedAction: 'Maintain current perimeter trajectory along North ridge.',
      });
    } finally {
      setIsAiLoading(false);
    }
  };

  // Export Hazard Matrix file download
  const handleExportMatrix = () => {
    const jsonString = JSON.stringify(
      {
        mission: 'MISSION ALPHA-1',
        sector: 'SECTOR-7 OPS',
        timestamp: new Date().toISOString(),
        coordinates: currentCoords,
        hazards,
      },
      null,
      2
    );

    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `LUNAR_HAZARD_MATRIX_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#05080f] text-[#dce4e5]">
      {/* Side Navigation Rail */}
      <SideNavBar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onInitiateAscent={() => setShowAscentModal(true)}
        onOpenSettings={() => setShowSettingsModal(true)}
        hazardCount={hazards.filter((h) => h.severity === 'CRITICAL').length}
      />

      {/* Main Workspace Area */}
      <main className="flex-1 ml-[320px] flex flex-col min-h-screen bg-[#05080f] data-grid">
        {/* Top Header Bar */}
        <TopAppBar
          currentCoords={currentCoords}
          onEmergencyAbort={() => setShowAbortModal(true)}
          batteryPct={metrics.battery}
          subTitle={
            activeTab === 'navigation'
              ? 'CRATER ANALYSIS'
              : activeTab === 'mission_control'
              ? 'SUBSYSTEM OVERVIEW'
              : activeTab === 'telemetry'
              ? 'REALTIME STREAMS'
              : activeTab === 'trajectory'
              ? 'PATHFINDER PLANNER'
              : 'SYSTEM DIAGNOSTICS'
          }
        />

        {/* Tab Content Display */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'navigation' && (
            <div className="p-6 flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Dielectric Map Overlay */}
              <div className="lg:col-span-5 flex flex-col gap-4">
                {/* Pipeline Connection / Run Control */}
                <div className="bento-card p-4 flex items-center justify-between gap-3 font-['JetBrains_Mono'] text-xs">
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        pipelineStatus === 'connected'
                          ? 'bg-[#10B981] live-pulse'
                          : pipelineStatus === 'unavailable'
                          ? 'bg-[#ffb4ab]'
                          : 'bg-[#737373]'
                      }`}
                    />
                    <span className="text-[#bac9cc] uppercase tracking-wider">
                      {pipelineStatus === 'connected'
                        ? 'Pipeline connected — live outputs'
                        : pipelineStatus === 'unavailable'
                        ? 'Pipeline outputs unavailable'
                        : 'Checking pipeline…'}
                    </span>
                  </div>
                  <button
                    onClick={handleRunPipeline}
                    disabled={isPipelineRunning}
                    className="px-3 py-1.5 bg-[#1A1A1A] hover:bg-[#262626] border border-[#333333] hover:border-[#3B82F6] text-[#3B82F6] hover:text-white font-semibold rounded-lg transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
                  >
                    <span className="material-symbols-outlined text-sm">
                      {isPipelineRunning ? 'sync' : 'play_circle'}
                    </span>
                    {isPipelineRunning ? 'RUNNING…' : 'RUN PIPELINE'}
                  </button>
                </div>

                {pipelineLog && (
                  <pre className="bento-card p-3 max-h-32 overflow-y-auto text-[10px] leading-snug text-[#8f98a3] font-['JetBrains_Mono'] whitespace-pre-wrap">
                    {pipelineLog}
                  </pre>
                )}

                <DielectricOverlay
                  currentCoords={currentCoords}
                  onSelectCoords={handleSelectCoords}
                  selectedBand={selectedBand}
                  setSelectedBand={handleBandChange}
                  reflectance={metrics.reflectance}
                  roughness={metrics.roughness}
                  dielectric={metrics.dielectric}
                  altitude={metrics.altitude}
                  onRunAiAnalysis={handleRunAiAnalysis}
                  isAiLoading={isAiLoading}
                  mapImageUrl={mapImageUrl}
                />

                {/* AI Terrain Report Box if generated */}
                {aiReport && (
                  <div className="border border-[#06e0f9] bg-[#111625] p-4 flex flex-col gap-2 font-['JetBrains_Mono'] text-xs relative">
                    <button
                      onClick={() => setAiReport(null)}
                      className="absolute top-2 right-2 text-[#bac9cc] hover:text-[#ffb4ab] cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-sm">close</span>
                    </button>
                    <div className="flex items-center gap-2 text-[#06e0f9] font-bold">
                      <span className="material-symbols-outlined text-sm">auto_awesome</span>
                      <span>AI TACTICAL EVALUATION REPORT</span>
                    </div>
                    <div className="text-[#dce4e5] leading-relaxed mt-1">{aiReport.summary}</div>
                    <div className="flex justify-between items-center border-t border-[#2a3441] pt-2 mt-1">
                      <span className="text-[#bac9cc]">
                        REC SPEED: <strong className="text-[#06e0f9]">{aiReport.recommendedSpeed}</strong>
                      </span>
                      <span className="text-[#06e0f9] font-bold">{aiReport.recommendedAction}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Center Column: Depth Profile Graph */}
              <div className="lg:col-span-4 flex flex-col gap-4">
                <DepthProfileChart
                  maxSlope={metrics.maxSlope}
                  status={metrics.status}
                  onSelectWaypoint={(km, depthKm) => {
                    setMetrics((m) => ({
                      ...m,
                      altitude: depthKm.toString(),
                    }));
                  }}
                />
              </div>

              {/* Right Column: Hazard Log Panel */}
              <div className="lg:col-span-3 flex flex-col gap-4">
                <HazardLogPanel
                  hazards={hazards}
                  onAddHazard={(newH) => setHazards([newH, ...hazards])}
                  onExportMatrix={handleExportMatrix}
                />
              </div>
            </div>
          )}

          {activeTab === 'mission_control' && (
            <MissionControlView
              metrics={metrics}
              onUpdateDriveMode={(mode) => console.log('Drive mode:', mode)}
            />
          )}

          {activeTab === 'telemetry' && <TelemetryStreamView />}

          {activeTab === 'trajectory' && <TrajectoryPlannerView />}

          {activeTab === 'diagnostics' && <DiagnosticsView />}
        </div>
      </main>

      {/* Ascent Modal */}
      {showAscentModal && <AscentModal onClose={() => setShowAscentModal(false)} />}

      {/* Emergency Abort Modal */}
      {showAbortModal && (
        <EmergencyAbortModal
          onClose={() => setShowAbortModal(false)}
          onConfirmAbort={() => {
            setMetrics((m) => ({ ...m, status: 'NO-GO ZONE', commsStatus: 'ABORT TETHER' }));
          }}
        />
      )}

      {/* Settings Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 bg-[#05080f]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111625] border border-[#06e0f9] p-6 w-full max-w-md flex flex-col gap-4">
            <div className="flex justify-between items-center border-b border-[#2a3441] pb-2">
              <h3 className="font-['Space_Grotesk'] text-base font-bold text-[#06e0f9] uppercase flex items-center gap-2">
                <span className="material-symbols-outlined">settings</span> Sector-7 Station Config
              </h3>
              <button
                onClick={() => setShowSettingsModal(false)}
                className="text-[#bac9cc] hover:text-[#ffb4ab] cursor-pointer"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="font-['JetBrains_Mono'] text-xs flex flex-col gap-3">
              <div className="flex justify-between items-center p-2 border border-[#2a3441] bg-[#05080f]">
                <span>Telemetry Sampling Rate</span>
                <span className="text-[#06e0f9] font-bold">100 Hz</span>
              </div>
              <div className="flex justify-between items-center p-2 border border-[#2a3441] bg-[#05080f]">
                <span>Orbiter S-Band Link</span>
                <span className="text-[#06e0f9] font-bold">LUNAR_RELAY_4</span>
              </div>
              <div className="flex justify-between items-center p-2 border border-[#2a3441] bg-[#05080f]">
                <span>LIDAR Sensor Calibration</span>
                <span className="text-[#06e0f9] font-bold">AUTONOMOUS</span>
              </div>
              <div className="flex justify-between items-center p-2 border border-[#2a3441] bg-[#05080f]">
                <span>AI Core Model</span>
                <span className="text-[#06e0f9] font-bold">Gemini 3.6 Flash</span>
              </div>
            </div>

            <button
              onClick={() => setShowSettingsModal(false)}
              className="mt-2 py-2.5 bg-[#06e0f9] text-[#05080f] font-bold font-['JetBrains_Mono'] text-xs uppercase cursor-pointer"
            >
              SAVE CONFIGURATION
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
