"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useDemo } from "@/context/DemoContext";
import { StepIndicator } from "@/components/ui/StepIndicator";
import {
  Card,
  Badge,
  Button,
  MetricCard,
  SimulatedBadge,
  Loader,
  ErrorState,
} from "@/components/ui";
import { simulateDrought, simulateExcessRain } from "@/lib/api";

export default function PayoutPage() {
  const router = useRouter();
  const { farm, policy, simulationResult, setSimulationResult, resetDemo } = useDemo();

  const [retesting, setRetesting] = useState(false);
  const [retestError, setRetestError] = useState<string | null>(null);

  useEffect(() => {
    if (!farm) {
      router.push("/demo/farm-setup");
      return;
    }
    if (!policy) {
      router.push("/demo/policy");
      return;
    }
    if (!simulationResult) {
      router.push("/demo/simulate");
      return;
    }
  }, [farm, policy, simulationResult, router]);

  if (!farm || !policy || !simulationResult) return null;

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

  function handleRestart() {
    resetDemo();
    router.push("/demo/farm-setup");
  }

  // Re-run the same simulation to prove idempotency
  async function handleRepeatEvaluation() {
    if (!policy) return;

    setRetesting(true);
    setRetestError(null);

    try {
      const simulateFn =
        policy.trigger_type === "drought" ? simulateDrought : simulateExcessRain;
      const result = await simulateFn(policy.id);
      setSimulationResult(result);
    } catch (err) {
      console.error("Repeat evaluation failed:", err);
      setRetestError(
        err instanceof Error ? err.message : "Repeat evaluation failed."
      );
    } finally {
      setRetesting(false);
    }
  }

  const triggered = simulationResult.triggered;
  const payoutAmount = simulationResult.payout?.amount ?? null;

  return (
    <div className="animate-fade-in">
      <StepIndicator currentStep="payout" />

      <div className="max-w-3xl mx-auto mt-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-100">
              <span className="gradient-text">Payout Result</span>
            </h1>
            <p className="text-gray-400 mt-2">
              Final settlement for your parametric insurance policy.
            </p>
          </div>
          <SimulatedBadge />
        </div>

        {retestError && (
          <div className="mb-6">
            <ErrorState
              title="Repeat Evaluation Failed"
              message={retestError}
              onRetry={() => setRetestError(null)}
            />
          </div>
        )}

        {retesting && <Loader text="Re-running evaluation..." />}

        {/* ─── Main payout card ─── */}
        <Card
          className={`!p-10 text-center mb-6 ${
            triggered
              ? "!border-climate-500/30"
              : "!border-gray-700"
          }`}
        >
          {/* Trigger status */}
          <div
            className={`inline-flex items-center justify-center w-24 h-24 rounded-full mb-6 ${
              triggered
                ? "bg-climate-500/10 shadow-[0_0_40px_rgba(16,185,129,0.2)]"
                : "bg-gray-800"
            }`}
            style={{
              animation: triggered ? "glow 3s ease-in-out infinite" : "none",
            }}
          >
            {triggered ? (
              <svg
                className="w-12 h-12 text-climate-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            ) : (
              <svg
                className="w-12 h-12 text-gray-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            )}
          </div>

          <Badge
            variant={triggered ? "success" : "warning"}
            size="lg"
          >
            {triggered ? "✓ TRIGGER CONFIRMED" : "NO TRIGGER"}
          </Badge>

          {triggered && payoutAmount && (
            <div className="mt-8">
              <p className="text-sm text-gray-500 uppercase tracking-widest">
                Payout Amount
              </p>
              <p className="text-5xl sm:text-6xl font-bold gradient-text mt-2">
                {formatCurrency(payoutAmount)}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                {simulationResult.payout?.currency} • Status:{" "}
                {simulationResult.payout?.status} • Coverage:{" "}
                {formatCurrency(policy.coverage_amount)}
              </p>
            </div>
          )}

          {!triggered && (
            <div className="mt-6">
              <p className="text-gray-400">
                The climate event did not breach the trigger threshold.
              </p>
              <p className="text-sm text-gray-500 mt-2">
                No payout is due for this event.
              </p>
            </div>
          )}

          {/* Idempotency badge */}
          {simulationResult.idempotent_reuse && (
            <div className="mt-4">
              <Badge variant="info" size="sm">
                ♻️ Idempotent Reuse — same result returned
              </Badge>
            </div>
          )}
        </Card>

        {/* ─── Evaluation details ─── */}
        <Card className="mb-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wider">
            Evaluation Details
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <MetricCard
              label="Observed Rainfall"
              value={`${simulationResult.observed_rainfall_mm} mm`}
              variant={triggered ? "danger" : "success"}
            />
            <MetricCard
              label="Threshold"
              value={`${simulationResult.threshold_mm} mm`}
              variant="info"
            />
            <MetricCard
              label="Trigger Type"
              value={
                simulationResult.trigger_type === "drought"
                  ? "Drought"
                  : "Excess Rain"
              }
              variant="warning"
            />
          </div>

          {/* Additional metadata */}
          <div className="mt-4 space-y-2 bg-navy-800/50 rounded-xl p-4 border border-gray-800">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Policy ID</span>
              <span className="text-gray-300 font-mono">#{simulationResult.policy_id}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Trigger ID</span>
              <span className="text-gray-300 font-mono">#{simulationResult.trigger_id}</span>
            </div>
            {simulationResult.payout?.payout_id != null && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Payout ID</span>
                <span className="text-gray-300 font-mono">#{simulationResult.payout.payout_id}</span>
              </div>
            )}
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Evaluation Date</span>
              <span className="text-gray-300">{simulationResult.evaluation_date}</span>
            </div>
            {simulationResult.window_start && simulationResult.window_end && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Window</span>
                <span className="text-gray-300">
                  {simulationResult.window_start} → {simulationResult.window_end}
                </span>
              </div>
            )}
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Engine</span>
              <span className="text-gray-300 font-mono text-xs">{simulationResult.engine_version}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Data Source</span>
              <Badge variant="warning" size="sm">
                {simulationResult.data_source || "Simulated"}
              </Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Idempotent Reuse</span>
              <Badge variant={simulationResult.idempotent_reuse ? "info" : "success"} size="sm">
                {simulationResult.idempotent_reuse ? "Yes (reused)" : "No (fresh)"}
              </Badge>
            </div>
          </div>
        </Card>

        {/* ─── Flow summary ─── */}
        <Card className="mb-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wider">
            Golden Demo Summary
          </h3>

          <div className="space-y-3">
            <div className="flex items-center gap-3 text-sm">
              <div className="w-8 h-8 rounded-full bg-climate-500/20 flex items-center justify-center text-climate-400 text-xs font-bold">
                1
              </div>
              <span className="text-gray-300">
                <strong>Farm:</strong> {farm.farmer_name} — {farm.crop} in{" "}
                {farm.location} ({farm.area_acres} acres)
              </span>
            </div>

            <div className="flex items-center gap-3 text-sm">
              <div className="w-8 h-8 rounded-full bg-climate-500/20 flex items-center justify-center text-climate-400 text-xs font-bold">
                2
              </div>
              <span className="text-gray-300">
                <strong>Risk:</strong> Analyzed climate risk for the farm
              </span>
            </div>

            <div className="flex items-center gap-3 text-sm">
              <div className="w-8 h-8 rounded-full bg-climate-500/20 flex items-center justify-center text-climate-400 text-xs font-bold">
                3
              </div>
              <span className="text-gray-300">
                <strong>Policy:</strong> Coverage{" "}
                {formatCurrency(policy.coverage_amount)},{" "}
                {policy.trigger_type} trigger at {policy.threshold_mm}mm / {policy.window_days} days
              </span>
            </div>

            <div className="flex items-center gap-3 text-sm">
              <div className="w-8 h-8 rounded-full bg-climate-500/20 flex items-center justify-center text-climate-400 text-xs font-bold">
                4
              </div>
              <span className="text-gray-300">
                <strong>Event:</strong> Simulated{" "}
                {simulationResult.observed_rainfall_mm}mm rainfall
              </span>
            </div>

            <div className="flex items-center gap-3 text-sm">
              <div className="w-8 h-8 rounded-full bg-climate-500/20 flex items-center justify-center text-climate-400 text-xs font-bold">
                5
              </div>
              <span className="text-gray-300">
                <strong>Payout:</strong>{" "}
                {triggered && payoutAmount
                  ? `${formatCurrency(payoutAmount)} settled`
                  : "No payout — threshold not breached"}
              </span>
            </div>
          </div>
        </Card>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <Link
            href="/"
            className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
          >
            ← Back to Home
          </Link>
          <div className="flex gap-3">
            <Button
              id="repeat-evaluation-btn"
              onClick={handleRepeatEvaluation}
              loading={retesting}
              variant="secondary"
              size="lg"
            >
              ♻️ Repeat Evaluation
            </Button>
            <Button
              id="restart-demo-btn"
              onClick={handleRestart}
              variant="secondary"
              size="lg"
            >
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
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Restart Demo
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
