"use client";

import Link from "next/link";
import { DemoProvider } from "@/context/DemoContext";
import { type ReactNode } from "react";

export default function DemoLayout({ children }: { children: ReactNode }) {
  return (
    <DemoProvider>
      <div className="min-h-screen flex flex-col bg-navy-950">
        {/* Top bar */}
        <header className="border-b border-gray-800/50 px-6 py-3">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-climate-500 to-ocean-500 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
              </div>
              <span className="text-sm font-bold text-gray-200 group-hover:text-climate-400 transition-colors">
                Climate Shield
              </span>
            </Link>
            <Link
              href="/"
              className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              ← Back to Home
            </Link>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 flex flex-col">
          <div className="max-w-5xl mx-auto w-full px-4 sm:px-6 py-6 flex-1">
            {children}
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-gray-800/50 px-6 py-3">
          <div className="max-w-6xl mx-auto text-center text-xs text-gray-600">
            Climate Shield — Golden Demo Flow
          </div>
        </footer>
      </div>
    </DemoProvider>
  );
}
