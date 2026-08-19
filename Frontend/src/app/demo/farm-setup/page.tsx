"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useDemo } from "@/context/DemoContext";
import { StepIndicator } from "@/components/ui/StepIndicator";
import {
  Card,
  Button,
  Input,
  Select,
  ErrorState,
} from "@/components/ui";
import { createFarm } from "@/lib/api";
import { LOCATIONS, CROPS, CROP_STAGES } from "@/lib/types";

export default function FarmSetupPage() {
  const router = useRouter();
  const { setFarm, setCurrentStep } = useDemo();

  const [farmerName, setFarmerName] = useState("Rajan Kumar");
  const [locationIdx, setLocationIdx] = useState("0");
  const [crop, setCrop] = useState(CROPS[0] as string);
  const [areaAcres, setAreaAcres] = useState("5");
  const [cropStage, setCropStage] = useState(CROP_STAGES[1] as string);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedLocation =
    locationIdx !== "" ? LOCATIONS[parseInt(locationIdx)] : null;

  async function handleSubmit() {
    if (!selectedLocation || !farmerName || !crop || !areaAcres) {
      setError("Please fill in all required fields");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const farm = await createFarm({
        farmer_name: farmerName,
        location: selectedLocation.name,
        latitude: selectedLocation.lat,
        longitude: selectedLocation.lng,
        crop: crop,
        area_acres: parseFloat(areaAcres),
        crop_stage: cropStage || null,
      });

      setFarm(farm);
      setCurrentStep("risk-analysis");
      router.push("/demo/risk-analysis");
    } catch (err) {
      console.error("Farm creation failed:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create farm. Is the backend running?"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="animate-fade-in">
      <StepIndicator currentStep="farm-setup" />

      <div className="max-w-2xl mx-auto mt-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-100">
            <span className="gradient-text">Farm Setup</span>
          </h1>
          <p className="text-gray-400 mt-2">
            Enter your farm details to begin the climate risk analysis and insurance setup.
          </p>
        </div>

        {error && (
          <div className="mb-6">
            <ErrorState
              message={error}
              onRetry={() => setError(null)}
            />
          </div>
        )}

        <Card>
          <div className="space-y-5">
            <Input
              id="farmer-name"
              label="Farmer Name"
              value={farmerName}
              onChange={setFarmerName}
              placeholder="Enter farmer name"
              required
            />

            <Select
              id="farm-location"
              label="Location"
              value={locationIdx}
              onChange={setLocationIdx}
              required
              options={LOCATIONS.map((loc, i) => ({
                value: String(i),
                label: loc.name,
              }))}
              placeholder="Select location..."
            />

            {selectedLocation && (
              <div className="flex gap-4 text-xs text-gray-500 bg-navy-800/50 rounded-lg px-4 py-2.5">
                <span>
                  📍 Lat: {selectedLocation.lat.toFixed(3)}, Lng:{" "}
                  {selectedLocation.lng.toFixed(3)}
                </span>
              </div>
            )}

            <Select
              id="farm-crop"
              label="Crop"
              value={crop}
              onChange={setCrop}
              required
              options={CROPS.map((c) => ({
                value: c,
                label: c,
              }))}
              placeholder="Select crop..."
            />

            <Input
              id="farm-area"
              label="Farm Area (Acres)"
              value={areaAcres}
              onChange={setAreaAcres}
              type="number"
              min={0.1}
              max={1000}
              step={0.1}
              required
              placeholder="e.g. 5"
            />

            <Select
              id="crop-stage"
              label="Crop Stage"
              value={cropStage}
              onChange={setCropStage}
              options={CROP_STAGES.map((s) => ({
                value: s,
                label: s,
              }))}
              placeholder="Select stage..."
            />
          </div>

          <div className="mt-8 flex justify-end">
            <Button
              id="analyze-risk-btn"
              onClick={handleSubmit}
              loading={loading}
              size="lg"
            >
              Continue — Analyze Risk
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
        </Card>
      </div>
    </div>
  );
}
