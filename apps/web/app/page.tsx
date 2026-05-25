"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area,
} from "recharts";
import { AlertTriangle, Activity, Server, Cpu, Database, Wifi, WifiOff, Loader2, Zap, Shield, TrendingUp, ChevronRight } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS  = process.env.NEXT_PUBLIC_WS_URL  || "ws://localhost:8000/ws";

type Severity = "critical" | "high" | "medium";

interface TelemetryPoint {
  time: string;
  latency: number;
  cpu: number;
  errors: number;
  memory: number;
  rps?: number;
}

interface Incident {
  id: string;
  severity: Severity;
  service: string;
  summary: string;
  ts?: string;
}

interface Analysis {
  root_cause: string;
  confidence: number;
  actions: string[];
  blast_radius?: string;
  agent?: string;
}

interface ServiceHealth {
  name: string;
  status: string;
  health: number;
  region: string;
}

const SEV_STYLES: Record<Severity, { bar: string; badge: string; border: string }> = {
  critical: { bar: "bg-red-500",    badge: "bg-red-500/10 text-red-400 border-red-500/20",    border: "border-red-500/30" },
  high:     { bar: "bg-amber-500",  badge: "bg-amber-500/10 text-amber-400 border-amber-500/20", border: "border-amber-500/30" },
  medium:   { bar: "bg-blue-500",   badge: "bg-blue-500/10 text-blue-400 border-blue-500/20",  border: "border-blue-500/30" },
};

const fmt = (n: number) => new Date().toLocaleTimeString("en-US", { hour12: false });

