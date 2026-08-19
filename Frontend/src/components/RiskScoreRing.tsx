"use client";

import { useEffect, useState } from "react";

interface RiskScoreRingProps {
  score: number;
  level: "LOW" | "MEDIUM" | "HIGH" | "SEVERE";
  size?: number;
  strokeWidth?: number;
}

const LEVEL_COLORS: Record<string, { ring: string; text: string; glow: string }> = {
  LOW: {
    ring: "#10b981",
    text: "text-climate-400",
    glow: "rgba(16, 185, 129, 0.3)",
  },
  MEDIUM: {
    ring: "#f59e0b",
    text: "text-alert-400",
    glow: "rgba(245, 158, 11, 0.3)",
  },
  HIGH: {
    ring: "#f97316",
    text: "text-orange-400",
    glow: "rgba(249, 115, 22, 0.3)",
  },
  SEVERE: {
    ring: "#ef4444",
    text: "text-danger-400",
    glow: "rgba(239, 68, 68, 0.3)",
  },
};

export function RiskScoreRing({
  score,
  level,
  size = 200,
  strokeWidth = 12,
}: RiskScoreRingProps) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const colors = LEVEL_COLORS[level] || LEVEL_COLORS.LOW;

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (animatedScore / 100) * circumference;
  const dashOffset = circumference - progress;

  useEffect(() => {
    const duration = 1500;
    const startTime = performance.now();

    function animate(currentTime: number) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(Math.round(score * eased));

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    }

    requestAnimationFrame(animate);
  }, [score]);

  return (
    <div className="risk-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth={strokeWidth}
        />
        {/* Glow effect */}
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {/* Progress ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colors.ring}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          filter="url(#glow)"
          style={{ transition: "stroke-dashoffset 0.1s ease-out" }}
        />
      </svg>
      {/* Score text in center */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-5xl font-bold tabular-nums ${colors.text}`}>
          {animatedScore}
        </span>
        <span className="text-xs text-gray-400 uppercase tracking-widest mt-1">
          Risk Score
        </span>
      </div>
    </div>
  );
}
