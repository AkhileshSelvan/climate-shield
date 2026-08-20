import type {
  Farm,
  FarmCreate,
  RiskAnalysis,
  RiskAnalysisRequest,
  Policy,
  PolicyCreate,
  SimulationResult,
} from "./types";

// ─── Configuration ──────────────────────────────────────────
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Helpers ────────────────────────────────────────────────
class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = await response.text();
    }

    // Extract the backend's detail message when available
    const detail =
      errorData && typeof errorData === "object" && "detail" in errorData
        ? String((errorData as Record<string, unknown>).detail)
        : `API Error ${response.status}: ${response.statusText}`;

    throw new ApiError(detail, response.status, errorData);
  }

  return response.json() as Promise<T>;
}

// ─── Farm Endpoints ─────────────────────────────────────────
// Backend: POST /api/v1/farms/
export async function createFarm(farm: FarmCreate): Promise<Farm> {
  return request<Farm>("/api/v1/farms/", {
    method: "POST",
    body: JSON.stringify(farm),
  });
}

export async function getFarm(farmId: number): Promise<Farm> {
  return request<Farm>(`/api/v1/farms/${farmId}`);
}

// ─── Risk Endpoints ─────────────────────────────────────────
// Backend: POST /api/v1/risk/analyze
// Requires: trigger_type, threshold_mm, window_days, and either farm_id or lat/lng
export async function analyzeRisk(
  data: RiskAnalysisRequest
): Promise<RiskAnalysis> {
  return request<RiskAnalysis>("/api/v1/risk/analyze", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Backend: POST /api/v1/risk/analyze/policy/{policy_id}
export async function analyzeRiskForPolicy(
  policyId: number
): Promise<RiskAnalysis> {
  return request<RiskAnalysis>(`/api/v1/risk/analyze/policy/${policyId}`, {
    method: "POST",
  });
}

// Backend: GET /api/v1/risk/bands
export async function getRiskBands(): Promise<unknown> {
  return request<unknown>("/api/v1/risk/bands");
}

// ─── Policy Endpoints ───────────────────────────────────────
// Backend: POST /api/v1/policies/
// Requires: farm_id, coverage_amount (Decimal), premium (Decimal),
//           trigger_type, threshold_mm, window_days
export async function createPolicy(policy: PolicyCreate): Promise<Policy> {
  return request<Policy>("/api/v1/policies/", {
    method: "POST",
    body: JSON.stringify(policy),
  });
}

export async function getPolicy(policyId: number): Promise<Policy> {
  return request<Policy>(`/api/v1/policies/${policyId}`);
}

// ─── Weather Endpoints ──────────────────────────────────────
// Backend: POST /api/v1/weather/ingest
export async function ingestWeather(data: {
  farm_id?: number;
  latitude?: number;
  longitude?: number;
  days?: number;
  provider?: string;
}): Promise<unknown> {
  return request("/api/v1/weather/ingest", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ─── Simulation Endpoints ───────────────────────────────────
// Backend: POST /api/v1/simulate/drought/{policy_id}
// Does NOT accept rainfall_mm in body — uses hardcoded DROUGHT_RAINFALL_MM = 11.0
// Optional query param: evaluation_date
export async function simulateDrought(
  policyId: number,
  evaluationDate?: string
): Promise<SimulationResult> {
  const params = evaluationDate ? `?evaluation_date=${evaluationDate}` : "";
  return request<SimulationResult>(
    `/api/v1/simulate/drought/${policyId}${params}`,
    { method: "POST" }
  );
}

// Backend: POST /api/v1/simulate/excess_rain/{policy_id}
// Note: underscore, not hyphen
export async function simulateExcessRain(
  policyId: number,
  evaluationDate?: string
): Promise<SimulationResult> {
  const params = evaluationDate ? `?evaluation_date=${evaluationDate}` : "";
  return request<SimulationResult>(
    `/api/v1/simulate/excess_rain/${policyId}${params}`,
    { method: "POST" }
  );
}

// Backend: POST /api/v1/simulate/reset/{policy_id}
export async function resetSimulation(
  policyId: number
): Promise<unknown> {
  return request(`/api/v1/simulate/reset/${policyId}`, {
    method: "POST",
  });
}

// ─── Export error class ─────────────────────────────────────
export { ApiError };