export default function Dashboard() {
  const [telemetry, setTelemetry]       = useState<TelemetryPoint[]>([]);
  const [incidents, setIncidents]       = useState<Incident[]>([]);
  const [services, setServices]         = useState<ServiceHealth[]>([]);
  const [connected, setConnected]       = useState(false);
  const [analyzing, setAnalyzing]       = useState<string | null>(null);
  const [analyses, setAnalyses]         = useState<Record<string, Analysis>>({});
  const [selected, setSelected]         = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Fetch initial data from REST
  useEffect(() => {
    fetch(`${API}/incidents`).then(r => r.json()).then(setIncidents).catch(() => {});
    fetch(`${API}/services`).then(r => r.json()).then(setServices).catch(() => {});
  }, []);

  // WebSocket
  useEffect(() => {
    let retryTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      const ws = new WebSocket(WS);
      wsRef.current = ws;

      ws.onopen  = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        retryTimer = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();

      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === "ping") return;

          if (data.type === "snapshot") {
            setIncidents(prev => {
              const ids = new Set(prev.map((i: Incident) => i.id));
              const fresh = (data.incidents || []).filter((i: Incident) => !ids.has(i.id));
              return [...fresh, ...prev].slice(0, 20);
            });
            return;
          }

          if (data.type === "telemetry") {
            setTelemetry(prev => [
              ...prev.slice(-29),
              { time: new Date().toLocaleTimeString("en-US", { hour12: false }), ...data },
            ]);
          } else if (data.type === "incident") {
            setIncidents(prev => {
              if (prev.some(i => i.id === data.id)) return prev;
              return [data, ...prev].slice(0, 20);
            });
          }
        } catch {}
      };
    };

    connect();
    return () => {
      clearTimeout(retryTimer);
      wsRef.current?.close();
    };
  }, []);

  const runAnalysis = useCallback(async (inc: Incident) => {
    setAnalyzing(inc.id);
    setSelected(inc.id);
    try {
      const r = await fetch(`${API}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ incident_id: inc.id, service: inc.service, summary: inc.summary, severity: inc.severity }),
      });
      const d = await r.json();
      setAnalyses(prev => ({ ...prev, [inc.id]: d }));
    } catch {
      setAnalyses(prev => ({ ...prev, [inc.id]: { root_cause: "Analysis failed — check API connectivity.", confidence: 0, actions: [] } }));
    }
    setAnalyzing(null);
  }, []);

  const last = telemetry[telemetry.length - 1];
  const cpu    = last?.cpu    ?? 0;
  const mem    = last?.memory ?? 0;
  const lat    = last?.latency ?? 0;
  const errs   = last?.errors ?? 0;

  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 font-sans">
      {/* Top Nav */}
      <header className="sticky top-0 z-50 border-b border-slate-800/60 bg-[#080c14]/80 backdrop-blur px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Shield size={16} className="text-white" />
          </div>
          <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            SentinelAI
          </span>
          <span className="text-xs text-slate-500 border border-slate-700 rounded px-2 py-0.5">v1.0</span>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-xs text-slate-500">{incidents.length} incidents</span>
          <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${connected ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-red-500/10 text-red-400 border-red-500/20"}`}>
            {connected ? <Wifi size={12} /> : <WifiOff size={12} />}
            {connected ? "Live" : "Reconnecting..."}
          </div>
        </div>
      </header>

      <div className="p-6 grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* Left + Center column */}
        <div className="xl:col-span-2 space-y-6">

          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "CPU Usage",   value: `${cpu}%`,    icon: <Cpu size={16} className="text-blue-400" />,    bar: cpu,       color: "bg-blue-500" },
              { label: "Memory",      value: `${mem}%`,    icon: <Database size={16} className="text-violet-400" />, bar: mem,   color: "bg-violet-500" },
              { label: "P99 Latency", value: `${lat}ms`,   icon: <Activity size={16} className="text-emerald-400" />, bar: Math.min(lat / 10, 100), color: lat > 500 ? "bg-red-500" : lat > 200 ? "bg-amber-500" : "bg-emerald-500" },
              { label: "Error Rate",  value: `${errs}/s`,  icon: <Zap size={16} className="text-red-400" />,     bar: Math.min(errs / 3, 100), color: errs > 100 ? "bg-red-500" : "bg-amber-500" },
            ].map(({ label, value, icon, bar, color }) => (
              <div key={label} className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3 text-xs text-slate-400">
                  <span>{label}</span>
                  {icon}
                </div>
                <div className="text-2xl font-bold text-white mb-2">{value}</div>
                <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div className={`h-full ${color} transition-all duration-700`} style={{ width: `${bar}%` }} />
                </div>
              </div>
            ))}
          </div>

          {/* Charts */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <TrendingUp size={16} className="text-blue-400" />
                Live Telemetry Stream
              </h2>
              <span className="text-xs text-slate-500">{telemetry.length} data points</span>
            </div>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={telemetry}>
                  <defs>
                    <linearGradient id="gCpu" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gLat" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#10b981" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="time" stroke="#334155" fontSize={11} tick={{ fill: "#64748b" }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                  <YAxis stroke="#334155" fontSize={11} tick={{ fill: "#64748b" }} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8, fontSize: 12 }}
                    itemStyle={{ color: "#cbd5e1" }}
                    labelStyle={{ color: "#94a3b8" }}
                  />
                  <Area type="monotone" dataKey="cpu"     stroke="#3b82f6" strokeWidth={1.5} fill="url(#gCpu)" dot={false} name="CPU %" />
                  <Area type="monotone" dataKey="latency" stroke="#10b981" strokeWidth={1.5} fill="url(#gLat)" dot={false} name="Latency ms" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Services Health */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
              <Server size={16} className="text-slate-400" />
              Service Health
            </h2>
            <div className="space-y-3">
              {services.map(svc => (
                <div key={svc.name} className="flex items-center gap-4">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${svc.status === "healthy" ? "bg-emerald-400" : svc.status === "degraded" ? "bg-red-400" : "bg-amber-400"}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-medium text-slate-300 truncate">{svc.name}</span>
                      <span className="text-slate-500 ml-2">{svc.health}%</span>
                    </div>
                    <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${svc.health > 90 ? "bg-emerald-500" : svc.health > 70 ? "bg-amber-500" : "bg-red-500"}`}
                        style={{ width: `${svc.health}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-xs text-slate-600 flex-shrink-0 w-20 text-right">{svc.region}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right column — Incidents */}
        <div className="space-y-4">
          <div className="flex items-center justify-between sticky top-20">
            <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <AlertTriangle size={16} className="text-amber-400" />
              Active Incidents
            </h2>
            <span className="text-xs bg-slate-800 text-slate-400 border border-slate-700 px-2 py-0.5 rounded-full">{incidents.length}</span>
          </div>

          <div className="space-y-3 max-h-[calc(100vh-120px)] overflow-y-auto pr-1 scrollbar-thin">
            {incidents.length === 0 ? (
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center">
                <div className="w-10 h-10 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Shield size={18} className="text-emerald-400" />
                </div>
                <p className="text-sm text-slate-400">All systems nominal</p>
                <p className="text-xs text-slate-600 mt-1">No active incidents detected</p>
              </div>
            ) : incidents.map(inc => {
              const sev = SEV_STYLES[inc.severity] ?? SEV_STYLES.medium;
              const isSelected = selected === inc.id;
              const result = analyses[inc.id];
              return (
                <div key={inc.id} className={`bg-slate-900/60 border rounded-xl overflow-hidden transition-all ${isSelected ? sev.border : "border-slate-800"}`}>
                  <div className="flex">
                    <div className={`w-1 flex-shrink-0 ${sev.bar}`} />
                    <div className="flex-1 p-4">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${sev.badge}`}>
                          {inc.severity.toUpperCase()}
                        </span>
                        <span className="text-xs text-slate-600 font-mono">{inc.id}</span>
                      </div>
                      <h3 className="text-sm font-semibold text-slate-200 mb-1">{inc.service}</h3>
                      <p className="text-xs text-slate-400 leading-relaxed mb-3">{inc.summary}</p>

                      {!result ? (
                        <button
                          onClick={() => runAnalysis(inc)}
                          disabled={analyzing === inc.id}
                          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition-colors text-white"
                        >
                          {analyzing === inc.id
                            ? <><Loader2 size={13} className="animate-spin" /> Analyzing...</>
                            : <><Cpu size={13} /> Run AI Root Cause Analysis</>}
                        </button>
                      ) : (
                        <div className="mt-2 bg-slate-950/60 border border-indigo-500/20 rounded-lg p-3 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-indigo-400 tracking-wider">AI DIAGNOSIS</span>
                            <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded">
                              {Math.round(result.confidence * 100)}% confidence
                            </span>
                          </div>
                          <p className="text-xs text-slate-300 leading-relaxed">{result.root_cause}</p>
                          {result.blast_radius && (
                            <p className="text-xs text-amber-400/80"><span className="font-semibold">Blast radius:</span> {result.blast_radius}</p>
                          )}
                          {result.actions?.length > 0 && (
                            <div className="pt-1 space-y-1.5">
                              <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Remediation</span>
                              {result.actions.map((a, i) => (
                                <div key={i} className="flex items-start gap-2 text-xs text-slate-400">
                                  <ChevronRight size={11} className="text-emerald-500 mt-0.5 flex-shrink-0" />
                                  <span>{a}</span>
                                </div>
                              ))}
                            </div>
                          )}
                          {result.agent && <p className="text-xs text-slate-600 pt-1 border-t border-slate-800">{result.agent}</p>}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
