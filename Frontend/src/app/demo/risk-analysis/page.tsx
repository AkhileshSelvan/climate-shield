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
  MetricCard,
  SimulatedBadge,
} from "@/components/ui";
import { RiskScoreRing } from "@/components/RiskScoreRing";
import { analyzeRisk } from "@/lib/api";
import type { RiskAnalysis } from "@/lib/types";

const RISK_LEVEL_VARIANT = {
  LOW: "low" as const,
  MEDIUM: "medium" as const,
  HIGH: "high" as const,
  SEVERE: "severe" as const,
};

export default function RiskAnalysisPage() {
  const router = useRouter();
  const { farm, riskAnalysis, setRiskAnalysis, setCurrentStep } = useDemo();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!farm) {
      router.push("/demo/farm-setup");
      return;
    }

    if (!riskAnalysis) {
      fetchRiskAnalysis();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [farm]);

  async function fetchRiskAnalysis() {
    if (!farm) return;

    setLoading(true);
    setError(null);

    try {
      const result = await analyzeRisk({
        location: farm.location,
        crop: farm.crop,
        area_acres: farm.area_acres,
        latitude: farm.latitude,
        longitude: farm.longitude,
        farm_id: farm.id,
      });

      setRiskAnalysis(result);
    } catch (err) {
      console.error("Risk analysis failed:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to analyze risk. Please check the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleContinue() {
    setCurrentStep("policy");
    router.push("/demo/policy");
  }

  if (!farm) return null;

  return (
    <div className="animate-fade-in">
      <StepIndicator currentStep="risk-analysis" />

      <div className="mt-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-100">
              <span className="gradient-text">Climate Risk Analysis</span>
            </h1>
            <p className="text-gray-400 mt-2">
              {farm.crop} farm in {farm.location} • {farm.area_acres} acres
            </p>
          </div>
          {riskAnalysis?.is_synthetic && <SimulatedBadge />}
        </div>

        {/* Loading state */}
        {loading && (
          <Loader text="Analyzing climate risk data..." size="lg" />
        )}

        {/* Error state */}
        {error && !loading && (
          <ErrorState
            title="Risk Analysis Failed"
            message={error}
            onRetry={fetchRiskAnalysis}
          />
        )}

        {/* Results */}
        {riskAnalysis && !loading && (
          <div className="space-y-6">
            {/* Risk Score & Level - Hero section */}
            <Card className="!p-8">
              <div className="flex flex-col lg:flex-row items-center gap-8">
                {/* Score Ring */}
                <div className="flex-shrink-0">
                  <RiskScoreRing
                    score={riskAnalysis.risk_score}
                    level={riskAnalysis.risk_level}
                  />
                </div>

                {/* Risk details */}
                <div className="flex-1 space-y-4 text-center lg:text-left">
                  <div className="flex items-center gap-3 justify-center lg:justify-start">
                    <Badge
                      variant={RISK_LEVEL_VARIANT[riskAnalysis.risk_level]}
                      size="lg"
                    >
                      {riskAnalysis.risk_level} RISK
                    </Badge>
                    {riskAnalysis.confidence != null && (
                      <Badge variant="info" size="sm">
                        {Math.round(riskAnalysis.confidence * 100)}% confidence
                      </Badge>
                    )}
                  </div>

                  {/* Why this risk */}
                  {riskAnalysis.explanation && (
                    <div className="bg-navy-800/50 rounded-xl p-4 border border-gray-800">
                      <p className="text-sm font-medium text-gray-300 mb-1">
                        Why this risk level?
                      </p>
                      <p className="text-sm text-gray-400 leading-relaxed">
                        {riskAnalysis.explanation}
                      </p>
                    </div>
                  )}

                  {/* Trigger definition */}
                  {riskAnalysis.trigger_definition && (
                    <div className="bg-navy-800/50 rounded-xl p-4 border border-gray-800">
                      <p className="text-sm font-medium text-gray-300 mb-1">
                        Trigger Definition
                      </p>
                      <p className="text-sm text-gray-400">
                        {riskAnalysis.trigger_definition}
                      </p>
                    </div>
                  )}

                  {/* Data quality */}
                  {riskAnalysis.data_quality && (
                    <p className="text-xs text-gray-500">
                      Data quality: {riskAnalysis.data_quality}
                    </p>
                  )}
                </div>
              </div>
            </Card>

            {/* Key metrics grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {riskAnalysis.trigger_frequency != null && (
                <MetricCard
                  label="Trigger Frequency"
                  value={`${(riskAnalysis.trigger_frequency * 100).toFixed(0)}%`}
                  subtitle="Probability per year"
                  variant="warning"
                />
              )}

              {riskAnalysis.eligible_years != null && (
                <MetricCard
                  label="Eligible Years"
                  value={riskAnalysis.eligible_years}
                  subtitle="Years of data analyzed"
                  variant="info"
                />
              )}

              {riskAnalysis.triggered_years != null && (
                <MetricCard
                  label="Triggered Years"
                  value={riskAnalysis.triggered_years}
                  subtitle="Years trigger was breached"
                  variant="danger"
                />
              )}

              <MetricCard
                label="Risk Score"
                value={`${riskAnalysis.risk_score}/100`}
                subtitle={`${riskAnalysis.risk_level} severity`}
                variant={
                  riskAnalysis.risk_level === "SEVERE"
                    ? "danger"
                    : riskAnalysis.risk_level === "HIGH"
                    ? "warning"
                    : riskAnalysis.risk_level === "MEDIUM"
                    ? "warning"
                    : "success"
                }
              />
            </div>

            {/* Recommendations */}
            {riskAnalysis.recommendations &&
              riskAnalysis.recommendations.length > 0 && (
                <Card>
                  <h3 className="text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wider">
                    Recommendations
                  </h3>
                  <ul className="space-y-2">
                    {(riskAnalysis.recommendations as string[]).map(
                      (rec: string, i: number) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                          <span className="text-climate-400 mt-0.5">•</span>
                          {rec}
                        </li>
                      )
                    )}
                  </ul>
                </Card>
              )}

            {/* Continue button */}
            <div className="flex justify-end pt-2">
              <Button id="view-policy-btn" onClick={handleContinue} size="lg">
                View Policy
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
          </div>
        )}
      </div>
    </div>
  );
}
