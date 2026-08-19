import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex-1 flex flex-col">
      {/* Hero Section */}
      <div className="relative flex-1 flex flex-col items-center justify-center px-6 py-20 overflow-hidden">
        {/* Background gradient effects */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-climate-500/5 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-ocean-500/5 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-climate-500/3 rounded-full blur-[100px]" />
        </div>

        <div className="relative z-10 max-w-4xl mx-auto text-center animate-fade-in">
          {/* Logo/Icon */}
          <div className="inline-flex items-center gap-3 mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-climate-500 to-ocean-500 flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.3)]">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <span className="text-sm font-semibold text-climate-400 tracking-widest uppercase">
              Climate Shield
            </span>
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight">
            <span className="gradient-text">Parametric Climate</span>
            <br />
            <span className="text-gray-100">Insurance Platform</span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
            AI-powered risk analysis and automated payouts for smallholder farmers.
            Protecting harvests against drought and extreme rainfall events.
          </p>

          {/* CTA */}
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/demo/farm-setup"
              id="start-demo-btn"
              className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-climate-600 to-climate-500
                         hover:from-climate-500 hover:to-climate-400
                         text-white text-lg font-semibold rounded-2xl
                         shadow-[0_8px_30px_rgba(16,185,129,0.3)]
                         hover:shadow-[0_8px_40px_rgba(16,185,129,0.4)]
                         transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
              Start Golden Demo
            </Link>
          </div>

          {/* Flow preview */}
          <div className="mt-16 flex flex-wrap items-center justify-center gap-3 text-sm text-gray-500">
            {[
              "Farm Setup",
              "Risk Analysis",
              "Policy",
              "Climate Event",
              "Payout",
            ].map((step, i) => (
              <div key={step} className="flex items-center gap-3">
                <span className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-navy-700 border border-gray-700 flex items-center justify-center text-xs font-medium text-gray-400">
                    {i + 1}
                  </span>
                  {step}
                </span>
                {i < 4 && (
                  <svg className="w-4 h-4 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-800/50 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-gray-600">
          <span>Climate Shield © 2026 — Hackathon Project</span>
          <span>AI-Powered Parametric Insurance</span>
        </div>
      </footer>
    </main>
  );
}
