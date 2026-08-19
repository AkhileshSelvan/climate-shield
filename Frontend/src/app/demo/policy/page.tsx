"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useDemo } from "@/context/DemoContext";
import { StepIndicator } from "@/components/ui/StepIndicator";
import {
  Card,
  Badge,
  Button,
  Input,
  Select,
  Loader,
  ErrorState,
  MetricCard,
} from "@/components/ui";
import { createPolicy } from "@/lib/api";
import { TRIGGER_TYPES } from "@/lib/types";

export default function PolicyPage() {
  const router = useRouter();
  const { farm, riskAnalysis, policy, setPolicy, setCurrentStep } = useDemo();

  const [coverageAmount, setCoverageAmount] = useState("50000");
  const [triggerType, setTriggerType] = useState("drought");
  const [thresholdMm, setThresholdMm] = useState("50");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState(false);

  useEffect(() => {
    if (!farm) {
      router.push("/demo/farm-setup");
      return;
    }
    if (!riskAnalysis) {
      router.push("/demo/risk-analysis");
      return;
    }
    if (policy) {
      setCreated(true);
    }
  }, [farm, riskAnalysis, policy, router]);

  async function handleCreatePolicy() {
    if (!farm) return;

    setLoading(true);
    setError(null);

    try {
      const result = await createPolicy({
        farm_id: farm.id,
        coverage_amount: parseFloat(coverageAmount),
        trigger_type: triggerType,
        threshold_mm: parseFloat(thresholdMm),
      });

      setPolicy(result);
      setCreated(true);
    } catch (err) {
      console.error("Policy creation failed:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create policy. Is the backend running?"
      );
    } finally {
      setLoading(false);
    }
  }

  function handleContinue() {
    setCurrentStep("simulate");
    router.push("/demo/simulate");
  }

  if (!farm || !riskAnalysis) return null;

  // Format currency string (backend returns decimal strings)
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
      <StepIndicator currentStep="policy" />

      <div className="max-w-3xl mx-auto mt-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-100">
            <span className="gradient-text">Insurance Policy</span>
          </h1>
          <p className="text-gray-400 mt-2">
            {created
              ? "Your parametric insurance policy has been created."
              : "Configure your parametric insurance coverage."}
          </p>
        </div>

        {error && (
          <div className="mb-6">
            <ErrorState
              title="Policy Creation Failed"
              message={error}
              onRetry={() => setError(null)}
            />
          </div>
        )}

        {!created ? (
          /* ─── Policy creation form ─── */
          <Card>
            <div className="space-y-5">
              {/* Farm info summary */}
              <div className="bg-navy-800/50 rounded-xl p-4 border border-gray-800">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
                  Farm Details
                </p>
                <div className="flex flex-wrap gap-4 text-sm text-gray-300">
                  <span>🌾 {farm.crop}</span>
                  <span>📍 {farm.location}</span>
                  <span>📐 {farm.area_acres} acres</span>
                  <span>
                    Risk:{" "}
                    <Badge
                      variant={
                        riskAnalysis.risk_level === "LOW"
                          ? "low"
                          : riskAnalysis.risk_level === "MEDIUM"
                          ? "medium"
                          : riskAnalysis.risk_level === "HIGH"
                          ? "high"
                          : "severe"
                      }
                      size="sm"
                    >
                      {riskAnalysis.risk_level}
                    </Badge>
                  </span>
                </div>
              </div>

              <Input
                id="coverage-amount"
                label="Coverage Amount (₹)"
                value={coverageAmount}
                onChange={setCoverageAmount}
                type="number"
                min={1000}
                step={1000}
                required
                helpText="Maximum payout amount in case of trigger activation"
              />

              <Select
                id="trigger-type"
                label="Trigger Type"
                value={triggerType}
                onChange={setTriggerType}
                options={TRIGGER_TYPES.map((t) => ({
                  value: t.value,
                  label: t.label,
                }))}
                required
              />

              <Input
                id="threshold-mm"
                label="Threshold (mm rainfall)"
                value={thresholdMm}
                onChange={setThresholdMm}
                type="number"
                min={1}
                step={1}
                required
                helpText={
                  triggerType === "drought"
                    ? "Trigger activates if rainfall drops BELOW this threshold"
                    : "Trigger activates if rainfall exceeds this threshold"
                }
              />
            </div>

            <div className="mt-8 flex justify-end">
              <Button
                id="create-policy-btn"
                onClick={handleCreatePolicy}
                loading={loading}
                size="lg"
              >
                Create Policy
              </Button>
            </div>
          </Card>
        ) : (
          /* ─── Policy view ─── */
          <div className="space-y-6">
            {loading && <Loader text="Creating policy..." />}

            {policy && (
              <>
                {/* Policy status card */}
                <Card className="!p-8">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Policy #{policy.id}
                      </p>
                      <h2 className="text-2xl font-bold text-gray-100 mt-1">
                        Parametric Insurance
                      </h2>
                    </div>
                    <Badge
                      variant={
                        policy.status === "active" ? "success" : "warning"
                      }
                      size="lg"
                    >
                      {policy.status?.toUpperCase() || "ACTIVE"}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <MetricCard
                      label="Coverage Amount"
                      value={formatCurrency(policy.coverage_amount)}
                      variant="success"
                    />
                    <MetricCard
                      label="Premium"
                      value={
                        policy.premium
                          ? formatCurrency(policy.premium)
                          : "Pending"
                      }
                      subtitle={
                        policy.premium
                          ? "From backend calculation"
                          : "Backend has not returned premium"
                      }
                      variant="info"
                    />
                  </div>
                </Card>

                {/* Trigger details */}
                <Card>
                  <h3 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wider">
                    Trigger Configuration
                  </h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between py-2 border-b border-gray-800/50">
                      <span className="text-sm text-gray-400">
                        Trigger Type
                      </span>
                      <Badge variant="info">
                        {policy.trigger_type === "drought"
                          ? "🌵 Drought"
                          : "🌧️ Excess Rainfall"}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between py-2 border-b border-gray-800/50">
                      <span className="text-sm text-gray-400">
                        Threshold
                      </span>
                      <span className="text-sm font-semibold text-gray-200">
                        {policy.threshold_mm} mm
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-2 border-b border-gray-800/50">
                      <span className="text-sm text-gray-400">
                        Condition
                      </span>
                      <span className="text-sm text-gray-300">
                        {policy.trigger_type === "drought"
                          ? `Rainfall < ${policy.threshold_mm}mm`
                          : `Rainfall > ${policy.threshold_mm}mm`}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-2">
                      <span className="text-sm text-gray-400">Farm</span>
                      <span className="text-sm text-gray-300">
                        {farm.crop} • {farm.location}
                      </span>
                    </div>
                  </div>
                </Card>

                {/* Continue */}
                <div className="flex justify-end pt-2">
                  <Button
                    id="simulate-event-btn"
                    onClick={handleContinue}
                    size="lg"
                  >
                    Simulate Climate Event
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
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
