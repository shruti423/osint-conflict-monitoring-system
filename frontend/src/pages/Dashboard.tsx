import { useState, useEffect } from "react";
import TypewriterText from "@/components/TypewriterText";
import TacticalMap from "@/components/TacticalMap";

// Define TypeScript interfaces matching our FastAPI backend Pydantic models
interface IntelligenceAlert {
  actor_1: string | null;
  actor_2: string | null;
  location_text: string | null;
  country: string | null;
  event_type: string | null;
  tags: string | null;
  source_name: string;
  claim_text: string;
  severity_score: number;
  confidence_score: number;
  published_at: string;
}

interface KPISummary {
  total_events: number;
  active_actors: number;
  alert_level: string;
  avg_severity: number;
}

interface DashboardData {
  kpis: KPISummary;
  sitrep: string;
  flash_alerts: IntelligenceAlert[];
}

const severityColor = (score: number) => {
  if (score >= 0.7) return "text-destructive text-glow-red";
  if (score >= 0.4) return "text-amber text-glow-amber";
  return "text-foreground text-glow";
};

const Dashboard = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        // Hitting our live FastAPI endpoint
        const response = await fetch("http://localhost:8000/api/v1/dashboard/live");
        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`);
        }
        const jsonData = await response.json();
        setData(jsonData);
      } catch (err: any) {
        setError(err.message || "Failed to establish secure connection to OSINT engine.");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6 flex flex-col items-center justify-center animate-pulse text-foreground text-glow">
        <h1 className="text-2xl font-bold tracking-widest mb-4">[ SYSTEM INITIALIZATION ]</h1>
        <p>Establishing secure handshake with intelligence feeds...</p>
        <p>Running LLM extraction protocols (This may take up to 30 seconds on initial boot)...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background p-6 flex items-center justify-center">
        <div className="border border-destructive p-6 text-destructive text-glow-red text-center">
          <h1 className="text-xl font-bold mb-2">CRITICAL SYSTEM FAILURE</h1>
          <p>{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 border border-destructive hover:bg-destructive/20 transition-colors"
          >
            RETRY CONNECTION
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  // Prepare KPIs for dynamic rendering
  const kpiDisplay = [
    { label: "TOTAL EVENTS", value: data.kpis.total_events },
    { label: "UNIQUE ACTORS", value: data.kpis.active_actors },
    { label: "GLOBAL SEVERITY", value: `${data.kpis.avg_severity.toFixed(2)} / 1.0` },
    { label: "SYSTEM STATUS", value: data.kpis.alert_level, critical: data.kpis.alert_level === "CRITICAL" },
  ];

  return (
    <div className="min-h-screen bg-background p-4 md:p-6 space-y-6 animate-flicker">
      {/* Header */}
      <h1 className="text-xl md:text-2xl font-bold text-foreground text-glow tracking-widest flex justify-between items-end">
        <span>GLOBAL TACTICAL OVERVIEW</span>
        <button 
          onClick={() => window.location.reload()}
          className="text-xs border border-foreground px-3 py-1 hover:bg-foreground hover:text-background transition-colors"
        >
          [ REFRESH DATA ]
        </button>
      </h1>

      {/* SITREP */}
      <div className="border border-foreground border-glow p-4 rounded-none">
        <h2 className="text-sm font-bold text-foreground text-glow mb-2 tracking-wider">
          [!] DECRYPTED SITUATION REPORT
        </h2>
        <p className="text-sm text-foreground leading-relaxed">
          <TypewriterText text={data.sitrep} speed={15} />
        </p>
      </div>

      {/* KPI Row (Adjusted to grid-cols-4 for our 4 dynamic KPIs) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {kpiDisplay.map((kpi) => (
          <div
            key={kpi.label}
            className={`border p-4 rounded-none text-center space-y-2 ${
              kpi.critical ? "border-destructive" : "border-border border-glow"
            }`}
          >
            <div className="text-xs text-muted-foreground tracking-wider">{kpi.label}</div>
            <div
              className={`text-2xl font-bold ${
                kpi.critical ? "text-destructive text-glow-red animate-pulse" : "text-foreground text-glow"
              }`}
            >
              {kpi.value}
            </div>
          </div>
        ))}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Tactical Map */}
        <div className="lg:col-span-2 space-y-2">
          <h2 className="text-xs text-muted-foreground tracking-wider">[MAP] TACTICAL OVERLAY</h2>
          {/* Note: The map currently uses static mock data inside TacticalMap.tsx. 
              We can update that component next to accept the live flash_alerts if desired. */}
          <TacticalMap alerts={data.flash_alerts} />
        </div>

        {/* Critical Alerts */}
        <div className="space-y-2">
          <h2 className="text-xs text-muted-foreground tracking-wider">[FEED] CRITICAL ALERTS</h2>
          <div className="border border-border border-glow p-3 rounded-none space-y-3 max-h-[400px] overflow-y-auto">
            {data.flash_alerts.slice(0, 10).map((alert, i) => (
              <div
                key={i}
                className={`border-l-2 pl-3 py-2 text-xs ${
                  alert.severity_score >= 0.7 ? "border-destructive" : "border-amber"
                }`}
              >
                <span className={severityColor(alert.severity_score)}>
                  SEV {alert.severity_score.toFixed(2)}
                </span>
                <span className="text-muted-foreground"> | </span>
                <span className="text-foreground">
                  {alert.actor_1 || "Unknown"} &gt;&gt; {alert.event_type || "Activity"}
                </span>
                {alert.location_text && (
                  <div className="text-muted-foreground mt-1 truncate">
                    Loc: {alert.location_text}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Raw Intercept Terminal */}
      <div className="space-y-2">
        <h2 className="text-xs text-muted-foreground tracking-wider">
          [TERMINAL] INTELLIGENCE LOG
        </h2>
        <div className="border border-border border-glow rounded-none overflow-x-auto max-h-[500px] overflow-y-auto">
          <table className="w-full text-xs text-foreground relative">
            <thead className="sticky top-0 bg-background">
              <tr className="border-b border-border text-muted-foreground">
                <th className="text-left p-2">TIMESTAMP</th>
                <th className="text-left p-2">ACTOR</th>
                <th className="text-left p-2">EVENT_TYPE</th>
                <th className="text-left p-2">LOCATION</th>
                <th className="text-left p-2">CONFIDENCE</th>
                <th className="text-left p-2">SEVERITY</th>
              </tr>
            </thead>
            <tbody>
              {data.flash_alerts.map((row, i) => (
                <tr key={i} className="border-b border-muted/30 hover:bg-muted/20 transition-colors">
                  <td className="p-2 whitespace-nowrap text-muted-foreground">
                    {new Date(row.published_at).toISOString().split('T')[1].slice(0,8)} Z
                  </td>
                  <td className="p-2 truncate max-w-[150px]">{row.actor_1 || "Unknown"}</td>
                  <td className="p-2 truncate max-w-[150px]">{row.event_type}</td>
                  <td className="p-2 truncate max-w-[150px]">{row.location_text || "Unspecified"}</td>
                  <td className="p-2">{(row.confidence_score * 100).toFixed(0)}%</td>
                  <td className={`p-2 font-bold ${severityColor(row.severity_score)}`}>
                    {row.severity_score.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};

export default Dashboard;