"use client";

import React from "react";
import { useLanguage } from "@/context/LanguageContext";

export function LanguageToggle() {
  const { language, toggleLanguage } = useLanguage();

  return (
    <button
      onClick={toggleLanguage}
      className="fixed bottom-4 right-4 bg-climate-500 hover:bg-climate-600 text-white font-bold py-2 px-4 rounded-full shadow-lg transition-colors z-50 flex items-center gap-2 text-sm"
      aria-label="Toggle language"
    >
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
      </svg>
      {language === "en" ? "தமிழ்" : "English"}
    </button>
  );
}
