// ─── Farm ───────────────────────────────────────────────────
export interface FarmCreate {
  farmer_name: string;
  location: string;
  latitude: number | null;
  longitude: number | null;
  crop: string;
  area_acres: number;
  crop_stage: string | null;
}

export interface Farm extends FarmCreate {
  id: number;
  grid_cell_id?: number | null;
}

// ─── Risk Analysis ──────────────────────────────────────────
// Matches backend schemas.RiskAnalysisRequest
export interface RiskAnalysisRequest {
  farm_id?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  trigger_type: string;       // "drought" | "excess_rain"
  threshold_mm: number;
  window_days: number;
  season_end?: string | null;  // ISO date
  lookback_years?: number;
  min_coverage?: number;
}

// Matches backend schemas.RiskYear
export interface RiskYear {
  year: number;
  window_start: string;
  window_end: string;
  observed_mm: number | null;
  triggered: boolean | null;
  eligible: boolean;
  observations_used: number;
  expected_days: number;
  coverage: number;
  sources: string[];
  is_simulated: boolean;
  ineligible_reason: string | null;
}

// Matches backend schemas.RiskFactor
export interface RiskFactor {
  factor: string;
  detail: string;
  direction: string;
}

// Matches backend schemas.RiskAnalysisResponse
export interface RiskAnalysis {
  risk_score: number | null;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "SEVERE" | "UNKNOWN";
  risk_level_meaning: string;
  trigger_frequency: number | null;

  historical_years: number;
  eligible_years: number;
  triggered_years: number;
  triggered_year_labels: number[];
  total_observations_used: number;

  trigger_definition: Record<string, unknown>;
  data_source: string[];
  is_simulated: boolean;
  data_quality: string;      // "sufficient" | "limited" | "insufficient"
  confidence: string;         // Backend returns string, not number

  engine_version: string;
  context: Record<string, unknown>;
  factors: RiskFactor[];
  years: RiskYear[];

  // Catch-all for extra fields
  [key: string]: unknown;
}

export interface RiskBand {
  level: string;
  min_score: number;
  max_score: number;
  meaning: string;
}

// ─── Policy ─────────────────────────────────────────────────
// Matches backend schemas.PolicyCreate
export interface PolicyCreate {
  farm_id: number;
  coverage_amount: string;    // Decimal as string
  premium: string;            // Decimal as string — required by backend
  trigger_type: string;
  threshold_mm: number;
  window_days: number;        // Required by backend
}

// Matches backend schemas.PolicyResponse
export interface Policy {
  id: number;
  farm_id: number;
  coverage_amount: string;    // Backend serialises Decimal → string
  premium: string;            // Backend serialises Decimal → string
  trigger_type: string;
  threshold_mm: number;
  window_days: number;
  status: string;
  [key: string]: unknown;
}

// ─── Weather ────────────────────────────────────────────────
export interface WeatherData {
  farm_id: number;
  days: number;
  rainfall_data: RainfallRecord[];
  total_rainfall_mm: number;
  avg_daily_rainfall_mm: number;
  [key: string]: unknown;
}

export interface RainfallRecord {
  date: string;
  rainfall_mm: number;
  source?: string;
}

// ─── Simulation & Trigger ───────────────────────────────────
// The simulate endpoints do NOT accept a request body with rainfall_mm;
// they use hardcoded constants (DROUGHT_RAINFALL_MM = 11.0, EXCESS_RAIN = 150.0).
// Optional query param: evaluation_date.

// Matches the dict returned by evaluation._serialise()
export interface SimulationResult {
  trigger_id: number;
  policy_id: number;
  evaluation_date: string;
  trigger_type: string | null;
  observed_rainfall_mm: number;
  threshold_mm: number;
  triggered: boolean;
  window_start: string | null;
  window_end: string | null;
  observations_used: number;
  data_source: string;
  is_simulated: boolean;
  engine_version: string;
  idempotent_reuse: boolean;
  simulated?: boolean;

  // Nested payout object — only present when triggered
  payout?: {
    payout_id: number;
    amount: string;           // Decimal string e.g. "21600.00"
    currency: string;
    status: string;
  } | null;

  [key: string]: unknown;
}

export interface TriggerCheckResult {
  policy_id: number;
  triggered: boolean;
  observed_rainfall_mm: number;
  threshold_mm: number;
  trigger_type: string;
  payout?: {
    payout_id: number;
    amount: string;
    currency: string;
    status: string;
  } | null;
  trigger_id?: number;
  [key: string]: unknown;
}

// ─── Payout ─────────────────────────────────────────────────
export interface PayoutResult {
  payout_id: number;
  amount: string;             // Decimal string
  currency: string;
  status: string;
}

// ─── Demo State ─────────────────────────────────────────────
export interface DemoState {
  farm: Farm | null;
  riskAnalysis: RiskAnalysis | null;
  policy: Policy | null;
  simulationResult: SimulationResult | null;
  currentStep: DemoStep;
}

export type DemoStep =
  | "farm-setup"
  | "risk-analysis"
  | "policy"
  | "simulate"
  | "payout";

export const DEMO_STEPS: { key: DemoStep; label: string; number: number }[] = [
  { key: "farm-setup", label: "Farm Setup", number: 1 },
  { key: "risk-analysis", label: "Risk Analysis", number: 2 },
  { key: "policy", label: "Policy", number: 3 },
  { key: "simulate", label: "Simulate", number: 4 },
  { key: "payout", label: "Payout", number: 5 },
];

// ─── Location presets ───────────────────────────────────────
// The demo farm is Pollachi, Coimbatore — it MUST be the first entry
// so the default selection matches the seeded demo data.
export const LOCATIONS = [
  { name: "Pollachi, Coimbatore", lat: 11.02, lng: 76.98 },
  { name: "Thanjavur, Tamil Nadu", lat: 10.787, lng: 79.138 },
  { name: "Nagapattinam, Tamil Nadu", lat: 10.766, lng: 79.843 },
  { name: "Cuddalore, Tamil Nadu", lat: 11.748, lng: 79.768 },
  { name: "Ramanathapuram, Tamil Nadu", lat: 9.371, lng: 78.830 },
  { name: "Tirunelveli, Tamil Nadu", lat: 8.727, lng: 77.684 },
  { name: "Madurai, Tamil Nadu", lat: 9.925, lng: 78.120 },
  { name: "Villupuram, Tamil Nadu", lat: 11.940, lng: 79.493 },
  { name: "Tiruchirappalli, Tamil Nadu", lat: 10.790, lng: 78.705 },
] as const;

export const CROPS = [
  "Maize",
  "Rice (Paddy)",
  "Sugarcane",
  "Cotton",
  "Groundnut",
  "Millets",
  "Banana",
  "Coconut",
] as const;

export const CROP_STAGES = [
  "Sowing",
  "Vegetative",
  "Flowering",
  "Grain filling",
  "Harvesting",
] as const;

export const TRIGGER_TYPES = [
  { value: "drought", label: "Drought (Low Rainfall)" },
  { value: "excess_rain", label: "Excess Rainfall" },
] as const;

// Demo defaults matching backend seed_demo.py
export const DEMO_DEFAULTS = {
  farmer_name: "Murugan",
  location_index: 0,   // Pollachi, Coimbatore
  crop: "Maize",
  area_acres: 3.0,
  crop_stage: "Flowering",
  trigger_type: "drought",
  threshold_mm: 30,
  window_days: 30,
  coverage_amount: "72000.00",
  premium: "2169.00",
} as const;
