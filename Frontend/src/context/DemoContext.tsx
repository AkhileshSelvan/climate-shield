"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import type {
  DemoState,
  DemoStep,
  Farm,
  RiskAnalysis,
  Policy,
  SimulationResult,
} from "@/lib/types";

interface DemoContextValue extends DemoState {
  setFarm: (farm: Farm) => void;
  setRiskAnalysis: (analysis: RiskAnalysis) => void;
  setPolicy: (policy: Policy) => void;
  setSimulationResult: (result: SimulationResult) => void;
  setCurrentStep: (step: DemoStep) => void;
  resetDemo: () => void;
}

const initialState: DemoState = {
  farm: null,
  riskAnalysis: null,
  policy: null,
  simulationResult: null,
  currentStep: "farm-setup",
};

const DemoContext = createContext<DemoContextValue | null>(null);

export function DemoProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<DemoState>(initialState);

  const setFarm = useCallback((farm: Farm) => {
    setState((prev) => ({ ...prev, farm }));
  }, []);

  const setRiskAnalysis = useCallback((riskAnalysis: RiskAnalysis) => {
    setState((prev) => ({ ...prev, riskAnalysis }));
  }, []);

  const setPolicy = useCallback((policy: Policy) => {
    setState((prev) => ({ ...prev, policy }));
  }, []);

  const setSimulationResult = useCallback((simulationResult: SimulationResult) => {
    setState((prev) => ({ ...prev, simulationResult }));
  }, []);

  const setCurrentStep = useCallback((currentStep: DemoStep) => {
    setState((prev) => ({ ...prev, currentStep }));
  }, []);

  const resetDemo = useCallback(() => {
    setState(initialState);
  }, []);

  return (
    <DemoContext.Provider
      value={{
        ...state,
        setFarm,
        setRiskAnalysis,
        setPolicy,
        setSimulationResult,
        setCurrentStep,
        resetDemo,
      }}
    >
      {children}
    </DemoContext.Provider>
  );
}

export function useDemo(): DemoContextValue {
  const context = useContext(DemoContext);
  if (!context) {
    throw new Error("useDemo must be used within a DemoProvider");
  }
  return context;
}
