export type SystemTab = 'mission_control' | 'telemetry' | 'trajectory' | 'navigation' | 'diagnostics';

export type BandType = 'L-BAND' | 'S-BAND' | 'INFRARED' | 'RADAR';

export type HazardSeverity = 'CRITICAL' | 'WARNING' | 'INFO';

export interface HazardAttribute {
  label: string;
  value: string;
  isDanger?: boolean;
}

export interface HazardItem {
  id: string;
  code: string;
  distance: string;
  title: string;
  description: string;
  severity: HazardSeverity;
  attributes: HazardAttribute[];
}

export interface Coordinates {
  lat: number;
  lon: number;
}

export interface DepthProfilePoint {
  x: number; // Distance in km (0 to 20)
  y: number; // Depth in km (-1.0 to -3.0)
  slope: number;
  isHazard?: boolean;
  hazardType?: string;
}

export interface TelemetryMetrics {
  reflectance: string;
  roughness: string;
  dielectric: string;
  altitude: string;
  maxSlope: string;
  status: 'GO' | 'NO-GO ZONE' | 'CAUTION';
  speed: string;
  cabinTemp: string;
  battery: number;
  commsStatus: string;
  latency: string;
}

export interface AscentData {
  isAscending: boolean;
  stage: 'STANDBY' | 'IGNITION' | 'LIFT_OFF' | 'MAX_Q' | 'STAGE_SEPARATION' | 'ORBITAL_INSERTION';
  altitudeKm: number;
  velocityKmS: number;
  thrustPct: number;
  fuelPct: number;
  secondsRemaining: number;
}

export interface DiagnosticLog {
  timestamp: string;
  subsystem: string;
  status: 'OK' | 'WARN' | 'FAIL';
  message: string;
}
