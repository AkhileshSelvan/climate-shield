"use client";

import { DEMO_STEPS, type DemoStep } from "@/lib/types";

interface StepIndicatorProps {
  currentStep: DemoStep;
}

export function StepIndicator({ currentStep }: StepIndicatorProps) {
  const currentIndex = DEMO_STEPS.findIndex((s) => s.key === currentStep);

  return (
    <div className="w-full px-4 py-6">
      <div className="flex items-center justify-between max-w-3xl mx-auto">
        {DEMO_STEPS.map((step, index) => {
          const isActive = index === currentIndex;
          const isCompleted = index < currentIndex;

          return (
            <div key={step.key} className="flex items-center flex-1 last:flex-none">
              {/* Step circle */}
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`
                    w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold
                    transition-all duration-500
                    ${
                      isCompleted
                        ? "bg-climate-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.4)]"
                        : isActive
                        ? "bg-ocean-500 text-white shadow-[0_0_20px_rgba(59,130,246,0.4)] scale-110"
                        : "bg-navy-700 text-gray-500 border border-gray-700"
                    }
                  `}
                >
                  {isCompleted ? (
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2.5}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  ) : (
                    step.number
                  )}
                </div>
                <span
                  className={`text-xs font-medium hidden sm:block whitespace-nowrap ${
                    isActive
                      ? "text-ocean-400"
                      : isCompleted
                      ? "text-climate-400"
                      : "text-gray-600"
                  }`}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector line */}
              {index < DEMO_STEPS.length - 1 && (
                <div className="flex-1 mx-2 sm:mx-3">
                  <div
                    className={`h-0.5 rounded-full transition-all duration-700 ${
                      isCompleted
                        ? "bg-gradient-to-r from-climate-500 to-climate-400"
                        : "bg-navy-700"
                    }`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
