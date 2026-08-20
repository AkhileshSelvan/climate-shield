"use client";

import React, { useState } from "react";
import { useLanguage } from "@/context/LanguageContext";

interface ReadAloudButtonProps {
  textKey: string;
  values?: Record<string, string>;
}

export function ReadAloudButton({ textKey, values = {} }: ReadAloudButtonProps) {
  const { language, t } = useLanguage();
  const [isPlaying, setIsPlaying] = useState(false);

  const speak = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel(); // Stop any ongoing speech

      let text = t(textKey as any);
      Object.keys(values).forEach((key) => {
        text = text.replace(`{${key}}`, values[key]);
      });

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language === "ta" ? "ta-IN" : "en-US";
      
      utterance.onstart = () => setIsPlaying(true);
      utterance.onend = () => setIsPlaying(false);
      utterance.onerror = () => setIsPlaying(false);

      window.speechSynthesis.speak(utterance);
    }
  };

  return (
    <button
      onClick={speak}
      className={`p-2 rounded-full transition-colors ${isPlaying ? "bg-climate-500 text-white" : "bg-navy-800 text-gray-400 hover:text-climate-400 hover:bg-navy-700"}`}
      title="Read Aloud"
      aria-label="Read Aloud"
    >
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
      </svg>
    </button>
  );
}
