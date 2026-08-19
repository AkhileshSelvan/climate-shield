"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useDemo } from "@/context/DemoContext";
import { StepIndicator } from "@/components/ui/StepIndicator";
import {
  Card,
  Badge,
  Button,
  Loader,
  ErrorState,
  SimulatedBadge,
} from "@/components/ui";
import { simulateDrought, simulateExcessRain } from "@/lib/api";

export default function SimulatePage() {
  const router = useRouter();
  const { farm, policy, simulationResult, setSimulationResult, setCurrentStep } =
    useDemo();

  const [rainfallMm, setRainfallMm] = useState(20);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSimulated, setHasSimulated] = useState(false);

  useEffect(() => {
    if (!farm) {
      router.push("/demo/farm-setup");
      return;
    }
    if (!policy) {
      router.push("/demo/policy");
      return;
    }

    // Set default slider value based on trigger type
    if (policy.trigger_type === "drought") {
      setRainfallMm(Math.max(0, policy.threshold_mm - 20));
    } else {
      setRainfallMm(policy.threshold_mm + 50);
    }
  }, [farm, policy, router]);

  async function handleSimulate() {
    if (!policy) return;

    setLoading(true);
    setError(null);

    try {
      const simulateFn =
        policy.trigger_type === "drought" ? simulateDrought : simulateExcessRain;

      const result = await simulateFn(policy.id, {
        rainfall_mm: rainfallMm,
      });

      setSimulationResult(result);
      setHasSimulated(true);
    } catch (err) {
      console.error("Simulation failed:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Simulation failed. Please check the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleContinue() {
    setCurrentStep("payout");
    router.push("/demo/payout");
  }

  if (!farm || !policy) return null;

  const isDrought = policy.trigger_type === "drought";
  const threshold = policy.threshold_mm;
  const sliderMax = isDrought ? threshold * 3 : threshold * 3;

  // Calculate visual trigger status
  const wouldTrigger = isDrought
    ? rainfallMm < threshold
    : rainfallMm > threshold;

  function formatCurrency(val: string | number | null): string {
    if (val == null) return "—";
    const num = typeof val === "string" ? parseFloat(val) : val;
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(num);
  }

  return (
    <div className="animate-fade-in">
      <StepIndicator currentStep="simulate" />

      <div className="max-w-3xl mx-auto mt-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-100">
              <span className="gradient-text">Climate Event Simulator</span>
            </h1>
            <p className="text-gray-400 mt-2">
              Simulate a {isDrought ? "drought" : "excessive rainfall"} event to
              test the parametric trigger.
            </p>
          </div>
          <SimulatedBadge />
        </div>

        {error && (
          <div className="mb-6">
            <ErrorState
              title="Simulation Failed"
              message={error}
              onRetry={() => setError(null)}
            />
          </div>
        )}

        {/* Simulation controls */}
        <Card className="!p-8 mb-6">
          <div className="space-y-6">
            {/* Policy context */}
            <div className="bg-navy-800/50 rounded-xl p-4 border border-gray-800">
              <div className="flex flex-wrap gap-4 text-sm text-gray-300">
                <span>
                  Policy #{policy.id} •{" "}
                  {isDrought ? "🌵 Drought" : "🌧️ Excess Rain"}
                </span>
                <span>
                  Threshold: <strong>{threshold} mm</strong>
                </span>
                <span>
                  Coverage: <strong>{formatCurrency(policy.coverage_amount)}</strong>
                </span>
              </div>
            </div>

            {/* Rainfall slider */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-300">
                  Simulated Rainfall
                </label>
                <span className="text-2xl font-bold tabular-nums text-gray-100">
                  {rainfallMm} mm
                </span>
              </div>

              <div className="relative">
                <input
                  id="rainfall-slider"
                  type="range"
                  min={0}
                  max={sliderMax}
                  step={1}
                  value={rainfallMm}
                  onChange={(e) => setRainfallMm(parseInt(e.target.value))}
                  className="w-full h-3 rounded-full appearance-none cursor-pointer
                             bg-navy-700
                             [&::-webkit-slider-thumb]:appearance-none
                             [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6
                             [&::-webkit-slider-thumb]:rounded-full
                             [&::-webkit-slider-thumb]:bg-climate-500
                             [&::-webkit-slider-thumb]:shadow-[0_0_12px_rgba(16,185,129,0.4)]
                             [&::-webkit-slider-thumb]:cursor-pointer
                             [&::-webkit-slider-thumb]:transition-all
                             [&::-webkit-slider-thumb]:hover:scale-110"
                />

                {/* Threshold marker */}
                <div
                  className="absolute top-1/2 -translate-y-1/2 w-0.5 h-8 bg-danger-400/80"
                  style={{
                    left: `${(threshold / sliderMax) * 100}%`,
                  }}
                >
                  <span className="absolute -top-7 left-1/2 -translate-x-1/2 text-xs text-danger-400 whitespace-nowrap font-medium">
                    Threshold: {threshold}mm
                  </span>
                </div>
              </div>

              <div className="flex justify-between text-xs text-gray-600 mt-1">
                <span>0 mm</span>
                <span>{sliderMax} mm</span>
              </div>
            </div>

            {/* Trigger preview */}
            <div
              className={`
              rounded-xl p-4 border-2 transition-all duration-500
              ${
                wouldTrigger
                  ? "bg-danger-500/5 border-danger-500/30"
                  : "bg-climate-500/5 border-climate-500/30"
              }
            `}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    wouldTrigger ? "bg-danger-500/20" : "bg-climate-500/20"
                  }`}
                >
                  {wouldTrigger ? (
                    <svg className="w-5 h-5 text-danger-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5 text-climate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                </div>
                <div>
                  <p
                    className={`text-sm font-semibold ${
                      wouldTrigger ? "text-danger-400" : "text-climate-400"
                    }`}
                  >
                    {wouldTrigger
                      ? "⚡ TRIGGER WOULD ACTIVATE"
                      : "✓ Within safe range"}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {isDrought
                      ? `${rainfallMm}mm ${rainfallMm < threshold ? "<" : "≥"} ${threshold}mm threshold`
                      : `${rainfallMm}mm ${rainfallMm > threshold ? ">" : "≤"} ${threshold}mm threshold`}
                  </p>
                </div>
              </div>
            </div>

            {/* Run simulation button */}
            <Button
              id="run-simulation-btn"
              onClick={handleSimulate}
              loading={loading}
              size="lg"
              className="w-full"
              variant={wouldTrigger ? "danger" : "primary"}
            >
              {loading ? "Running Simulation..." : "Run Simulation"}
            </Button>
          </div>
        </Card>

        {/* Simulation result */}
        {loading && <Loader text="Simulating climate event..." />}

        {hasSimulated && simulationResult && !loading && (
          <div className="space-y-6 animate-slide-up">
            <Card
              className={`!p-8 ${
                simulationResult.triggered
                  ? "!border-danger-500/30"
                  : "!border-climate-500/30"
              }`}
            >
              <div className="text-center mb-6">
                <div
                  className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-4 ${
                    simulationResult.triggered
                      ? "bg-danger-500/10"
                      : "bg-climate-500/10"
                  }`}
                >
                  {simulationResult.triggered ? (
                    <svg className="w-10 h-10 text-danger-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  ) : (
                    <svg className="w-10 h-10 text-climate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                </div>

                <h2
                  className={`text-2xl font-bold ${
                    simulationResult.triggered
                      ? "text-danger-400"
                      : "text-climate-400"
                  }`}
                >
                  {simulationResult.triggered
                    ? "⚡ TRIGGER ACTIVATED"
                    : "✓ No Trigger"}
                </h2>

                <p className="text-gray-400 mt-2 text-sm">
                  Observed: {simulationResult.observed_value}mm vs Threshold:{" "}
                  {simulationResult.threshold_value}mm
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-navy-800/50 rounded-xl p-4 text-center">
                  <p className="text-xs text-gray-500 uppercase tracking-wider">
                    Observed
                  </p>
                  <p className="text-xl font-bold text-gray-100 mt-1">
                    {simulationResult.observed_value} mm
                  </p>
                </div>
                <div className="bg-navy-800/50 rounded-xl p-4 text-center">
                  <p className="text-xs text-gray-500 uppercase tracking-wider">
                    Threshold
                  </p>
                  <p className="text-xl font-bold text-gray-100 mt-1">
                    {simulationResult.threshold_value} mm
                  </p>
                </div>
              </div>

              {simulationResult.triggered && (
                <div className="mt-6 text-center">
                  <p className="text-xs text-gray-500 uppercase tracking-wider">
                    Estimated Payout
                  </p>
                  <p className="text-3xl font-bold text-climate-400 mt-1">
                    {formatCurrency(simulationResult.payout_amount)}
                  </p>
                </div>
              )}

              {/* Metadata */}
              <div className="mt-4 flex flex-wrap gap-2 justify-center">
                <Badge variant="warning" size="sm">
                  Simulated Event
                </Badge>
                {simulationResult.severity_ratio != null && (
                  <Badge variant="info" size="sm">
                    Severity: {(simulationResult.severity_ratio * 100).toFixed(0)}%
                  </Badge>
                )}
              </div>
            </Card>

            {/* Continue to payout */}
            {simulationResult.triggered && (
              <div className="flex justify-end pt-2">
                <Button id="view-payout-btn" onClick={handleContinue} size="lg">
                  View Payout
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M13 7l5 5m0 0l-5 5m5-5H6"
                    />
                  </svg>
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
