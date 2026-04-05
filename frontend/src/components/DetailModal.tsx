import { X } from "lucide-react";

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

interface DetailModalProps {
  alert: IntelligenceAlert | null;
  onClose: () => void;
}

const DetailModal = ({ alert, onClose }: DetailModalProps) => {
  if (!alert) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl border border-foreground border-glow bg-background p-6 space-y-6 relative animate-in fade-in zoom-in duration-200">
        
        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors"
        >
          <X size={20} />
        </button>

        {/* Header */}
        <div className="border-b border-border pb-4">
          <h2 className="text-xl font-bold text-foreground text-glow tracking-widest">
            [ EVENT_DOSSIER: {alert.event_type?.toUpperCase()} ]
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            TIMESTAMP: {new Date(alert.published_at).toLocaleString()} Z
          </p>
        </div>

        {/* Intelligence Grid */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-1">
            <span className="text-muted-foreground block text-[10px] tracking-tighter">PRIMARY ACTOR</span>
            <span className="text-foreground font-mono">{alert.actor_1 || "UNKNOWN"}</span>
          </div>
          <div className="space-y-1">
            <span className="text-muted-foreground block text-[10px] tracking-tighter">TARGET / ACTOR 2</span>
            <span className="text-foreground font-mono">{alert.actor_2 || "N/A"}</span>
          </div>
          <div className="space-y-1">
            <span className="text-muted-foreground block text-[10px] tracking-tighter">LOCATION</span>
            <span className="text-foreground font-mono">{alert.location_text}, {alert.country}</span>
          </div>
          <div className="space-y-1">
            <span className="text-muted-foreground block text-[10px] tracking-tighter">PROVENANCE</span>
            <span className="text-amber text-glow-amber font-mono text-xs">{alert.source_name}</span>
          </div>
        </div>

        {/* Raw Claim Text */}
        <div className="bg-muted/10 p-4 border border-border/50">
          <span className="text-muted-foreground block text-[10px] tracking-tighter mb-2">RAW INTELLIGENCE INTERCEPT</span>
          <p className="text-sm text-foreground leading-relaxed italic">
            "{alert.claim_text}"
          </p>
        </div>

        {/* Metadata & Tags */}
        <div className="flex flex-wrap gap-2 pt-2">
          {alert.tags?.split(',').map((tag, idx) => (
            <span key={idx} className="text-[10px] border border-muted px-2 py-0.5 text-muted-foreground uppercase">
              #{tag.trim()}
            </span>
          ))}
        </div>

        {/* Footer Metrics */}
        <div className="flex justify-between items-center pt-4 border-t border-border">
          <div className="text-xs">
            CONFIDENCE: <span className="text-foreground font-bold">{(alert.confidence_score * 100).toFixed(0)}%</span>
          </div>
          <div className="text-xs">
            SEVERITY: <span className={`${alert.severity_score >= 0.7 ? "text-destructive" : "text-amber"} font-bold`}>
              {alert.severity_score.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetailModal;