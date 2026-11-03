"use client";

import React, { useEffect, useState } from "react";

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<string>("Checking...");
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetch(`${apiUrl}/api/health`)
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status || "online"))
      .catch(() => setBackendStatus("offline (start backend container)"));
  }, [apiUrl]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-slate-950 text-slate-100">
      <div className="max-w-3xl w-full text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Round 2 · Build-a-thon Ready
        </div>

        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">
          SiteDesk <span className="text-emerald-400">Trade Counter AI</span>
        </h1>
        <p className="text-slate-400 text-lg">
          From Raw Material List to Confirmed POS Order in &lt; 2 Minutes.
        </p>

        {/* Status Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 text-left">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
            <p className="text-xs text-slate-500 uppercase font-semibold">Frontend</p>
            <p className="text-lg font-bold text-slate-200">Next.js 14 App</p>
            <p className="text-xs text-emerald-400 mt-1">● Port 3000 Running</p>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
            <p className="text-xs text-slate-500 uppercase font-semibold">Backend</p>
            <p className="text-lg font-bold text-slate-200">FastAPI Core</p>
            <p className="text-xs text-emerald-400 mt-1">● {backendStatus}</p>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
            <p className="text-xs text-slate-500 uppercase font-semibold">Database</p>
            <p className="text-lg font-bold text-slate-200">PostgreSQL 15</p>
            <p className="text-xs text-emerald-400 mt-1">● Port 5432 (Docker)</p>
          </div>
        </div>

        <div className="pt-4 text-xs text-slate-500">
          Ready for team meeting. Start building components in <code className="text-slate-300">/frontend/src</code> and APIs in <code className="text-slate-300">/backend</code>.
        </div>
      </div>
    </main>
  );
}
